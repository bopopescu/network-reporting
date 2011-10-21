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
from budget.models import (Budget,
                           BudgetSliceLog,
                           )
from budget.helpers import get_slice_from_datetime

from google.appengine.ext import testbed

ONE_DAY = datetime.timedelta(days=1)
EVEN_TOTAL = 50 * 288

#from budget.query_managers import BudgetSliceLogQueryManager

def test_advance(budget, dtetime):
    slice_num = budget_service.timeslice_advance(budget, testing=True, advance_to_datetime = dtetime)
    logging.warning("Budget is %s" % budget)
    return slice_num

class TestBudgetUnitTests(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.budget_start = datetime.datetime(2000,1,10,0)
        self.budget_end = datetime.datetime(2000,1,15,0)

        self.budget_arb_start = datetime.datetime(2000,1,10,4,33)
        self.budget_arb_end = datetime.datetime(2000,1,15,14,3)

        # We simplify the budgetmanger for testing purposes
        #budgetmodels.DEFAULT_TIMESLICES = 10 # this means each campaign has 100 dollars per slice
        #budgetmodels.DEFAULT_FUDGE_FACTOR = 0.0

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
                               )
        self.aao_budget = Budget(start_datetime = self.budget_start,
                                 delivery_type = 'allatonce',
                                 static_total_budget = 5000.0,
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

#        self.expensive_adgroup = AdGroup(account=self.account,
#                                          campaign=self.expensive_budget,
#                                          site_keys=[self.adunit.key()],
#                                          bid_strategy="cpc",
#                                          bid=100000.0) # 100 per click
#        self.expensive_adgroup.put()
#
#        self.expensive_budgetreative = Creative(account=self.account,
#                                ad_group=self.expensive_adgroup,
#                                tracking_url="test-tracking-url",
#                                cpc=.03)
#        self.expensive_budgetreative.put()
#
#        self.cheap_adgroup = AdGroup(account=self.account,
#                              campaign=self.e_budget,
#                              site_keys=[self.adunit.key()],
#                              bid_strategy="cpc",
#                              budget=1000.0,
#                              budget_strategy="evenly",
#                              bid=10000.0)
#        self.cheap_adgroup.put()
#
#
#        self.e_budgetreative = Creative(account=self.account,
#                                ad_group=self.cheap_adgroup,
#                                tracking_url="test-tracking-url",
#                                cpc=.03)
#        self.e_budgetreative.put()

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
        slice_num = test_advance(self.e_budget, self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

    def mptest_aao_basic(self):
        slice_num = test_advance(self.aao_budget, self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.aao_budget, 50), True)

        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4950)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4850)


    def mptest_basic_cheap(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        # We can do the cheap bidding 50 times
        for i in xrange(50):
            eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        # But it uses up all the timeslice's money and fails the 51st time
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_timeslices_update(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

        # Then after we advance the timeslice
        budget_service.timeslice_advance(self.e_budget)
        # We now have more budget and can do the bid one more time
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        # But it uses up all the timeslice's money and fails the second
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 0)

    def mptest_timeslices_rollover(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        # Then after we advance the timeslice
        budget_service.timeslice_advance(self.e_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)
        eq_(budget_service._apply_if_able(self.e_budget, 9), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 90)

        for i in xrange(90):
            eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        # But it uses up all the timeslice's money and fails the 91st time
        eq_(budget_service._apply_if_able(self.e_budget, 1), False)

    def mptest_multiple_budgetampaigns(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        slice_num = test_advance(self.aao_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        budget_service.timeslice_advance(self.e_budget)
        budget_service.timeslice_advance(self.aao_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 98)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4800)

    def mptest_multiple_budgetampaigns_advance_twice(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        slice_num = test_advance(self.aao_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service._apply_if_able(self.aao_budget, 100), True)

        budget_service.timeslice_advance(self.e_budget)
        budget_service.timeslice_advance(self.e_budget)
        budget_service.timeslice_advance(self.aao_budget)
        budget_service.timeslice_advance(self.aao_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 148)
        eq_(budget_service.remaining_ts_budget(self.aao_budget), 4800)

    def mptest_remaining_daily_budget(self):
        # We have init'd the TS w/ 50
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        budget_service.timeslice_advance(self.e_budget)

        # We have moved 100 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        budget_service.timeslice_advance(self.e_budget)
        budget_service.timeslice_advance(self.e_budget)

        # We have moved 200 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.e_budget), 199)

        budget_service.timeslice_advance(self.e_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget),249)


    def mptest_remaining_daily_budget_planned(self):
        """ We have a planned campaign for tomorrow, make sure budget
            is correct """

        # The campaign has a $1000 daily budget, and goes for 1 day
        day_before_start = self.budget_start - ONE_DAY
        self.e_budget.end_dateime = self.budget_end
        self.e_budget.put()

        slice_num = test_advance(self.e_budget, day_before_start)
        eq_(budget_service._apply_if_able(self.e_budget, 100), False)

        slice_num = test_advance(self.e_budget, self.budget_start)

        # After advancing to datetime.date(1987,4,4) we should have a budget
        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

    def mptest_cache_failure_then_spend(self):
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)
        budget_service._delete_memcache(self.e_budget)

        # Memcache miss -> restart timeslice
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

    def mptest_cache_failure_then_spend_multiple_timeslices(self):
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)

        budget_service.timeslice_advance(self.e_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        budget_service._delete_memcache(self.e_budget)
        # Memcache miss -> restart timeslice at last snapshot (99)
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 98)

    def mptest_cache_failure_then_apply_expense(self):
        slice_num = test_advance(self.e_budget, self.budget_start)

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
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 50)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        eq_(self.e_budget.spent_today, 0)

        budget_service.timeslice_advance(self.e_budget)

        eq_(self.e_budget.spent_today, 50)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)

        budget_service._delete_memcache(self.e_budget)

        # Memcache miss -> restart spending at last snapshot (50)
        budget_service.timeslice_advance(self.e_budget)

        eq_(self.e_budget.spent_today, 50)

        # 3 TS advances, should've spent 150, only spent 50, shoudl have 100 left
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

    def mptest_cache_failure_then_advance_multiple_timeslices(self):
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        budget_service.timeslice_advance(self.e_budget)

        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

        budget_service._delete_memcache(self.e_budget)
        # Memcache miss -> restart timeslice at last snapshot (99)

        budget_service.timeslice_advance(self.e_budget)
        budget_service.timeslice_advance(self.e_budget)

        # advanced 4 TS, spent 1, should have 199 left
        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 198)

    def mptest_budget_logging_basic(self):
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 50), True)
        budget_service.timeslice_advance(self.e_budget)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 49)

        budget_service.timeslice_advance(self.e_budget)

        last_log = self.e_budget.last_slice_log
        eq_(last_log.actual_spending, 1)

    def mptest_very_expensive(self):
        slice_num = test_advance(self.e_budget, self.budget_start)
        eq_(budget_service._apply_if_able(self.e_budget, 10000), False)

        eq_(budget_service._apply_if_able(self.e_budget, 1), True)
        eq_(budget_service.remaining_ts_budget(self.e_budget), 99)

    def mptest_remaining_daily_budget(self):
        # Even has 50 * 288 budget
        self.e_budget.delivery_type = "allatonce"
        self.e_budget.put()
        slice_num = test_advance(self.e_budget, self.budget_start)


        eq_(budget_service.daily_budget(self.e_budget), EVEN_TOTAL)
        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)

    def mptest_daily_budget_allatonce_budgetache_miss(self):
        # Even campaign has 50 * 288 total budget
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.put()
        slice_num = test_advance(self.e_budget, self.budget_start)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)
        eq_(budget_service._apply_if_able(self.e_budget, 200), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 1000)

        test_advance(self.e_budget, self.budget_start + ONE_DAY)
        budget_service._delete_memcache(self.e_budget)

        # Fall back to snapshot
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), EVEN_TOTAL - 600)

    def mptest_daily_budget_allatonce_budgetache_miss_ts(self):
        # Each campaign has $1000 total budget
        self.expensive_budget.budget_strategy = "allatonce"
        self.expensive_budget.put()

        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.put()

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), 400)
        eq_(budget_service._apply_if_able(self.e_budget, 600), False)
        eq_(budget_service.remaining_daily_budget(self.e_budget), 400)

        budget_service.daily_advance(self.e_budget)
        budget_service.timeslice_advance(self.e_budget,testing=True) # to backup
        budget_service._delete_memcache(self.e_budget)

        # Fall back to snapshot
        budget_service.daily_advance(self.e_budget)
        budget_service.timeslice_advance(self.e_budget,testing=True) # to backup
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service._apply_if_able(self.e_budget, 600), True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), 400)



    def mptest_get_spending_for_date_range(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
         self.e_budget.budget_strategy = "allatonce"
         self.e_budget.start_date = datetime.date(1987,4,4)
         self.e_budget.end_date = datetime.date(1987,4,4)
         self.e_budget.put()


         eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)

         eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

         # The end of the second day
         budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

         second_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                    datetime.date(1987,4,4),
                                                    datetime.date(1987,4,4))
         eq_(second_spending, 500)




    def mptest_get_spending_for_date(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
         self.e_budget.budget_strategy = "allatonce"
         self.e_budget.start_date = datetime.date(1987,4,4)
         self.e_budget.end_date = datetime.date(1987,4,4)
         self.e_budget.put()

         # Today is datetime.date(1987,4,3)
         today = datetime.date(1987,4,3)
         eq_(budget_service._apply_if_able(self.e_budget, 500, today=today), False)


         # The end of the first day
         budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))

         eq_(budget_service._apply_if_able(self.e_budget, 500,today=datetime.date(1987,4,4)), True)

         eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

         # The end of the second day
         budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))


         second_spending = budget_service._get_spending_for_date(self.e_budget,
                                                      datetime.date(1987,4,4))
         eq_(second_spending, 500)



    def mptest_get_spending_for_date_range_mult_no_rollover(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,7)
        self.e_budget.put()

        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the first day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,5)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the second day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,6))


        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,6)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the third day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,7))



        first_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,4),
                                                   datetime.date(1987,4,4))
        eq_(first_spending, 500)

        second_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,5),
                                                   datetime.date(1987,4,5))


        third_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,6),
                                                   datetime.date(1987,4,6))
        eq_(third_spending, 500)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,4),
                                                   datetime.date(1987,4,6))
        eq_(total_spending, 1500)

        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8))
        eq_(total_spending, 1500)

    def mptest_get_spending_for_date_range_mult_plus_today_no_rollover(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,10)
        self.e_budget.put()

        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the first day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,5)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the second day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,6))


        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,6)), True)

        # Three days have advanced and we have spent 1500 -> 1500 remains
        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # The end of the third day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,7))

        # Three days have advanced and we have spent 1500
        # We have spent 0 today
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service._apply_if_able(self.e_budget, 100, today=datetime.date(1987,4,7)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 900)


        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8))
        # 4000 - 2400 = 1600
        eq_(total_spending, 1600)


    def mptest_percent_delivered_finite(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,4)
        self.e_budget.put()

        # Start out at the date 1987/4/4
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        eq_(budget_service.percent_delivered(self.e_budget), 0.0)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)

        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)


        total_spending = budget_service.get_spending_for_date_range(self.e_budget,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8),
                                                   today=datetime.date(1987,4,4))
        eq_(total_spending, 500)


        # We have delivered 50.0%
        eq_(budget_service.percent_delivered(self.e_budget, today=datetime.date(1987,4,4)), 50.0)

        # The end of the first day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        # We have still delivered 50.0%
        eq_(budget_service.percent_delivered(self.e_budget), 50.0)

    def mptest_percent_delivered_finite_ten_days(self):
        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.put()

        eq_(budget_service.percent_delivered(self.e_budget, today=datetime.date(1987,4,4)), 0.0)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)

        # We have delivered 5.0%
        eq_(budget_service.percent_delivered(self.e_budget, today=datetime.date(1987,4,4)), 5.0)

        # The end of the first day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service.percent_delivered(self.e_budget), 5.0)

        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,5)), True)

        # We have delivered 15.0%
        eq_(budget_service.percent_delivered(self.e_budget, today=datetime.date(1987,4,5)), 15.0)

        # The end of the second day
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,6))

        # We have still delivered 15.0%
        eq_(budget_service.percent_delivered(self.e_budget), 15.0)

    def mptest_percent_delivered_none(self):
         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.e_budget.budget_strategy = "allatonce"
         self.e_budget.budget = None
         self.e_budget.put()

         eq_(budget_service.percent_delivered(self.e_budget), None)


    def mptest_finite_budgetampaign(self):

         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.e_budget.budget_strategy = "evenly"
         self.e_budget.start_date = datetime.date(1987,4,4)
         self.e_budget.end_date = datetime.date(1987,4,13)
         self.e_budget.put()

         eq_(self.e_budget.finite, True)

         eq_(self.expensive_budget.finite, False)


    def mptest_remaining_daily_budget_finite(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.put()

        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

    def mptest_remaining_daily_budget_finite_budgetache_failure_no_rollover(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.put()

        # Advance the budget 1 days (and 10 timeslices)
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-2):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        # 1000 remaining
        eq_(budget_service._apply_if_able(self.e_budget, 100, today=datetime.date(1987,4,5)), True)
        # We have spent 100 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), 900)

        # Catastrophic cache failure!!
        memcache.flush_all()

        # Should return to the state we had at the last backup (1000)
        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,5)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # Another advance, backs up to db
        budget_service.timeslice_advance(self.e_budget,testing=True)
        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)

        # Catastrophic cache failure again!!!
        memcache.flush_all()

        # Should return to the state we had at the last backup (500)
        eq_(budget_service._apply_if_able(self.e_budget, 100, today=datetime.date(1987,4,5)), True)
        # We have spent 600 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), 400)


    def mptest_timeslices_preplanned(self):
        """ If a campaign is preplanned, it should not build up a timeslice
            budget surplus. Makes sure that preplanned campaigns still have a
            smooth delivery. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.put()

        # Start on 1987/4/3
        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        # Advance the budget to the second day of the campaign
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        # The first two days' budget should be spread across this day. each timeslice is worth $100

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,5)), False)
        budget_service.timeslice_advance(self.e_budget,testing=True)
        budget_service.timeslice_advance(self.e_budget,testing=True)

        # We have $125
        eq_(budget_service._apply_if_able(self.e_budget, 125, today=datetime.date(1987,4,5)), True)

        # Now our budget is empty
        eq_(budget_service._apply_if_able(self.e_budget, 1, today=datetime.date(1987,4,5)), False)


    def mptest_timeslices_underdelivering(self):
        """ We have a campaign that does not deliver for the first half of the
            campaign. The second half should therefore deliver at twice the
            regular speed. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.put()

        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.e_budget), 500)


    def mptest_full_campaign_budget(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        # Advance the budget
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))

        # 1000 remaining because the 10K budget is split between the 10 remaining days
        eq_(budget_service.remaining_daily_budget(self.e_budget), 10000)

        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        # 1111.11 remaining because the 10K budget is split between the 9 remaining days
        eq_(budget_service.remaining_daily_budget(self.e_budget), 10000)

    def mptest_full_campaign_budget_later_end(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,4)), True)

        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 20 days total, 19 remain
        self.e_budget.end_date = datetime.date(1987,4,23)
        self.e_budget.put()
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        # ~480 remaining because the 10K budget is split between the 19 remaining days
        eq_(budget_service.remaining_daily_budget(self.e_budget), 9000.)

    def mptest_full_campaign_budget_earlier_end(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,4)), True)

        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 5 days total, 4 days remain
        self.e_budget.end_date = datetime.date(1987,4,8)
        self.e_budget.put()
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service.remaining_daily_budget(self.e_budget), 9000)

    def mptest_full_campaign_budget_increase_budget(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,4)), True)

        # 9K budget remains, but before the end of the first day we
        # increase the budget. Now we have 9 days and 18000 more to spend.
        self.e_budget.full_budget = 19000.
        self.e_budget.put()
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service.remaining_daily_budget(self.e_budget), 18000.)

    def mptest_full_campaign_budget_consistent_underdeliver(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        # Advance the budget and spend 500, twice
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4)), True)
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))

        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,5)), True)

        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,6))

        eq_(budget_service.remaining_daily_budget(self.e_budget), 9000)

    def mptest_daily_campaign_increase_budget(self):
        self.e_budget.budget_type = "daily"
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,6)
        self.e_budget.put()

        budget_service.daily_advance(self.e_budget, new_date=self.e_budget.start_date)
        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.e_budget, 200, today=datetime.date(1987,4,4)), False)

        self.e_budget.budget = 1200.
        self.e_budget.put()
        budget_service.update_budget(self.e_budget, dt=datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.e_budget, 200, today=datetime.date(1987,4,5)), True)
        eq_(budget_service._apply_if_able(self.e_budget, 100, today=datetime.date(1987,4,4)), False)

    def mptest_full_campaign_change_budget(self):
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.full_budget = 3000.
        self.e_budget.start_date = datetime.date(1987,4,3)
        self.e_budget.end_date = datetime.date(1987,4,5)
        self.e_budget.put()

        budget_service.daily_advance(self.e_budget, new_date=self.e_budget.start_date)
        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,3)), True)

        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))

        budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,4))
        self.e_budget.full_budget = 2000.
        self.e_budget.put()
        budget_service.update_budget(self.e_budget, dt=datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.e_budget, 1000, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.e_budget, 1, today=datetime.date(1987,4,4)), False)

    def mptest_full_campaign_change_length(self):
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.budget_strategy = "allatonce"
        self.e_budget.full_budget = 3000.
        self.e_budget.start_date = datetime.date(1987,4,3)
        self.e_budget.end_date = datetime.date(1987,4,5)
        self.e_budget.put()

        budget_service.daily_advance(self.e_budget, new_date=self.e_budget.start_date)
        eq_(budget_service._apply_if_able(self.e_budget, 500, today=datetime.date(1987,4,3)), True)

        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))

        self.e_budget.end_date = datetime.date(1987,4,4)
        self.e_budget.put()
        budget_service.update_budget(self.e_budget, dt = datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.e_budget, 2500, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.e_budget, 100, today=datetime.date(1987,4,4)), False)

    def mptest_full_campaign_budget_evenly(self):
        # We have a campaign that was set to begin several days ago
        # but is only beginning now.

        # The e_budgetampaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,13)
        self.e_budget.budget_type = "full_campaign"
        self.e_budget.full_budget = 10000.
        self.e_budget.put()

        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,4)),True)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,13)),True)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,14)),False)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,3)),False)

        # Advance the budget and the ts budgets
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        # 1000 remaining because the 10K budget is split between the 10 remaining days
        eq_(budget_service.remaining_daily_budget(self.e_budget), 1000)

        # Advance the budget and the ts budgets
        budget_service.daily_advance(self.e_budget, new_date=datetime.date(1987,4,5))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES):
            budget_service.timeslice_advance(self.e_budget,testing=True)

        # 1111.11 remaining because the 10K budget is split between the 9 remaining days
        assert_almost_equal(budget_service.remaining_daily_budget(self.e_budget), 10000./9, 5)

        # We can actually spend all the money, this means the timeslices have
        # been advanced properly
        eq_(budget_service._apply_if_able(self.e_budget, 1111.11111, today=datetime.date(1987,4,5)), True)

    def mptest_timeslice_budgethanges(self):
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.budget_type = "daily"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = self.e_budget.start_date
        self.e_budget.put()

        budget_service.update_budget(self.e_budget, dt = datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.e_budget,100, today=datetime.date(1987,4,4)), True)

        budget_service.timeslice_advance(self.e_budget,testing=True)
        self.e_budget.budget = 3000.
        self.e_budget.put()

        budget_service.update_budget(self.e_budget, dt = datetime.datetime(1987,4,4,2,30,0))

        eq_(budget_service._apply_if_able(self.e_budget,322.2222, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.e_budget,1, today=datetime.date(1987,4,4)), False)

    def mptest_campaign_starts_midday(self):
        self.e_budget.budget_strategy = "evenly"
        self.e_budget.budget_type = "daily"
        self.e_budget.start_date = datetime.date(1987,4,4)
        self.e_budget.end_date = datetime.date(1987,4,4)
        self.e_budget.put()

        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,4)),True)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,5)),False)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,3)),False)

        budget_service.update_budget(self.e_budget, dt=datetime.datetime(1987,4,4,12,0,0))
        eq_(budget_service._apply_if_able(self.e_budget,200, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.e_budget,1, today=datetime.date(1987,4,4)), False)

    def mptest_test_activity(self):
        self.e_budget.budget_type = "daily"

        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,4)),True)

        self.e_budget.start_date = datetime.date(1987,4,4)

        eq_(self.e_budget.is_active_for_date(datetime.date(1997,4,4)),True)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,3)),False)


        self.e_budget.end_date = datetime.date(1987,4,4)
        self.e_budget.start_date = None

        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,2)),True)
        eq_(self.e_budget.is_active_for_date(datetime.date(1987,4,5)),False)

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

        # If we deliver about the right amount, leave the fraction the same
        fraction = budget_service.calc_braking_fraction(100.0, 110.0, 0.8)

        eq_(fraction, 0.8)


        # If we deliver about the right amount, leave the fraction the same
        fraction = budget_service.calc_braking_fraction(114.0, 110.0, 0.8)

        eq_(fraction, 0.8)










