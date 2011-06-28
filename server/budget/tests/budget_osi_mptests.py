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
from budget.models import (Budget,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

from budget.query_managers import BudgetSliceLogQueryManager


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
        self.expensive_c = Campaign(name="expensive",
                                    budget=1000.0,
                                    budget_strategy="evenly")
        self.expensive_c.put()

        self.expensive_adgroup = AdGroup(account=self.account, 
                                          campaign=self.expensive_c, 
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=100000.0) # 100 per click
        self.expensive_adgroup.put()
        
        

        self.expensive_creative = Creative(account=self.account,
                                ad_group=self.expensive_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03)
        self.expensive_creative.put()
        
        # Make cheap campaign
        self.cheap_c = Campaign(name="expensive",
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
        budget_service.timeslice_advance(self.cheap_c)
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
        
        # We only spend 50 on the second one
        budget_service.timeslice_advance(self.cheap_c)
        eq_(budget_service._apply_if_able(self.cheap_c, 50), True)
        
        most_recent = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
        
        # The 50 spending one is not complete, therefore 100 was the most recent
        eq_(most_recent.spending, 100)
        
        # Now the most recent was 100
        budget_service.timeslice_advance(self.cheap_c)
        most_recent = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
          
          
    def mptest_get_osi(self):

        # Each slice has a budget of 100
        budget_service.timeslice_advance(self.cheap_c)
        
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

        # In the last timeslice, we spent 100%
        eq_(budget_service.get_osi(self.cheap_c), True)

        # Now in this new one, we only spent 100 total of the 200 available
        budget_service.timeslice_advance(self.cheap_c)

        # In the most recent completed timeslice, we only spent 50%
        eq_(budget_service.get_osi(self.cheap_c), False)

        # Now we spend the full 200
        eq_(budget_service._apply_if_able(self.cheap_c, 200), True)

        budget_service.timeslice_advance(self.cheap_c)

        # In the most recent completed timeslice, we spent 200
        eq_(budget_service.get_osi(self.cheap_c), True)

    def mptest_get_osi_with_weird_budget(self):
        """ When a budget doesn't match perfectly with a timeslice, we want
            the osi to still say it's ok"""
            
            
        self.cheap_adgroup.bid=30.0
        self.cheap_adgroup.put()                    
               
               
        eq_(self.cheap_adgroup.individual_cost, 30.)
        
        # We spend 90
        eq_(budget_service._apply_if_able(self.cheap_c, 30), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 30), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 30), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 30), False)                      
                             
        budget_service.timeslice_advance(self.cheap_c)

        # We spent the most that we could

        # In the most recent completed timeslice, we spent 200
        eq_(budget_service.get_osi(self.cheap_c), True)



    def mptest_temp(self):
        log = BudgetSliceLog()
        eq_(log.actual_spending, None)