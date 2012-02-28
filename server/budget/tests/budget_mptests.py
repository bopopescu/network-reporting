import os
import sys
import logging
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import datetime

from account.models import Account

from publisher.models import App
from publisher.models import Site as AdUnit

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )

############# Integration Tests #############
import unittest
from nose.tools import eq_,assert_almost_equal
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache
from advertiser.query_managers import CampaignQueryManager
from budget.models import (Budget,
                           BudgetSliceLog,
                           )
from budget.helpers import get_slice_from_datetime, TEST_TS_PER_DAY, get_datetime_from_slice
from budget.memcache_budget import (remaining_ts_budget,
                                    total_spent,
                                    braking_fraction,
                                    )
from budget.query_managers import BudgetQueryManager
from common.utils.tzinfo import utc, Pacific

from google.appengine.ext import testbed

ONE_DAY = datetime.timedelta(days=1)
JUST_UNDER_ONE_DAY = datetime.timedelta(minutes=1435)
EVEN_STATIC_BUDGET = 50
EVEN_TOTAL = EVEN_STATIC_BUDGET * TEST_TS_PER_DAY



def build_has_budget_for_bids(budget):
    def helper(bid):
        if budget_service.has_budget(budget, bid):
            return (bid, True)
        else:
            return (bid, False)
    return helper

