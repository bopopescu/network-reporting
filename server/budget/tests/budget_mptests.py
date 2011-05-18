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
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache
from budget import models as budgetmodels
from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

class TestBudgetUnitTests(unittest.TestCase):
    
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
                                          bid_strategy="cpc",
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
        eq_(1000,self.expensive_c.budget)
        eq_(1000,self.cheap_c.budget)
        
   
    def mptest_to_memcache_int(self):
        val = 123.00
        same = budget_service._to_memcache_int(budget_service._from_memcache_int(val))
        eq_(val,same)

        val = 1
        same = budget_service._to_memcache_int(budget_service._from_memcache_int(val))
        eq_(val,same)

        val = 15000000
        same = budget_service._to_memcache_int(budget_service._from_memcache_int(val))
        eq_(val,same)
        
    def mptest_timeslice_retrieval(self):
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_manager.timeslice_budget, 100)

    def mptest_memcache_rollunder(self):
        #It does not appear that memcache allows rollunders, TODO: test in devappserver
        memcache.add("thing", 15)
        eq_(memcache.get("thing"),15)
        memcache.decr("thing", 8)
        eq_(memcache.get("thing"),7)
        memcache.decr("thing", 150)
        eq_(memcache.get("thing"),0)

        
    def mptest_basic(self):
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        # But it uses up all the timeslice's money and fails the second    
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 0)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 0)       
                                  
             
    def mptest_basic_cheap(self):
        # We can do the cheap bidding 100 times
        for i in xrange(100):
            eq_(budget_service._apply_if_able(self.cheap_c, 1), True)

        # But it uses up all the timeslice's money and fails the 101st time             
        eq_(budget_service._apply_if_able(self.cheap_c, 1), False)

    def mptest_timeslices_update(self):
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        # But it uses up all the timeslice's money and fails the second             
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 0)       
                                  
        # Then after we advance the timeslice
        budget_service.timeslice_advance(self.expensive_c)
        
        # We now have more budget and can do the bid one more time
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        # But it uses up all the timeslice's money and fails the second             
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 0)
 
    def mptest_timeslices_rollover(self):
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)       

        # Then after we advance the timeslice
        budget_service._advance_all()
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)      
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 198)
        
        for i in xrange(198):
            eq_(budget_service._apply_if_able(self.cheap_c, 1), True)

        # But it uses up all the timeslice's money and fails the 101st time             
        eq_(budget_service._apply_if_able(self.cheap_c, 1), False)
    
    def mptest_multiple_campaigns(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)

        budget_service._advance_all()
        
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 198)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 100)
        
    def budget_sum_is_daily_budget():
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        mem_budget_c = budget_service.remaining_ts_budget(self.cheap_c)
        mem_budget_e = budget_service.remaining_ts_budget(self.expensive_c)
    
    def mptest_multiple_campaigns_advance_twice(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)

        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)

        budget_service._advance_all()
        budget_service._advance_all()
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 298)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 200)

    def mptestremaining_daily_budget(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        # We have moved 100 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),99)
        
        budget_service._advance_all()
        
        
        # We have moved 200 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),199)
        
        budget_service._advance_all()
        budget_service._advance_all()
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c),399)
        
        # We have moved 400 to the current timeslice budget
        
        budget_service._advance_all()
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c),499)

    def mptest_cache_failure_then_spend(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        budget_service._delete_memcache(self.cheap_c)
        
        # Memcache miss -> restart timeslice
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
  
    def mptest_cache_failure_then_spend_multiple_timeslices(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        
        budget_service._advance_all()
        
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)
        
        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 198)

    def mptest_cache_failure_then_apply_expense(self):
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        budget_service._delete_memcache(self.cheap_c)

        # Memcache miss -> restart timeslice
        budget_service.apply_expense(self.cheap_c, 1)
        budget_service.apply_expense(self.cheap_c, 1)
        
        # We lose any apply_expense calls that were queued
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)

    def mptest_cache_failure_then_advance(self):
        
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)

        eq_(budget_manager.timeslice_snapshot, 100)
        eq_(budget_service.remaining_ts_budget(self.cheap_c),99)
        
        budget_service._delete_memcache(self.cheap_c)
        eq_(budget_manager.timeslice_snapshot, 100)
        # Memcache miss -> restart timeslice at last snapshot (100)

        budget_service._advance_all()
        eq_(budget_manager.timeslice_snapshot, 100)
        
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_manager.timeslice_snapshot, 200)
        
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)

    def mptest_cache_failure_then_advance_multiple_timeslices(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all()
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)

        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        budget_service._advance_all()
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 298)
        
    def mptest_budget_logging_basic(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all()
        
        
        slicer = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(slicer.timeslice_snapshot, 199)
        
        last_log = slicer.timeslice_logs.order("-end_date").get()
        eq_(last_log.spending, 1)
        
    def mptest_budget_logging_multiple(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 98)

        budget_service._advance_all()
        

        last_log = budget_service.last_log(self.cheap_c)
        eq_(last_log.spending, 2)    
 
        eq_(budget_service._apply_if_able(self.cheap_c, 10), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 10), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 178)

        budget_service._advance_all()
        

        last_log = budget_service.last_log(self.cheap_c)
        eq_(last_log.spending, 20)    
 
    def mptest_very_expensive(self):
         eq_(budget_service._apply_if_able(self.cheap_c, 10000), False)
         
         eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
         eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)

    def mptestremaining_daily_budget(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)

    def mptest_budget_allatonce(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)
        eq_(budget_service._apply_if_able(self.cheap_c, 600), False)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)
        
        budget_service.daily_advance(self.cheap_c)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)
     
    def mptest_daily_budget_allatonce_cache_miss(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)
        eq_(budget_service._apply_if_able(self.cheap_c, 200), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 200)

        budget_service.daily_advance(self.cheap_c)
        budget_service._delete_memcache(self.cheap_c)
        
        # Fall back to snapshot
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)

    def mptest_daily_budget_allatonce_cache_miss_ts(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)
        eq_(budget_service._apply_if_able(self.cheap_c, 600), False)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)

        budget_service.daily_advance(self.cheap_c)
        budget_service.timeslice_advance(self.cheap_c) # to backup
        budget_service._delete_memcache(self.cheap_c)

        # Fall back to snapshot
        budget_service.daily_advance(self.cheap_c)
        budget_service.timeslice_advance(self.cheap_c) # to backup
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)


    def mptest_daily_logging(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 900), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 100)

        budget_service.daily_advance(self.cheap_c)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 950), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 50)

        budget_service.daily_advance(self.cheap_c)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)

        # Check logs
        
        slicer = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        
        daily_logs = slicer.daily_logs.order("-end_datetime").fetch(2)
          
        eq_(daily_logs[0].remaining_daily_budget, 50)
        eq_(daily_logs[1].remaining_daily_budget, 100)
          
        eq_(daily_logs[0].spending, 950)
        eq_(daily_logs[1].spending, 900)
        
    def mptest_recent_daily_logs(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)

        # We have only one day
        eq_(budget_service.percent_delivered(self.cheap_c),50)

        budget_service.daily_advance(self.cheap_c)
       
        # We have one day at 50, and a new empty one
        eq_(budget_service.percent_delivered(self.cheap_c),25)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)

        # We have two days at 50
        eq_(budget_service.percent_delivered(self.cheap_c),50)

        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 0)

        eq_(budget_service.percent_delivered(self.cheap_c),75)
    
    def mptest_recent_daily_logs_mult(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 900), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 100)
        
        # We have only one day
        eq_(budget_service.percent_delivered(self.cheap_c),90)

        for i in xrange(15):
            budget_service.daily_advance(self.cheap_c)
            eq_(budget_service._apply_if_able(self.cheap_c, 950), True)
            eq_(budget_service.remaining_daily_budget(self.cheap_c), 50)


        # Check logs

        # We use the full 14 days
        eq_(budget_service.percent_delivered(self.cheap_c),95)
   
    def mptest_total_delivered(self):
        # Each campaign has $1000 total budget
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()

        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.total_delivered(self.cheap_c), 500)

        budget_service.daily_advance(self.cheap_c)

        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.total_delivered(self.cheap_c), 500)

        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 0)
        
    def mptest_percent_delivered_dates(self):
        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        eq_(budget_service.percent_delivered(self.cheap_c), 0.0)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500), True)    
        eq_(budget_service.percent_delivered(self.cheap_c), 5.0)

        # The end of the first day
        budget_service.daily_advance(self.cheap_c, date=datetime.date(1987,4,4))
    
    def mptest_percent_delivered_none(self):
         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.cheap_c.budget_strategy = "allatonce"
         self.cheap_c.budget = None
         self.cheap_c.put()

         eq_(budget_service.percent_delivered(self.cheap_c), None)
