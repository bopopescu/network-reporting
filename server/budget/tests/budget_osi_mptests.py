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
from budget import models as budgetmodels
from budget.models import (Budget,
                           BudgetSliceLog,
                           )
from budget.memcache_budget import remaining_ts_budget

from google.appengine.ext import testbed

ONE_DAY = datetime.timedelta(days=1)
JUST_UNDER_ONE_DAY = datetime.timedelta(minutes=1435)


class TestBudgetOSIUnitTests(unittest.TestCase):

    def test_mock_budget_advance(self, testing=False, advance_to_datetime = None):
        budget_service._mock_budget_advance(advance_to_datetime, testing)
        self.full_c = Campaign.get(self.full_c.key())
        self.cheap_c = Campaign.get(self.cheap_c.key())
        self.full_b = Budget.get(self.full_b.key())
        self.cheap_b = Budget.get(self.cheap_b.key())

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
        self.budget_end = datetime.datetime(2000,1,11,23,59)

        self.budget_arb_start = datetime.datetime(2000,1,10,4,33)
        self.budget_arb_end = datetime.datetime(2000,1,15,14,3)
        # We simplify the budgetmanger for testing purposes

        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit")
        self.adunit.put()

        # Make Expensive Campaign

        self.full_b = Budget(start_datetime = self.budget_start,
                             end_datetime = self.budget_end,
                             delivery_type = 'evenly',
                             static_total_budget = 2400.0,
                             testing=True,
                            active = True,
                             )
        self.full_b.put()

        self.full_c = Campaign(name="full",
                               budget_obj = self.full_b)
        self.full_c.put()


        self.full_adgroup = AdGroup(account=self.account,
                                          campaign=self.full_c,
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=100000.0) # 100 per click
        self.full_adgroup.put()



        self.full_creative = Creative(account=self.account,
                                ad_group=self.full_adgroup,
                                tracking_url="test-tracking-url",
                                cpc=.03)
        self.full_creative.put()

        # Make a cheap campaign with a daily budget
        self.cheap_b = Budget(start_datetime = self.budget_start,
                              delivery_type = 'evenly',
                              static_slice_budget = 100.0,
                              testing = True,
                            active = True,
                              )
        self.cheap_b.put()

        self.cheap_c = Campaign(name="cheap",
                                budget_obj = self.cheap_b,
                                )
        self.cheap_c.put()

        self.cheap_adgroup = AdGroup(account=self.account,
                              campaign=self.cheap_c,
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpc",
                              budget=1000.0,
                              budget_strategy="evenly",
                              bid=10000.0)
        self.cheap_adgroup.put()


        self.cheap_creative = Creative(account=self.account,
                                ad_group=self.cheap_adgroup,
                                tracking_url="test-tracking-url",
                                cpc=.03)
        self.cheap_creative.put()

        # Init both budgets
        slice_num = self.test_advance(self.budget_start)

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_get_most_recent(self):
        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        self.test_mock_budget_advance(testing=True)

        # Each slice has a budget of 100
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        # We only spend 50 on the second one
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.cheap_b, 50), True)

        most_recent = self.cheap_b.most_recent_slice_log

        # The 50 spending one is not complete, therefore 100 was the most recent
        eq_(most_recent.actual_spending, 100)

        # Now the most recent was 100
        self.test_mock_budget_advance(testing=True)
        most_recent = self.cheap_b.most_recent_slice_log
        eq_(most_recent.actual_spending, 50)


    def mptest_query_managers_second_round(self):
        # Each slice has a budget of 100

        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        self.test_mock_budget_advance(testing=True)

        # In the most recent completed timeslice, we spent 100%
        last_budgetslice = self.cheap_b.most_recent_slice_log

        eq_(last_budgetslice.actual_spending, 100)
        eq_(last_budgetslice.desired_spending, 100)


    def mptest_get_osi_uninitialized(self):
        """ The first timeslice that is run, there is no previously initialized
            timeslice, so we have no recording for a desired budget. Because of
            this, we always return True initially. """

        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        # We only spend 50 on the second one
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service._apply_if_able(self.cheap_b, 50), True)

        # In the most recent completed timeslice, we spent 100%
        eq_(budget_service.get_osi(self.cheap_b), True)

        # We only spent 50 on the second one
        self.test_mock_budget_advance(testing=True)

        # In the most recent completed timeslice, we only spent 50%
        eq_(budget_service.get_osi(self.cheap_b), False)

    def mptest_get_osi(self):

        # Each slice has a budget of 100
        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)
        self.test_mock_budget_advance(testing=True)

        # We spend it all this second time
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)
        self.test_mock_budget_advance(testing=True)

        # We only spend 50 on the third one
        eq_(budget_service._apply_if_able(self.cheap_b, 50), True)

        # In the most recent completed timeslice, we spent 100%
        eq_(budget_service.get_osi(self.cheap_b), True)

        # We only spent 50 on the third one
        self.test_mock_budget_advance(testing=True)

        # In the most recent completed timeslice, we only spent 50%
        eq_(budget_service.get_osi(self.cheap_b), False)

    def mptest_get_osi_with_changing_budget(self):

        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)
        self.test_mock_budget_advance(testing=True)

        # Each slice has a budget of 100
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        # We only spend 50 on the second one
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)

        # Double the daily budget right before an advance
        self.cheap_b.set_total_daily_budget(2400.)
        self.cheap_b.put()
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)
        self.test_mock_budget_advance(testing=True)

        # Several slice_logs have advanced, last one has nothing, so false
        eq_(budget_service.get_osi(self.cheap_b), False)
        slice_num = self.test_advance(self.budget_start + ONE_DAY)

        # Now we spend the full 2000
        eq_(budget_service._apply_if_able(self.cheap_b, 200), True)

        self.test_mock_budget_advance(testing=True)

        # In the most recent completed timeslice, we spent 200
        eq_(budget_service.get_osi(self.cheap_b), True)

    def mptest_get_osi_with_weird_budget(self):
        """ When a budget doesn't match perfectly with a timeslice, we want
            the osi to still say it's ok, 95percent is fine. """

        # We do one round to set up the OSI
        eq_(budget_service._apply_if_able(self.cheap_b, 100), True)
        self.test_mock_budget_advance(testing=True)

        # We spend 99
        eq_(budget_service._apply_if_able(self.cheap_b, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_b, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_b, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_b, 2), False)

        self.test_mock_budget_advance(testing=True)

        # We spent the most that we could

        # In the most recent completed timeslice, we spent 99 out of 100
        # This is within 95% so it is ok
        eq_(budget_service.get_osi(self.cheap_b), True)


    def mptest_full_campaign_extended_dates(self):
        """ We change a two day campaign to a four day campaign.
            It should slow down the delivery."""

        eq_(budget_service._apply_if_able(self.full_b, 100), True)

        for i in xrange(9):
            self.test_mock_budget_advance(testing=True)
            eq_(budget_service._apply_if_able(self.full_b, 100), True)

        # 1000$ has been spent and the last timeslice is about to end,
        # the user says that the campaign must last three days.

        self.full_b.end_datetime=datetime.datetime(2000,1,13,23,59)
        self.full_b.put()

        slice_num = self.test_advance(self.budget_start + ONE_DAY)
        slice_num = self.test_advance(self.budget_start + 2*ONE_DAY)
        rem = remaining_ts_budget(self.full_b)

        # The budget should now only have $1000 to spend over 2 days
        eq_(budget_service._apply_if_able(self.full_b, rem), True)
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.get_osi(self.full_b), True)


    def mptest_full_campaign_compressed_dates(self):
        """ We spend a full day's budget as normal, then with one ts left,
            we set the campaign to be one day instead of two"""


        eq_(budget_service._apply_if_able(self.full_b, 100), True)
        for i in xrange(8):
            self.test_mock_budget_advance(testing=True)
            eq_(budget_service._apply_if_able(self.full_b, 100), True)

        # The last timeslice is about to begin, and the user says that
        # the campaign must end tomorrow.
        self.test_mock_budget_advance(testing=True)

        #self.full_b.end_datetime = self.budget_start + JUST_UNDER_ONE_DAY
        self.full_b.end_datetime = self.budget_start + ONE_DAY
        self.full_b.put()

        self.test_mock_budget_advance(testing=True)
        eq_(budget_service.get_osi(self.full_b), False)

        # We have spent 900 out of the $2000 total, we should now be able to spend
        # $1100
        eq_(budget_service._apply_if_able(self.full_b, 1130.76), True)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service.get_osi(self.full_b), True)

        eq_(budget_service._apply_if_able(self.full_b, 10.76), True)
        self.test_mock_budget_advance(testing=True)
        eq_(budget_service.get_osi(self.full_b), False)