class TestBudgetUnitTests(unittest.TestCase):

    def test_mock_budget_advance(self, testing=False, advance_to_datetime = None):
        slice_num = budget_service._mock_budget_advance(advance_to_datetime, testing)
        self.e_c = Campaign.get(self.e_c.key())
        self.aao_c = Campaign.get(self.aao_c.key())
        self.e_budget = Budget.get(self.e_budget.key())
        self.aao_budget = Budget.get(self.aao_budget.key())
        return slice_num

    def test_advance(self, dtetime):
        slice_num = self.test_mock_budget_advance(testing=True, advance_to_datetime = dtetime)
        logging.warning("Advancing....")
        return slice_num

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.budget_start = datetime.datetime(2000,1,10,0)
        self.budget_end = datetime.datetime(2000,1,15,23,59)

        self.budget_arb_start = datetime.datetime(2000,1,10,4,33)
        self.budget_arb_end = datetime.datetime(2000,1,15,14,3)

        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit")
        self.adunit.put()

        self.e_budget = Budget(start_datetime = self.budget_start,
                               delivery_type = 'evenly',
                               static_slice_budget = 50.0,
                               active = True,
                               testing = True,
                               )
        self.aao_budget = Budget(start_datetime = self.budget_start,
                                 active = True,
                                 delivery_type = 'allatonce',
                                 static_total_budget = 5000.0,
                                 testing = True,
                                 )
        self.e_budget.put()
        self.aao_budget.put()

        # Make AllAtOnce Campaign
        self.aao_c = Campaign(name="allatonce",
                              budget_obj = self.aao_budget,
                              )
        self.aao_c.put()

        # Make Even Campaign
        self.e_c= Campaign(name="even",
                            budget_obj = self.e_budget,
                            )
        self.e_c.put()


    @property
    def bids(self):
        for i in xrange(5000):
            yield .05

    def tearDown(self):
        self.testbed.deactivate()
        # budget_service._flush_all()

    def update_adgroups(self):
        group_query = AdGroup.all().filter('name =', 'expensive')

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.put()

        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.put()

    def mptest_create_budget(self):
        test_c_1 = Campaign(name="HerpDerp",
                            start_datetime = datetime.datetime(2000,1,1,0),
                            end_datetime = datetime.datetime(2000,5,5,0),
                            budget = 288.0,
                            budget_type = 'daily',
                            budget_strategy = 'evenly',
                            active = True)

        test_c_2 = Campaign(name="HerpDerp2",
                            start_datetime = datetime.datetime(2000,1,1,0),
                            end_datetime = datetime.datetime(2000,5,5,0),
                            full_budget = 288.0,
                            budget_strategy = 'evenly',
                            active = True)
        test_c_3 = Campaign(name="HerpDerp3",
                            start_datetime = datetime.datetime(2000,1,1,0),
                            end_datetime = datetime.datetime(2000,5,5,0),
                            active = True)
        test_camps = [test_c_1, test_c_2, test_c_3]
        CampaignQueryManager.put(test_camps)
        assert test_c_1.budget_obj.static_slice_budget == 1
        assert test_c_2.budget_obj.static_total_budget == 288
        assert test_c_3.budget_obj is None


    
    def mptest_pause_campaign(self):
        test_c_1 = Campaign(name="HerpDerp",
                    start_datetime = datetime.datetime(2000,1,1,0),
                    end_datetime = datetime.datetime(2000,5,5,0),
                    budget = 288.0,
                    budget_type = 'daily',
                    budget_strategy = 'evenly',
                    active = True)
        CampaignQueryManager.put(test_c_1)
        assert test_c_1.budget_obj.active
        test_c_1.active = False
        CampaignQueryManager.put(test_c_1)
        assert not test_c_1.budget_obj.active

    
    def mptest_delete_campaign(self):
        test_c_1 = Campaign(name="HerpDerp",
                    start_datetime = datetime.datetime(2000,1,1,0),
                    end_datetime = datetime.datetime(2000,5,5,0),
                    budget = 288.0,
                    budget_type = 'daily',
                    budget_strategy = 'evenly',
                    active = True)
        CampaignQueryManager.put(test_c_1)
        assert test_c_1.budget_obj.active
        test_c_1.deleted = True
        CampaignQueryManager.put(test_c_1)
        assert not test_c_1.budget_obj.active

    def mptest_load_campaigns(self):
        eq_(5000,self.aao_c.budget_obj.static_total_budget)
        eq_(50,self.e_c.budget_obj.static_slice_budget)


    def mptest_to_memcache_int(self):
        val = 123.00
        same = budget_service._from_memcache_int(budget_service._to_memcache_int(val))
        eq_(val,same)

        val = -1
        same = budget_service._from_memcache_int(budget_service._to_memcache_int(val))
        eq_(val,same)

        val = 1
        same = budget_service._from_memcache_int(budget_service._to_memcache_int(val))
        eq_(val,same)

        val = 15000000
        same = budget_service._from_memcache_int(budget_service._to_memcache_int(val))
        eq_(val,same)

    def mptest_memcache_rollunder(self):
        #It does not appear that memcache allows rollunders, TODO: test in devappserver
        memcache.add("thing", 15)
        eq_(memcache.get("thing"),15)
        memcache.decr("thing", 8)
        eq_(memcache.get("thing"),7)
        memcache.decr("thing", 150)
        eq_(memcache.get("thing"),0)

    def mptest_even_basic(self):
        slice_num = self.test_advance(self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

    def mptest_aao_basic(self):
        slice_num = self.test_advance(self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.aao_budget, 50), True)

        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4950)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4850)


    def mptest_basic_cheap(self):
        slice_num = self.test_advance(self.budget_start)
        # We can do the cheap bidding 50 times
        for i in xrange(50):
            eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        # But it uses up all the timeslice's money and fails the 51st time
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_timeslices_update(self):
        slice_num = self.test_advance(self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

        # Then after we advance the timeslice
        self.test_mock_budget_advance(testing=True)
        # We now have more budget and can do the bid one more time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

    def mptest_timeslices_rollover(self):
        slice_num = self.test_advance(self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        # Then after we advance the timeslice
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)
        eq_(budget_service._apply_if_able(self.e_budget, 9), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 90)

        for i in xrange(90):
            eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        # But it uses up all the timeslice's money and fails the 91st time
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_multiple_campaigns(self):
        slice_num = self.test_advance(self.budget_start)
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 98)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4800)

    def mptest_multiple_campaigns_advance_twice(self):
        slice_num = self.test_advance(self.budget_start)
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 148)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4800)

    def mptest_remaining_daily_budget(self):
        # We have init'd the TS w/ 50
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        self.test_mock_budget_advance(testing=True)

        # We have moved 100 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        # We have moved 200 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.e_budget), 199)

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget),249)


    def mptest_remaining_daily_budget_planned(self):
        """ We have a planned campaign for tomorrow, make sure budget
            is correct """

        # The campaign has a $1000 daily budget, and goes for 1 day
        day_before_start = self.budget_start - ONE_DAY
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)

        slice_num = self.test_advance(self.budget_start)

        # After advancing to datetime.date(1987,4,4) we should have a budget
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

    def mptest_cache_failure_then_spend(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)
        budget_service._delete_memcache(self.e_budget)

        # Memcache miss -> restart timeslice
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

    def mptest_cache_failure_then_spend_multiple_timeslices(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        budget_service._delete_memcache(self.e_budget)
        # Memcache miss -> restart timeslice at last snapshot (99)
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 98)

    def mptest_cache_failure_then_apply_expense(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        budget_service._delete_memcache(self.e_budget)

        # Memcache miss -> restart timeslice
        budget_service.apply_expense(self.e_budget, 1)
        budget_service.apply_expense(self.e_budget, 1)

        # New system notices apply_expenses..

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 47)

    def mptest_cache_failure_then_advance(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 50)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        eq_(self.e_budget.spent_today, 0)

        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.spent_today, 50)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        budget_service._delete_memcache(self.e_budget)

        # Memcache miss -> restart spending at last snapshot (50)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.spent_today, 50)

        # 3 TS advances, should've spent 150, only spent 50, shoudl have 100 left
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

    def mptest_cache_failure_then_advance_multiple_timeslices(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        budget_service._delete_memcache(self.e_budget)
        # Memcache miss -> restart timeslice at last snapshot (99)

        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        # advanced 4 TS, spent 1, should have 199 left
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 198)

    def mptest_budget_logging_basic(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        self.test_mock_budget_advance(testing=True)

        last_log = self.e_budget.timeslice_logs.filter('slice_num = ', self.e_budget.curr_slice -1).get()
        eq_(last_log.actual_spending, 1)

    def mptest_very_expensive(self):

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 10000), False)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

    def mptest_remaining_daily_budget(self):
        # Even has 50 * 288 budget
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)


        eq_(self.e_budget.daily_budget, EVEN_TOTAL)
        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)

    def mptest_daily_budget_allatonce_budgetache_miss(self):
        # Even campaign has 50 * 288 total budget
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)
        logging.warning("Remaing TS Budget: %s" % remaining_ts_budget(self.e_budget))

        eq_(budget_service._apply_if_able(self.e_budget, 400), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 400)
        eq_(budget_service._apply_if_able(self.e_budget, 200), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)

        #self.test_advance(self.budget_start + ONE_DAY)
        budget_service._delete_memcache(self.e_budget)

        # Fall back to snapshot
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)

    def mptest_daily_budget_allatonce_budgetache_miss_ts(self):
        # Campain has 12 * 50 daily budget = 600
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 400), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 400)
        eq_(budget_service._apply_if_able(self.e_budget, 6000), False)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 400)

        slice_num = self.test_advance(self.budget_start + ONE_DAY) # to backup
        budget_service._delete_memcache(self.e_budget)

        # Fall back to snapshot
        slice_num = self.test_advance(self.budget_start + ONE_DAY + ONE_DAY) # to backup
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 400), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 400)



    def mptest_get_spending_for_date_range(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the second day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        second_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start,
                                                   self.budget_start,
                                                   testing = True)
        eq_(second_spending, 500)




    def mptest_get_spending_for_date(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start - ONE_DAY)
        eq_(budget_service._apply_if_able(self.e_budget, 500), False)


        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the second day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        second_spending = budget_service._get_spending_for_date(self.e_budget,
                                                      self.budget_start, testing=True)
        eq_(second_spending, 500)



    def mptest_get_spending_for_date_range_mult(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        logging.warning("INITIAL ADVANCE")
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the first day
        logging.warning("FIRST ADVANCE")
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the second day
        logging.warning("SECOND ADVANCE")
        slice_num = self.test_advance(self.budget_end)


        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the third day
        logging.warning("THIRD ADVANCE")
        slice_num = self.test_advance(self.budget_end + ONE_DAY)

        first_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                  self.budget_start,
                                                  self.budget_start,
                                                  testing = True,
                                                  )

        second_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                  self.budget_start + ONE_DAY,
                                                  self.budget_start + ONE_DAY,
                                                  testing = True)


        third_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_end-ONE_DAY,
                                                   self.budget_end,
                                                   testing = True)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start,
                                                   self.budget_end,
                                                   testing = True)

        total_spending2 = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start - ONE_DAY,
                                                   self.budget_end + ONE_DAY,
                                                   testing = True)
        #for log in BudgetSliceLog.all():
            #logging.warning("%s" % log)
        logging.warning("Spending 1, 3, tot, tot2: %s %s %s %s" % (first_spending, third_spending, total_spending, total_spending2))

        eq_(total_spending2, 1500)
        eq_(total_spending, 1500)
        eq_(third_spending, 500)
        eq_(first_spending, 500)

    def mptest_get_spending_for_date_range_mult_plus_today_no_rollover(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the first day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the second day
        slice_num = self.test_advance(self.budget_start + 2*ONE_DAY)


        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        # Three days have advanced and we have spent 1500 -> 1500 remains
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the third day
        slice_num = self.test_advance(self.budget_start + 3*ONE_DAY)

        # Three days have advanced and we have spent 1500
        # We have spent 0 today
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 100), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 100)

        self.test_mock_budget_advance(testing=True)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start - 2*ONE_DAY,
                                                   self.budget_end + 2*ONE_DAY,
                                                   testing = True)
        # 500 + 500 + 500 + 100 = 1600
        eq_(total_spending, 1600)

    def mptest_get_spending_for_date_range_mult_plus_today(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the first day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the second day
        slice_num = self.test_advance(self.budget_start + 2*ONE_DAY)


        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        # Three days have advanced and we have spent 1500 -> 1500 remains
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # The end of the third day
        slice_num = self.test_advance(self.budget_start + 3*ONE_DAY)

        # Three days have advanced and we have spent 1500
        # We have spent 0 today
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service._apply_if_able(self.e_budget, 100), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 100)

        self.test_mock_budget_advance(testing=True)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start - 2*ONE_DAY,
                                                   self.budget_end + 2*ONE_DAY,
                                                   testing = True)
        # 500 + 500 + 500 + 100 = 1600
        eq_(total_spending, 1600)


    def mptest_percent_delivered_finite(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.end_datetime = self.budget_start + JUST_UNDER_ONE_DAY
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL)

        eq_(budget_service.percent_delivered(self.e_budget), 0.0)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        self.test_mock_budget_advance(testing=True)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   self.budget_start - 2*ONE_DAY,
                                                   self.budget_end,
                                                   testing = True)
        eq_(total_spending, 500)

        per_deliv = 500/(EVEN_TOTAL*1.0)
        # We have delivered 50.0%
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

        # The end of the first day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        # We have still delivered 50.0%
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

    def mptest_percent_delivered_finite_mult_days(self):
        # The campaign has a $600 daily budget

        self.e_budget.delivery_type = "allatonce"
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        total_budget = self.e_budget.total_budget

        slice_num = self.test_advance(self.budget_start)
        #600 available

        eq_(budget_service.percent_delivered(self.e_budget), 0.0)
        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        #100

        # We have delivered some %
        per_deliv = 500 / (total_budget*1.0)
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

        # The end of the first day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        #700 available
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

        eq_(budget_service._apply_if_able(self.e_budget, 700), True)

        # We have delivered some more %
        per_deliv = 1200/(total_budget*1.0)
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

        # The end of the second day
        slice_num = self.test_advance(self.budget_start + 2*ONE_DAY)

        # We have still delivered some %
        eq_(budget_service.percent_delivered(self.e_budget), per_deliv)

    def mptest_percent_delivered_none(self):
        """ No end date, not finite, % deliv is None """
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service.percent_delivered(self.e_budget), 0.0)


    def mptest_finite_campaign(self):

         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.e_budget.end_datetime = self.budget_end
         self.e_budget.put()

         eq_(self.e_budget.finite, True)

    def mptest_remaining_daily_budget_finite(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        # Advance the budget 1 day (and 10 timeslices)
        slice_num = self.test_advance(self.budget_start)

        for i in xrange(10):
            self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

    def mptest_remaining_daily_budget_finite_budgetache_failure_no_rollover(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.spend_allocation = 'daily'
        self.e_budget.put()

        # Advance the budget 1 days (and 10 timeslices)
        slice_num = self.test_advance(self.budget_start)
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        for i in xrange(10):
            self.test_mock_budget_advance(testing=True)

        # 1000 remaining
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        # We have spent 100 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 100)

        # Catastrophic cache failure!!
        memcache.flush_all()

        # Should return to the state we had at the last backup (1000)
        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # Another advance, backs up to db
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)

        # Catastrophic cache failure again!!!
        memcache.flush_all()

        # Should return to the state we had at the last backup (500)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        # We have spent 600 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)


    def mptest_timeslices_preplanned(self):
        """ If a campaign is preplanned, it should not build up a timeslice
            budget surplus. Makes sure that preplanned campaigns still have a
            smooth delivery. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.spend_allocation = 'daily'
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        # Advance the budget to the second day of the campaign
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        # All of Day 1's budget wasn't spent, spend that shittttt

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        # One day + 2 TS's worth = EVEN_TOTAL + 150 alloc, less 500 = 
        # We have $EVEN_TOTAL - 350
        eq_(budget_service._apply_if_able(self.e_budget, EVEN_TOTAL - 350), True)

        # Now our budget is empty
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)


    def mptest_timeslices_underdelivering(self):
        """ We have a campaign that does not deliver for the first half of the
            campaign. The second half should therefore deliver at twice the
            regular speed. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        # Advance the budget 1 day (and 10 timeslices)
        slice_num = self.test_advance(self.budget_start)

        for i in xrange(10):
            # Try to apply this expense, but we can't because the TS budget isn't enough
            # it has to rollover!
            eq_(budget_service._apply_if_able(self.e_budget, 600), False)
            self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 500), True)

        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 500)


    def mptest_full_campaign_budget(self):
        # The aao_budget has a $5000 total budget
        # goes for 5 days inclusive -> $1,000/day
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        # Advance the budget
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 5000)

        self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 5000)

    def mptest_full_campaign_budget_later_end(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The aao_budget has a $5000 total budget
        # goes for 5 days inclusive -> $1,000/day
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        # Advance the budget and spend the full 1000
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.aao_budget, 1000), True)

        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 20 days total, 19 remain
        self.aao_budget.end_datetime = self.budget_end + 5 * ONE_DAY
        self.aao_budget.put()

        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 4000.)

    def mptest_full_campaign_budget_earlier_end(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The aao_budget has a $5000 total budget
        # goes for 5 days inclusive -> $1,000/day
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        # Advance the budget and spend the full 1000
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.aao_budget, 1000), True)

        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 5 days total, 4 days remain
        self.aao_budget.end_datetime = self.budget_end - 2*ONE_DAY
        self.aao_budget.put()
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 4000)

    def mptest_full_campaign_budget_increase_budget(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The aao_budget has a $5000 total budget
        # goes for 5 days inclusive -> $1,000/day
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        # Advance the budget and spend the full 1000
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.aao_budget, 1000), True)

        # 9K budget remains, but before the end of the first day we
        # increase the budget. Now we have 9 days and 18000 more to spend.
        self.aao_budget.set_total_budget(10000)
        self.aao_budget.put()
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 9000.)

    def mptest_full_campaign_budget_consistent_underdeliver(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The aao_budget has a $5000 total budget
        # goes for 5 days inclusive -> $1,000/day
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        # Advance the budget and spend 500, twice
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.aao_budget, 500), True)

        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service._apply_if_able(self.aao_budget, 500), True)

        slice_num = self.test_advance(self.budget_start + 2*ONE_DAY)

        eq_(budget_service.remaining_daily_budget(self.aao_budget), 4000)

    def mptest_daily_campaign_increase_budget(self):
        self.e_budget.spend_allocation = "daily"
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 200), False)

        self.e_budget.set_total_daily_budget(1200)
        self.e_budget.put()

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)

    def mptest_full_campaign_change_budget(self):
        self.aao_budget.end_datetime = self.budget_end
        self.aao_budget.put()

        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.aao_budget, 500), True)

        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        eq_(budget_service._apply_if_able(self.aao_budget, 500), True)

        self.aao_budget.set_total_budget(2000)
        self.aao_budget.put()

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.aao_budget, 1000), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

    def mptest_full_campaign_change_length(self):
        self.aao_budget.end_datetime = self.budget_start + 3*ONE_DAY
        self.aao_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.aao_budget, 500), True)
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        self.aao_budget.end_datetime = self.budget_start + 2*ONE_DAY
        self.aao_budget.put()

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.aao_budget, 4500), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), False)

    def mptest_full_campaign_budget_evenly(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.static_total_budget = 6000.0
        self.e_budget.static_slice_budget = None
        self.e_budget.put()

        eq_(self.e_budget.is_active_for_date(self.budget_start),True)
        eq_(self.e_budget.is_active_for_date(self.budget_start - ONE_DAY),False)
        eq_(self.e_budget.is_active_for_date(self.budget_end),True)
        eq_(self.e_budget.is_active_for_date(self.budget_end + ONE_DAY),False)

        # Advance the budget and the ts budgets
        slice_num = self.test_advance(self.budget_start)

        # 1000 remaining because the 6K budget is split between the 6 remaining days
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)
        logging.warning("Next slice budget: %s" % self.e_budget.next_slice_budget)

        # Advance the budget and the ts budgets
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        logging.warning("Next slice budget after skip: %s" % self.e_budget.next_slice_budget)

        # 12 slices for today, each slice should have 100, try it, make it work
        eq_(budget_service._apply_if_able(self.e_budget, float('%.5f' % (1000 + self.e_budget.slice_budget))), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_timeslice_changes(self):
        self.e_budget.end_datetime = self.e_budget.start_datetime + ONE_DAY
        self.e_budget.put()

        # Advance the budget and the ts budgets
        slice_num = self.test_advance(self.budget_start)

        # 50 TS budget, spend it
        eq_(budget_service._apply_if_able(self.e_budget,50), True)

        self.test_mock_budget_advance(testing=True)
        # 50 left, unspent
        self.e_budget.set_total_daily_budget(3000)
        self.e_budget.put()
        # New static_ts_budget is 250 PER SLICE. 2 slices went by, should be 500, spent 50, have 50
        self.test_mock_budget_advance(testing=True)
        # Third slice, should have spent 750, only have spent 50, should have 700 to spend

        eq_(budget_service._apply_if_able(self.e_budget, 700), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_campaign_starts_midday(self):
        # 4hrs, 33mins into the day
        # 2hrs per ts,
        # TS 0 --> 0:00 -> 1:59
        # TS 1 --> 2:00 -> 3:59
        # TS 2 --> 4:00 -> 5:59 ---> GOGOGOOGOOG
        self.e_budget.start_datetime = self.budget_arb_start
        self.e_budget.end_datetime = self.budget_arb_end
        self.e_budget.put()

        # Advance the budget and the ts budgets.  START OF THE DAY, SHOULD NOT WORK
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget,1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget,1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget,50), True)

        eq_(budget_service._apply_if_able(self.e_budget,1), False)

    def mptest_test_activity(self):

        eq_(self.e_budget.is_active_for_date(self.budget_start),True)

        self.e_budget.start_datetime = self.budget_start + ONE_DAY
        self.e_budget.put()

        eq_(self.e_budget.is_active_for_date(self.budget_start),False)

        self.e_budget.end_datetime = self.budget_start + 2*ONE_DAY
        self.e_budget.put()

        eq_(self.e_budget.is_active_for_date(self.budget_start), False)
        eq_(self.e_budget.is_active_for_date(self.budget_start + 3*ONE_DAY), False)
        eq_(self.e_budget.is_active_for_datetime(self.budget_start + 1*ONE_DAY), True)
        eq_(self.e_budget.is_active_for_datetime(self.budget_start + 2*ONE_DAY), True)

    def mptest_calc_braking_fraction_simple(self):
        # We wanted to spend 100, but spent 200 instead.
        fraction = budget_service.calc_braking_fraction(100.0, 200.0, 1.0)

        eq_(fraction, 0.5)

        # We wanted to spend 100, but only spent 50.
        fraction = budget_service.calc_braking_fraction(100.0, 50.0, 0.1)

        eq_(fraction, 0.2)

        # Never go above 1.0
        # We wanted to spend 50, but spent 100.
        fraction = budget_service.calc_braking_fraction(100.0, 50.0, 0.8)

        eq_(fraction, 1.0)

        fraction = budget_service.calc_braking_fraction(100.0, 110.0, 0.8)

        eq_(fraction, 0.8 / (110.0/100))


        # If we deliver about the right amount, leave the fraction the same
        fraction = budget_service.calc_braking_fraction(114.0, 110.0, 0.8)
        eq_(fraction, 0.8 / (110/114.0))



    def mptest_total_aao_end_update_datetime(self):
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 5000.
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 4050), True)
        BudgetQueryManager.prep_update_budget(self.e_budget, start_datetime = self.e_budget.start_datetime + datetime.timedelta(minutes=480))

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 50), False)

        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 950), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_total_evenly_end_update_datetime(self):
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 7200.
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        # on slice 3, each slice has 100 to spend, 

        BudgetQueryManager.prep_update_budget(self.e_budget, start_datetime = self.e_budget.start_datetime + ONE_DAY)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 100), False)

        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 60), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 120), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 120), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 120), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 720)

    def mptest_total_evenly_end_update_budget(self):
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 7200.
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 14400)

        self.test_mock_budget_advance(testing=True)
        # Expected to spend 200/slice, spent 100 in 2 slices, 300 left
        eq_(budget_service._apply_if_able(self.e_budget, 300), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 300), False)
        eq_(budget_service._apply_if_able(self.e_budget, 200), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 7200)

        self.test_mock_budget_advance(testing=True)
        # spent 600, expected to spend 400, 100/slice, 
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 200), False)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 200), False)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(self.e_budget.total_spent, 800)
        pass

    def mptest_total_aao_end_update_budget(self):
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 7200.
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 7000), True)
        eq_(budget_service._apply_if_able(self.e_budget, 200), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 10200)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 2900), True)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 7200)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 10201)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 10201)

    def mptest_total_aao_no_end_update_datetime(self):
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 5000.
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 4050), True)
        BudgetQueryManager.prep_update_budget(self.e_budget, start_datetime = self.e_budget.start_datetime + datetime.timedelta(minutes=480))

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 50), False)

        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 950), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)


    def mptest_total_aao_no_end_update_budget(self):
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.static_slice_budget = None
        self.e_budget.static_total_budget = 7200.
        self.e_budget.put()

        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 7000), True)
        eq_(budget_service._apply_if_able(self.e_budget, 200), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 10200)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 2900), True)
        eq_(budget_service._apply_if_able(self.e_budget, 100), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 7200)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_total_budget = 10201)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 10201)


    # 50 per TS for all these dudes, 600 total
    def mptest_daily_aao_end_update_budget(self):
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 100)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 10)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service._apply_if_able(self.e_budget, 10), False)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 101)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service._apply_if_able(self.e_budget, 12), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(self.e_budget.total_spent, 1212)

    def mptest_daily_evenly_end_update_budget(self):
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        # should spent 50, did

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 10)
        self.test_mock_budget_advance(testing=True)
        # should've spent 20, spent 50   2TS
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        # should've spent 30, spent 50   3TS
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        # should've spent 40, spent 50   4TS
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        # should've spent 50, spent 50   5TS
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        # should've spent 60, spent 50   6TS

        eq_(budget_service._apply_if_able(self.e_budget, 10), True)
        # should've spent 60, spent 60
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 100)
        self.test_mock_budget_advance(testing=True)
        # should've spent 700, spent 60

        eq_(budget_service._apply_if_able(self.e_budget, 640), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 700)


    # 50 per TS for all these dudes, 600 total
    def mptest_daily_aao_end_update_datetime(self):
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 300), True)
        BudgetQueryManager.prep_update_budget(self.e_budget, end_datetime = self.e_budget.end_datetime - ONE_DAY)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 300), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, start_datetime = self.e_budget.start_datetime - ONE_DAY)
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        # 2 days (according to the update) have been processed.  
        # We should have spent 1800, only spent 600, 1200 today
        eq_(budget_service._apply_if_able(self.e_budget, 1200), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 1800)


    # 50 per TS for all these dudes, 600 total
    def mptest_daily_evenly_end_update_datetime(self):
        self.e_budget.end_datetime = self.budget_end
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        BudgetQueryManager.prep_update_budget(self.e_budget, end_datetime = self.e_budget.end_datetime - ONE_DAY)
        # changing the enddate of a daily campaign doesn't really do anything....
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, start_datetime = self.e_budget.start_datetime - ONE_DAY)
        self.test_mock_budget_advance(testing=True)
        # as before, we've spent 100, the budget now began a day before now, 
        # so we should've spent all 600 + 100 for today.  New Ts should have 650
        eq_(budget_service._apply_if_able(self.e_budget, 650), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        # Now that we spent the buildup, we shouldn't have any more than a single TS
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)

        eq_(self.e_budget.total_spent, 800)

    #50/slice = 600/day
    def mptest_daily_aao_no_end_update_budget(self):
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 300), True)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 10)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        #10/slice = 120/day
        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        #120/day, days don't roll over
        eq_(budget_service._apply_if_able(self.e_budget, 120), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 20)
        logging.warning("\nPre Advance\nBUDGET IN QUESTION: %s\n\n" % self.e_budget)
        self.test_mock_budget_advance(testing=True)
        logging.warning("\nPost Advance\nBUDGET IN QUESTION: %s\n\n" % self.e_budget)
        logging.warning("Expected: %s  Total: %s" % (self.e_budget.expected_spent, self.e_budget.spent_today))
        eq_(budget_service._apply_if_able(self.e_budget, 120), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        # Because end dates aren't set, the total spent constrains NOTHING
        eq_(self.e_budget.total_spent, 540)

    #50/slice 600/day
    def mptest_daily_evenly_no_end_update_budget(self):
        slice_num = self.test_advance(self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 20)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 10), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        BudgetQueryManager.prep_update_budget(self.e_budget, static_slice_budget = 1)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        self.test_mock_budget_advance(testing=True)

        # Because end dates aren't set, the total spent constrains NOTHING
        eq_(self.e_budget.total_spent, 62)


    def mptest_daily_aao_no_end_update_datetime(self):
        # Meaningless test, no end date -> changing start datetime won't do anything
        pass

    def mptest_daily_evenly_no_end_update_datetime(self):
        # Meaningless test, no end date -> changing start datetime won't do anything
        pass


    # sum of bids is 250, we only have 50, should only let 20% through
    def mptest_memcache_overspend(self):
        """ Simulate multiple machines reading True from memcache when
        only a small number of these machines should """

        slice_num = self.test_advance(self.budget_start)
        tuples = map(build_has_budget_for_bids(self.e_budget), self.bids)

        # They should all be True the first time through
        tot = 0.
        tot_apply = 0.
        for bid, should_apply in tuples:
            tot += 1
            if should_apply:
                tot_apply += 1
                budget_service.apply_expense(self.e_budget, bid)
        eq_(tot_apply/tot, 1)
        # hella overspent.  Should've spent 50, spent 250
        self.test_mock_budget_advance(testing=True)
        # 100
        self.test_mock_budget_advance(testing=True)
        # 150
        self.test_mock_budget_advance(testing=True)
        # 200
        self.test_mock_budget_advance(testing=True)
        # 250
        self.test_mock_budget_advance(testing=True)
        # 300, spent 250, have 50, but braking in place!
        tuples = map(build_has_budget_for_bids(self.e_budget), self.bids)
        # They should all be True the first time through
        tot = 0.
        tot_apply = 0.
        for bid, should_apply in tuples:
            tot += 1
            if should_apply:
                tot_apply += 1
                budget_service.apply_expense(self.e_budget, bid)
        logging.warning("Total bids: %s  Applied bids: %s  %%Applied: %s" % (tot, tot_apply, tot_apply/tot))
        assert_almost_equal(round(tot_apply/tot, 1), 0.2, 2)


    def mptest_daily_start(self):
        """ Given that a 'day' can start at an arbitrary time, test that it actually
        works as expected """
        self.aao_budget.static_slice_budget = 50.0
        self.aao_budget.static_total_budget = None
        self.aao_budget.day_tz = 'Pacific'
        self.aao_budget.put()
        self.e_budget.delivery_type = 'allatonce'
        self.e_budget.put()
        slice_num = self.test_advance(self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        eq_(budget_service._apply_if_able(self.aao_budget, 600), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        # TS 13, e_budget should be on a new day, the other one shoudl not be
        self.test_mock_budget_advance(testing=True)
        logging.warning("Time1: %s" % get_datetime_from_slice(self.e_budget.curr_slice, testing=True))
        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 600), False)

        #Day 2 ts 2
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.aao_budget, 600), False)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        #Day 2 ts 3
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.aao_budget, 600), False)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

        #Day 2 ts 4, 8 hours in, should be new day
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)

        self.test_mock_budget_advance(testing=True)
        logging.warning("Time2: %s" % get_datetime_from_slice(self.e_budget.curr_slice, testing=True))
        eq_(budget_service._apply_if_able(self.aao_budget, 600), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)
        eq_(budget_service._apply_if_able(self.aao_budget, 1), False)


