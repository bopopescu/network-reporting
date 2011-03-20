########## Set up Django ###########
import sys
import os

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append(os.environ['PWD'])


from advertiser.models import ( Campaign,
                                AdGroup,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )
                                          
from server.ad_server.main import  ( AdHandler,
                                     AdAuction,
                                     AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
#########################################
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from server.ad_server.budget import budget_service
from google.appengine.api import memcache

class TestBudgetIntegration(unittest.TestCase):
    
    def setUp(self):
        # We simplify budget_service for testing purposes
        budget_service.TEST_MODE = True
        budget_service.TIMESLICES = 10 # this means each campaign has 100 dollars per slice
        budget_service.FUDGE_FACTOR = 0.0
        
        # Simulate starting at midnight
        budget_service.reset_all()
        
        #get the campaigns
        self.fetch_campaigns()
    
    def tearDown(self):
        # use the query as an iterable, reset all memcache vals
        for camp in self.camp_query:
            budget_service._delete_memcache(camp)
        pass
    
    def fetch_campaigns(self):
        """Gets the campaigns from the database, updates their remaining budget.
        We should be able to call this at any time without effect"""
         # 100.00 bid with 1000 daily budget -> 1 per TS
        self.camp_query = Campaign.all().filter('name =', 'expensive') 

        self.expensive_c = self.camp_query.get()
         # 1.00 bid with 1000 daily budget -> 100 per TS
        self.camp_query = Campaign.all().filter('name =', 'cheap')
        self.cheap_c = self.camp_query.get()
    
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
        eq_(budget_service.get_budget(self.expensive_c), 0)         
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)
        eq_(budget_service.get_budget(self.expensive_c), 0)       
                                  
             
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
        eq_(budget_service.get_budget(self.expensive_c), 0)       
                                  
        # Then after we advance the timeslice
        budget_service.advance_timeslice(self.expensive_c)
        
        # We now have more budget and can do the bid one more time
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        # But it uses up all the timeslice's money and fails the second             
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)
        eq_(budget_service.get_budget(self.expensive_c), 0)
 
    def mptest_timeslices_rollover(self):
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.get_budget(self.cheap_c), 99)       

        # Then after we advance the timeslice
        budget_service.advance_all()
        self.fetch_campaigns()

        eq_(budget_service.get_budget(self.cheap_c), 199)      
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.get_budget(self.cheap_c), 198)
        
        for i in xrange(198):
            eq_(budget_service._apply_if_able(self.cheap_c, 1), True)

        # But it uses up all the timeslice's money and fails the 101st time             
        eq_(budget_service._apply_if_able(self.cheap_c, 1), False)
    
    def mptest_multiple_campaigns(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)

        budget_service.advance_all()
        self.fetch_campaigns()
        
        eq_(budget_service.get_budget(self.cheap_c), 198)
        eq_(budget_service.get_budget(self.expensive_c), 100)
        
    def budget_sum_is_daily_budget():
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)
        
        mem_budget_c = budget_service.get_budget(self.cheap_c)
        mem_budget_e = budget_service.get_budget(self.expensive_c)
        
        eq_(mem_budget_c + self.cheap_c.remaining_budget, self.cheap_c.budget)
        eq_(mem_budget_c + self.expensive_c.remaining_budget,
            self.expensive_c.budget)
    
    def mptest_multiple_campaigns_advance_twice(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), True)

        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.expensive_c, 100), False)

        budget_service.advance_all()
        budget_service.advance_all()
        self.fetch_campaigns()

        eq_(budget_service.get_budget(self.cheap_c), 298)
        eq_(budget_service.get_budget(self.expensive_c), 200)

    def mptest_remaining_budget(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        # We have moved 100 to the current timeslice budget
        eq_(self.cheap_c.remaining_budget, 900) 
        
        budget_service.advance_all()
        self.fetch_campaigns()
        
        # We have moved 200 to the current timeslice budget
        eq_(self.cheap_c.remaining_budget, 800) 
        
        budget_service.advance_all()
        budget_service.advance_all()
        self.fetch_campaigns()
        
        # We have moved 400 to the current timeslice budget
        eq_(self.cheap_c.remaining_budget, 600) 
        
        budget_service.advance_all()
        self.fetch_campaigns()
        
        
        
        