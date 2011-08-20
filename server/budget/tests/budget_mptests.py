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
from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

from budget.query_managers import BudgetSliceLogQueryManager

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
        budget_service.timeslice_advance(self.expensive_c, testing=True)
        
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
        budget_service._advance_all(testing=True)
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 111)      
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 110)
        
        for i in xrange(110):
            eq_(budget_service._apply_if_able(self.cheap_c, 1), True)

        # But it uses up all the timeslice's money and fails the 101st time             
        eq_(budget_service._apply_if_able(self.cheap_c, 1), False)
    
    def mptest_multiple_campaigns(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)

        budget_service._advance_all(testing=True)
        
        
        assert_almost_equal(budget_service.remaining_ts_budget(self.cheap_c), 998/9.,4)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 900/9.)
        
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

        budget_service._advance_all(testing=True)
        budget_service._advance_all(testing=True)
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 998/8.)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 900/8.)

    def mptest_remaining_daily_budget(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        # We have moved 100 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),99)
        
        budget_service._advance_all(testing=True)
        
        
        # We have moved 200 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),199)
        
        budget_service._advance_all(testing=True)
        budget_service._advance_all(testing=True)
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c),399)
        
        # We have moved 400 to the current timeslice budget
        
        budget_service._advance_all(testing=True)
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c),499)



    def mptest_remaining_daily_budget_planned(self):
        """ We have a planned campaign for tomorrow, make sure budget
            is correct """
            
        # The campaign has a $1000 daily budget, and goes for 1 day
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,4)
        self.cheap_c.put()
    
        # Today is datetime.date(1987,4,2)
        
        # After advancing to datetime.date(1987,4,3) we should still have no budget
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,3))
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,3)), False)
        
        # After advancing to datetime.date(1987,4,4) we should have a budget
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        budget_service.timeslice_advance(self.cheap_c, testing=True)
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,4)), True)
        
    def mptest_cache_failure_then_spend(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        budget_service._delete_memcache(self.cheap_c)
        
        # Memcache miss -> restart timeslice
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
  
    def mptest_cache_failure_then_spend_multiple_timeslices(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        
        budget_service._advance_all(testing=True)
        
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 999/9.)
        
        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 999/9.-1)

    def mptest_cache_failure_then_apply_expense(self):
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        budget_service._delete_memcache(self.cheap_c)

        # Memcache miss -> restart timeslice
        budget_service.apply_expense(self.cheap_c, 1)
        budget_service.apply_expense(self.cheap_c, 1)
        
        # New system notices apply_expenses..
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 97)

    def mptest_cache_failure_then_advance(self):
        
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 100)

        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)

        eq_(budget_manager.spent_today, 0)

        budget_service._advance_all(testing=True)
        
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_manager.spent_today, 100)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
        
        budget_service._delete_memcache(self.cheap_c)
                
        # Memcache miss -> restart spending at last snapshot (100)
        budget_service._advance_all(testing=True)
        
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        
        eq_(budget_manager.spent_today, 100)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 111.5)

    def mptest_cache_failure_then_advance_multiple_timeslices(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all(testing=True)
        

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 999/9.)

        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        budget_service._advance_all(testing=True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 999/8.-1)
        
    def mptest_budget_logging_basic(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 100), True)
        budget_service._advance_all(testing=True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all(testing=True)
        
        last_log = BudgetSliceLogQueryManager().get_most_recent(self.cheap_c)
        eq_(last_log.actual_spending, 1)
   
    def mptest_very_expensive(self):
         eq_(budget_service._apply_if_able(self.cheap_c, 10000), False)
         
         eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
         eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)

    def mptest_remaining_daily_budget(self):
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
        budget_service.timeslice_advance(self.cheap_c,testing=True) # to backup
        budget_service._delete_memcache(self.cheap_c)

        # Fall back to snapshot
        budget_service.daily_advance(self.cheap_c)
        budget_service.timeslice_advance(self.cheap_c,testing=True) # to backup
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)


        
    def mptest_get_spending_for_date_range(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
         self.cheap_c.budget_strategy = "allatonce"
         self.cheap_c.start_date = datetime.date(1987,4,4)
         self.cheap_c.end_date = datetime.date(1987,4,4)
         self.cheap_c.put()


         eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)    

         eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)

         # The end of the second day
         budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))

         second_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                    datetime.date(1987,4,4),
                                                    datetime.date(1987,4,4))
         eq_(second_spending, 500)

       
    
    
    def mptest_get_spending_for_date(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
         self.cheap_c.budget_strategy = "allatonce"
         self.cheap_c.start_date = datetime.date(1987,4,4)
         self.cheap_c.end_date = datetime.date(1987,4,4)
         self.cheap_c.put()

         # Today is datetime.date(1987,4,3)
         today = datetime.date(1987,4,3)
         eq_(budget_service._apply_if_able(self.cheap_c, 500, today=today), False)    


         # The end of the first day
         budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))

         eq_(budget_service._apply_if_able(self.cheap_c, 500,today=datetime.date(1987,4,4)), True)    

         eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)

         # The end of the second day
         budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))

         
         second_spending = budget_service._get_spending_for_date(self.cheap_c,
                                                      datetime.date(1987,4,4))
         eq_(second_spending, 500)
     
       
          
    def mptest_get_spending_for_date_range_mult_no_rollover(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,7)
        self.cheap_c.put()
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the first day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,5)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the second day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,6))
        
         
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,6)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the third day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,7))
        
        
        
        first_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,4),
                                                   datetime.date(1987,4,4))
        eq_(first_spending, 500)
        
        second_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,5),
                                                   datetime.date(1987,4,5))
        
                
        third_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,6),
                                                   datetime.date(1987,4,6))
        eq_(third_spending, 500)
        
        total_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,4),
                                                   datetime.date(1987,4,6))
        eq_(total_spending, 1500)
        
        total_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8))
        eq_(total_spending, 1500)

    def mptest_get_spending_for_date_range_mult_plus_today_no_rollover(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,10)
        self.cheap_c.put()
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the first day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,5)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the second day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,6))
        
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,6)), True)    
        
        # Three days have advanced and we have spent 1500 -> 1500 remains
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # The end of the third day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,7))  
        
        # Three days have advanced and we have spent 1500 
        # We have spent 0 today
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,7)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 900)
        
        
        total_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8))
        # 4000 - 2400 = 1600
        eq_(total_spending, 1600)
        
       
    def mptest_percent_delivered_finite(self):
        # The campaign has a $1000 daily budget, and goes for 1 days inclusive -> $1,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,4)
        self.cheap_c.put()

        # Start out at the date 1987/4/4
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)

        eq_(budget_service.percent_delivered(self.cheap_c), 0.0)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)    
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        
        total_spending = budget_service.get_spending_for_date_range(self.cheap_c,
                                                   datetime.date(1987,4,2),
                                                   datetime.date(1987,4,8),
                                                   today=datetime.date(1987,4,4))
        eq_(total_spending, 500)
        
        
        # We have delivered 50.0%
        eq_(budget_service.percent_delivered(self.cheap_c, today=datetime.date(1987,4,4)), 50.0)

        # The end of the first day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))

        # We have still delivered 50.0%
        eq_(budget_service.percent_delivered(self.cheap_c), 50.0)
    
    def mptest_percent_delivered_finite_ten_days(self):
        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        eq_(budget_service.percent_delivered(self.cheap_c, today=datetime.date(1987,4,4)), 0.0)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)    
        
        # We have delivered 5.0%
        eq_(budget_service.percent_delivered(self.cheap_c, today=datetime.date(1987,4,4)), 5.0)

        # The end of the first day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service.percent_delivered(self.cheap_c), 5.0)      

        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,5)), True) 
           
        # We have delivered 15.0%
        eq_(budget_service.percent_delivered(self.cheap_c, today=datetime.date(1987,4,5)), 15.0)
    
        # The end of the second day
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,6))

        # We have still delivered 15.0%
        eq_(budget_service.percent_delivered(self.cheap_c), 15.0)
        
    def mptest_percent_delivered_none(self):
         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.cheap_c.budget_strategy = "allatonce"
         self.cheap_c.budget = None
         self.cheap_c.put()

         eq_(budget_service.percent_delivered(self.cheap_c), None)
         
         
    def mptest_finite_campaign(self):
        
         # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
         self.cheap_c.budget_strategy = "evenly"
         self.cheap_c.start_date = datetime.date(1987,4,4)
         self.cheap_c.end_date = datetime.date(1987,4,13)
         self.cheap_c.put()
         
         eq_(self.cheap_c.finite, True)
       
         eq_(self.expensive_c.finite, False)
         
         
    def mptest_remaining_daily_budget_finite(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
        
        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.cheap_c,testing=True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
    def mptest_remaining_daily_budget_finite_cache_failure_no_rollover(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        # Advance the budget 1 days (and 10 timeslices)
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-2):
            budget_service.timeslice_advance(self.cheap_c,testing=True)

        # 1000 remaining
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,5)), True)
        # We have spent 100 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 900)
        
        # Catastrophic cache failure!!
        memcache.flush_all()
    
        # Should return to the state we had at the last backup (1000)
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,5)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # Another advance, backs up to db
        budget_service.timeslice_advance(self.cheap_c,testing=True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        
        # Catastrophic cache failure again!!!
        memcache.flush_all()
    
        # Should return to the state we had at the last backup (500)
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,5)), True)
        # We have spent 600 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 400)   


    def mptest_timeslices_preplanned(self):
        """ If a campaign is preplanned, it should not build up a timeslice
            budget surplus. Makes sure that preplanned campaigns still have a 
            smooth delivery. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        # Start on 1987/4/3
        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES):
            budget_service.timeslice_advance(self.cheap_c,testing=True)

        # Advance the budget to the second day of the campaign
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))

        # The first two days' budget should be spread across this day. each timeslice is worth $100

        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,5)), False)
        budget_service.timeslice_advance(self.cheap_c,testing=True)
        budget_service.timeslice_advance(self.cheap_c,testing=True)
        
        # We have $125
        eq_(budget_service._apply_if_able(self.cheap_c, 125, today=datetime.date(1987,4,5)), True)
        
        # Now our budget is empty
        eq_(budget_service._apply_if_able(self.cheap_c, 1, today=datetime.date(1987,4,5)), False)


    def mptest_timeslices_underdelivering(self):
        """ We have a campaign that does not deliver for the first half of the
            campaign. The second half should therefore deliver at twice the 
            regular speed. """

        # The campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.put()

        # Advance the budget 1 day (and 10 timeslices)
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.cheap_c,testing=True)

        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)
        # We have spent 500 out of 1000 total
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 500)
        

    def mptest_full_campaign_budget(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
        
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
        
        # Advance the budget 
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        
        # 1000 remaining because the 10K budget is split between the 10 remaining days
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 10000)
        
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        # 1111.11 remaining because the 10K budget is split between the 9 remaining days
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 10000)
    
    def mptest_full_campaign_budget_later_end(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
    
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
    
        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,4)), True)
    
        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 20 days total, 19 remain
        self.cheap_c.end_date = datetime.date(1987,4,23)
        self.cheap_c.put()
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        # ~480 remaining because the 10K budget is split between the 19 remaining days
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 9000.)
     
    def mptest_full_campaign_budget_earlier_end(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
    
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
    
        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,4)), True)
    
        # 9K budget remains, but before the end of the first day we
        # change the end date, now the campaign goes for 5 days total, 4 days remain
        self.cheap_c.end_date = datetime.date(1987,4,8)
        self.cheap_c.put()
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 9000)
        
    def mptest_full_campaign_budget_increase_budget(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
        
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
        
        # Advance the budget and spend the full 1000
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,4)), True)
        
        # 9K budget remains, but before the end of the first day we
        # increase the budget. Now we have 9 days and 18000 more to spend.
        self.cheap_c.full_budget = 19000.
        self.cheap_c.put()
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 18000.)
        
    def mptest_full_campaign_budget_consistent_underdeliver(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now. 
        
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
        
        # Advance the budget and spend 500, twice
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4)), True)
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,5)), True)
        
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,6))
        
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 9000)
        
    def mptest_daily_campaign_increase_budget(self):
        self.cheap_c.budget_type = "daily"
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,6)
        self.cheap_c.put()

        budget_service.daily_advance(self.cheap_c, new_date=self.cheap_c.start_date)
        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 200, today=datetime.date(1987,4,4)), False)

        self.cheap_c.budget = 1200.
        self.cheap_c.put()
        budget_service.update_budget(self.cheap_c, dt=datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.cheap_c, 200, today=datetime.date(1987,4,5)), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,4)), False)
         
    def mptest_full_campaign_change_budget(self):
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.full_budget = 3000.
        self.cheap_c.start_date = datetime.date(1987,4,3)
        self.cheap_c.end_date = datetime.date(1987,4,5)
        self.cheap_c.put()

        budget_service.daily_advance(self.cheap_c, new_date=self.cheap_c.start_date)
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,3)), True)
        
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        
        budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,4))
        self.cheap_c.full_budget = 2000.
        self.cheap_c.put()
        budget_service.update_budget(self.cheap_c, dt=datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.cheap_c, 1000, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 1, today=datetime.date(1987,4,4)), False)
          
    def mptest_full_campaign_change_length(self):
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.full_budget = 3000.
        self.cheap_c.start_date = datetime.date(1987,4,3)
        self.cheap_c.end_date = datetime.date(1987,4,5)
        self.cheap_c.put()

        budget_service.daily_advance(self.cheap_c, new_date=self.cheap_c.start_date)
        eq_(budget_service._apply_if_able(self.cheap_c, 500, today=datetime.date(1987,4,3)), True)

        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))

        self.cheap_c.end_date = datetime.date(1987,4,4)
        self.cheap_c.put()
        budget_service.update_budget(self.cheap_c, dt = datetime.datetime(1987,4,4,0,0,0))

        eq_(budget_service._apply_if_able(self.cheap_c, 2500, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 100, today=datetime.date(1987,4,4)), False)

    def mptest_full_campaign_budget_evenly(self):
        # We have a campaign that was set to begin several days ago 
        # but is only beginning now.
        
        # The cheap_campaign has a $1000 daily budget, and goes for 10 days inclusive -> $10,000
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,13)
        self.cheap_c.budget_type = "full_campaign"
        self.cheap_c.full_budget = 10000.
        self.cheap_c.put()
        
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,4)),True)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,13)),True)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,14)),False)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,3)),False)
        
        # Advance the budget and the ts budgets
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,4))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES-1):
            budget_service.timeslice_advance(self.cheap_c,testing=True)
        
        # 1000 remaining because the 10K budget is split between the 10 remaining days
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1000)
        
        # Advance the budget and the ts budgets
        budget_service.daily_advance(self.cheap_c, new_date=datetime.date(1987,4,5))
        for i in xrange(budgetmodels.DEFAULT_TIMESLICES):
            budget_service.timeslice_advance(self.cheap_c,testing=True)
        
        # 1111.11 remaining because the 10K budget is split between the 9 remaining days
        assert_almost_equal(budget_service.remaining_daily_budget(self.cheap_c), 10000./9, 5)
        
        # We can actually spend all the money, this means the timeslices have 
        # been advanced properly
        eq_(budget_service._apply_if_able(self.cheap_c, 1111.11111, today=datetime.date(1987,4,5)), True)
        
    def mptest_timeslice_changes(self):
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.budget_type = "daily"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = self.cheap_c.start_date
        self.cheap_c.put()
        
        budget_service.update_budget(self.cheap_c, dt = datetime.datetime(1987,4,4,0,0,0))
        
        eq_(budget_service._apply_if_able(self.cheap_c,100, today=datetime.date(1987,4,4)), True)
        
        budget_service.timeslice_advance(self.cheap_c,testing=True)
        self.cheap_c.budget = 3000.
        self.cheap_c.put()
        
        budget_service.update_budget(self.cheap_c, dt = datetime.datetime(1987,4,4,2,30,0))
        
        eq_(budget_service._apply_if_able(self.cheap_c,322.2222, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.cheap_c,1, today=datetime.date(1987,4,4)), False)
    
    def mptest_campaign_starts_midday(self):
        self.cheap_c.budget_strategy = "evenly"
        self.cheap_c.budget_type = "daily"
        self.cheap_c.start_date = datetime.date(1987,4,4)
        self.cheap_c.end_date = datetime.date(1987,4,4)
        self.cheap_c.put()
        
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,4)),True)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,5)),False)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,3)),False)
        
        budget_service.update_budget(self.cheap_c, dt=datetime.datetime(1987,4,4,12,0,0))
        eq_(budget_service._apply_if_able(self.cheap_c,200, today=datetime.date(1987,4,4)), True)
        eq_(budget_service._apply_if_able(self.cheap_c,1, today=datetime.date(1987,4,4)), False)
        
    def mptest_test_activity(self):
        self.cheap_c.budget_type = "daily"
        
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,4)),True)
        
        self.cheap_c.start_date = datetime.date(1987,4,4)
        
        eq_(self.cheap_c.is_active_for_date(datetime.date(1997,4,4)),True)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,3)),False)
        
        
        self.cheap_c.end_date = datetime.date(1987,4,4)
        self.cheap_c.start_date = None
        
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,2)),True)
        eq_(self.cheap_c.is_active_for_date(datetime.date(1987,4,5)),False)
        
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
        
        
        
        
        
        
        
        
        
        