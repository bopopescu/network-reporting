import os
import sys

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
import budget
from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

from budget.query_managers import BudgetSliceLogQueryManager

budget.models.DEFAULT_FUDGE_FACTOR = 0.0


class TestBudgetOSIUnitTests(unittest.TestCase):
    
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        
        # We simplify the budgetmanger for testing purposes
        budgetmodels.DEFAULT_TIMESLICES = 10 # this means each campaign has 100 dollars per slice
        budgetmodels.DEFAULT_FUDGE_FACTOR = 0.0
        
        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit")
        self.adunit.put()

        # Make Expensive Campaign
        
        # Full c is a campaign that goes for 2 days total and spreads $2000
        # Evenly over those two days.
        
        self.start_date = datetime.date(1987,4,4)
        self.end_date = datetime.date(1987,4,5)
        self.full_c = Campaign(name="full",
                               full_budget=2000.0,
                               budget_type="full_campaign",
                               start_date=self.start_date,
                               end_date=self.end_date,
                               budget_strategy="evenly")
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
        self.cheap_c = Campaign(name="cheap",
                                budget=1000.0,
                                budget_strategy="evenly")
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
        
        
    
    def tearDown(self):
        self.testbed.deactivate()

    def mptest_get_most_recent(self):
        
        # Each slice has a budget of 100
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
        
        # We only spend 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        eq_(budget_service._apply_if_able(self.cheap_c, 50), True)
        
        most_recent = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
        
        # The 50 spending one is not complete, therefore 100 was the most recent
        eq_(most_recent.actual_spending, 100)
        
        # Now the most recent was 100
        budget_service.timeslice_advance(self.cheap_c)
        most_recent = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
          
          
    def mptest_query_managers(self):
        # Each slice has a budget of 100
        
        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)

        # We only spend 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        # eq_(budget_service._apply_if_able(self.cheap_c, 50), True)
        
        # In the most recent completed timeslice, we spent 100%
        last_budgetslice = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
        
        eq_(last_budgetslice.actual_spending, 100)
        eq_(last_budgetslice.desired_spending, 100)
        
    
    def mptest_get_osi(self):
    
        # Each slice has a budget of 100
        
        # We spend it all this first time
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
    
        # We only spend 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        eq_(budget_service._apply_if_able(self.cheap_c, 50), True)
        
        # In the most recent completed timeslice, we spent 100%
        eq_(budget_service.get_osi(self.cheap_c), True)
    
        # We only spent 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        
        # In the most recent completed timeslice, we only spent 50%
        eq_(budget_service.get_osi(self.cheap_c), False)
    
    def mptest_get_osi_with_changing_budget(self):
    
        # Each slice has a budget of 100
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
    
        # We only spend 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
        
        # Double the daily budget right before an advance
        self.cheap_c.budget = 2000.
        self.cheap_c.put()
        budget_service.update_budget(self.cheap_c, dt = datetime.datetime(1987,4,4,2,45,0))
        
        # In the last timeslice, we spent 100%
        eq_(budget_service.get_osi(self.cheap_c), True)
    
        # Now in this new one, we have 1800/8 = $225 available
        budget_service.timeslice_advance(self.cheap_c)
    
        # In the most recent completed timeslice, we spent what we wanted
        eq_(budget_service.get_osi(self.cheap_c), False)
    
        # Now we spend the full 225
        eq_(budget_service._apply_if_able(self.cheap_c, 225), True)
    
        budget_service.timeslice_advance(self.cheap_c)
    
        # In the most recent completed timeslice, we spent 225
        eq_(budget_service.get_osi(self.cheap_c), True)
    
    def mptest_get_osi_with_weird_budget(self):
        """ When a budget doesn't match perfectly with a timeslice, we want
            the osi to still say it's ok, 95percent is fine. """

        # We spend 99
        eq_(budget_service._apply_if_able(self.cheap_c, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 33), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 2), False)                      
                             
        budget_service.timeslice_advance(self.cheap_c)
    
        # We spent the most that we could
    
        # In the most recent completed timeslice, we spent 99 out of 100
        # This is within 95% so it is ok
        eq_(budget_service.get_osi(self.cheap_c), True)
        
        
        
    
    
    def mptest_full_campaign_extended_dates(self):
        """ We change a two day campaign to a four day campaign. 
            It should slow down the delivery."""
    
        eq_(budget_service._apply_if_able(self.full_c, 100), True)
        for i in xrange(9):
            budget_service.timeslice_advance(self.full_c)
            eq_(budget_service._apply_if_able(self.full_c, 100), True)
    
        # 1000$ has been spent and the last timeslice is about to end, 
        # the user says that the campaign must last three days.
    
        new_end_date = datetime.date(1987,4,6)
        self.full_c.end_date=new_end_date
        self.full_c.put()
        dt = datetime.datetime(1987,4,4,23,0,0)
        budget_service.update_budget(self.full_c, dt)
    
        eq_(self.full_c.budget, 2000/3.)

        budget_service.daily_advance(self.full_c, datetime.date(1987,4,5))
        budget_service.timeslice_advance(self.full_c)
        
        eq_(self.full_c.budget, 500)
        
        # The budget should now only have $1000 to spend over 2 days
        eq_(budget_service._apply_if_able(self.full_c, 50), True)
        eq_(budget_service._apply_if_able(self.full_c, 1), False)
        budget_service.timeslice_advance(self.full_c)
        
        eq_(budget_service.get_osi(self.full_c), True)
    
        
    def mptest_full_campaign_compressed_dates(self):
        """ We spend a full day's budget as normal, then with one ts left, 
            we set the campaign to be one day instead of two"""
            
        
        eq_(budget_service._apply_if_able(self.full_c, 100), True)
        for i in xrange(8):
            budget_service.timeslice_advance(self.full_c)
            eq_(budget_service._apply_if_able(self.full_c, 100), True)
        
        # The last timeslice is about to begin, and the user says that 
        # the campaign must end tomorrow.
        budget_service.timeslice_advance(self.full_c)
        
        today = self.start_date
        new_end_date = datetime.date(1987,4,4)
        self.full_c.end_date=new_end_date
        self.full_c.put()
        
        budget_service.update_budget(self.full_c, datetime.datetime(1987,4,4,23,40,0))
        
        # We have spent 900 out of the $2000 total, we should now be able to spend
        # $1100
        eq_(budget_service._apply_if_able(self.full_c, 1100), True)
        
        
        