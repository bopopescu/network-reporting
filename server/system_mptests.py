########## Set up Django ###########
import sys
import os
import datetime
import logging
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from account.models import Account

from publisher.models import App
from publisher.models import Site as AdUnit

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                HtmlCreative,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )

from ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )

from ad_server.handlers.adhandler import AdHandler

############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache
from budget import models as budgetmodels
from budget.models import (Budget,
                           BudgetSliceLog,
                           )
from budget.query_managers import BudgetQueryManager

from google.appengine.ext import testbed
################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request



""" This module is where all of our ad_server system and end-to-end tests can live. """



class TestBudgetEndToEnd(unittest.TestCase):

    def test_mock_budget_advance(self, testing=False, advance_to_datetime = None):
        budget_service._mock_budget_advance(advance_to_datetime, testing)
        self.expensive_c = Campaign.get(self.expensive_c.key())
        self.cheap_c = Campaign.get(self.cheap_c.key())
        self.exp_b = Budget.get(self.exp_b.key())
        self.cheap_b = Budget.get(self.cheap_b.key())

    def test_advance(self, dtetime):
        slice_num = self.test_mock_budget_advance(testing=True, advance_to_datetime = dtetime)
        logging.warning("Advancing....")

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

        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account,
                                     app_key=self.app,
                                     name="Test AdUnit",
                                     format=u'320x50')
        self.adunit.put()

        # Make Expensive Campaign
        self.exp_b = Budget(start_datetime = self.budget_start,
                            delivery_type = 'evenly',
                            static_slice_budget = 100.0,
                            active = True,
                            testing = True)
        self.exp_b.put()

        self.expensive_c = Campaign(name="expensive",
                                    budget_obj=self.exp_b,
                                    campaign_type="gtee")
        self.expensive_c.put()

        self.expensive_adgroup = AdGroup(account=self.account,
                                          name="expensive",
                                          campaign=self.expensive_c,
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=100000.0) # 100 per click
        self.expensive_adgroup.put()



        self.expensive_creative = HtmlCreative(account=self.account,
                                ad_group=self.expensive_adgroup,
                                tracking_url="test-tracking-url",
                                cpc=.03,
                                ad_type="clear")
        self.expensive_creative.put()

        # Make cheap campaign

        self.cheap_b = Budget(start_datetime = self.budget_start,
                            delivery_type = 'evenly',
                            static_slice_budget = 100.0,
                            active = True,
                            testing = True)
        self.cheap_b.put()


        self.cheap_c = Campaign(name="cheap",
                                budget_obj = self.cheap_b,
                                campaign_type="gtee")
        self.cheap_c.put()

        self.cheap_adgroup = AdGroup(account=self.account,
                              name="cheap",
                              campaign=self.cheap_c,
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm",
                              bid=10000.0) # $10 per click
        self.cheap_adgroup.put()


        self.cheap_creative = HtmlCreative(account=self.account,
                                ad_group=self.cheap_adgroup,
                                tracking_url="test-tracking-url",
                                cpc=.03,
                                ad_type="clear")
        self.cheap_creative.put()

        self.switch_adgroups_to_cpm()

        slice_num = self.test_advance(self.budget_start)
        logging.warning("In setup:")
        for b in Budget.all():
            logging.warning("%s" % b)



    def tearDown(self):
        self.testbed.deactivate()

    def update_adgroups(self):
        group_query = AdGroup.all().filter('name =', 'expensive')

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.put()

        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.put()


    def switch_adgroups_to_cpm(self):
        group_query = AdGroup.all().filter('name =', 'expensive')

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.bid_strategy = "cpm"
        e_g.put()

        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.bid_strategy = "cpm"
        c_g.put()


    def update_adgroups(self):
        group_query = AdGroup.all().filter('name =', 'expensive')

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.put()

        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.put()

    def mptest_simple_request(self):
        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "expensive")


    def mptest_two_requests(self):
        # We have enough budget for one expensive ad

        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj), 1200)
        eq_(budget_service.remaining_ts_budget(self.expensive_c.budget_obj), 100)

        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.bid, 100000.0)
        eq_(creative.ad_group.campaign.name, "expensive")

        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj), 1100)
        eq_(budget_service.remaining_ts_budget(self.expensive_c.budget_obj), 0)

        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "cheap")



    def mptest_multiple_requests(self):
        # We have enough budget for one expensive ad

        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj), 1200)
        eq_(budget_service.remaining_ts_budget(self.expensive_c.budget_obj), 100)

        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.bid, 100000.0)
        eq_(creative.ad_group.campaign.name, "expensive")

        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj), 1100)
        eq_(budget_service.remaining_ts_budget(self.expensive_c.budget_obj), 0)

        # We have enough budget for 10 cheap ads
        for i in xrange(10):
            creative = run_auction(self.adunit.key())
            eq_(creative.ad_group.campaign.name, "cheap")

        creative = run_auction(self.adunit.key())
        eq_(creative, None)

    def mptest_multiple_requests_timeslice_advance(self):
        # We have enough budget for one expensive ad
        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "expensive")

        # We use none of our cheap campaign budget

        # Advance all of our campaigns
        self.test_mock_budget_advance(testing=True)


        # We again have enough budget for one expensive ad
        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "expensive")

        # 100/slice, two slices elapsed (Start slice, now) spent 0,
        # so we have budget for 20 cheap creatives
        for i in xrange(20):
            creative = run_auction(self.adunit.key())
            eq_(creative.ad_group.campaign.name, "cheap")

        creative = run_auction(self.adunit.key())
        eq_(creative, None)




    def mptest_allatonce(self):

        logging.warning("In the test:")
        for b in Budget.all():
            logging.warning("%s, %s" % (b,b.key()))

        BudgetQueryManager.prep_update_budget(self.cheap_b, delivery_type = 'allatonce')
        BudgetQueryManager.prep_update_budget(self.exp_b, delivery_type = 'allatonce')
        # Spend budgets out
        while run_auction(self.adunit.key()):
            pass

        # Exec the allatonce change
        self.test_mock_budget_advance(testing=True)

        eq_(budget_service.remaining_daily_budget(self.cheap_c.budget_obj),1100)
        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj),1100)

        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "expensive")


        eq_(budget_service.remaining_daily_budget(self.expensive_c.budget_obj),1000)

        # We have enough budget for 10 expensive ads
        for i in xrange(10):
            creative = run_auction(self.adunit.key())
            eq_(creative.ad_group.campaign.name, "expensive")

        # We now use our cheap campaign budget
        creative = run_auction(self.adunit.key())
        eq_(creative.ad_group.campaign.name, "cheap")






