########## Set up Django ###########
import sys
import os

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append(os.environ['PWD'])


from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
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
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache
from budget import models as budgetmodels
from budget.models import (BudgetSlicer,
                           TimesliceLog,
                           )

################# End to End #################
from ad_server_tests import run_auction
from publisher.models import Site as AdUnit

class TestBudgetUnitTests(unittest.TestCase):
    
    def setUp(self):
        # We simplify the budgetmanger for testing purposes
        budgetmodels.DEFAULT_TIMESLICES = 10 # this means each campaign has 100 dollars per slice
        budgetmodels.DEFAULT_FUDGE_FACTOR = 0.0
        
        self.update_adgroups()
        
        # Get the campaigns and initialize them
        self.fetch_campaigns()
        
        #unpause them and set the appropriate bids
        self.expensive_c.active = True
        self.expensive_c.budget_strategy = "evenly"

        self.expensive_c.put()
        
        self.cheap_c.active = True
        self.cheap_c.budget_strategy = "evenly"

        self.cheap_c.put()
        
    
    def tearDown(self):
        budget_service._flush_all()
  
    def update_adgroups(self):
        group_query = AdGroup.all().filter('name =', 'expensive') 

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.put()

        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.put()
    
    def fetch_campaigns(self):
        """Gets the campaigns from the database, updates their remaining budget.
        We should be able to call this at any time without effect"""
        self.camp_query = Campaign.all().filter('name =', 'expensive') 

        self.expensive_c = self.camp_query.get()
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
        self.fetch_campaigns()

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
        self.fetch_campaigns()
        
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
        self.fetch_campaigns()

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 298)
        eq_(budget_service.remaining_ts_budget(self.expensive_c), 200)

    def mptestremaining_daily_budget(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        # We have moved 100 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),99)
        
        budget_service._advance_all()
        self.fetch_campaigns()
        
        # We have moved 200 to the current timeslice budget
        eq_(budget_service.remaining_ts_budget(self.cheap_c),199)
        
        budget_service._advance_all()
        budget_service._advance_all()
        self.fetch_campaigns()
        eq_(budget_service.remaining_ts_budget(self.cheap_c),399)
        
        # We have moved 400 to the current timeslice budget
        
        budget_service._advance_all()
        self.fetch_campaigns()
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
        self.fetch_campaigns()
        
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)
        
        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 198)

    def mptest_cache_failure_then_apply_expense(self):
        self.fetch_campaigns()
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
        self.fetch_campaigns()
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
        self.fetch_campaigns()
        budget_manager = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(budget_manager.timeslice_snapshot, 200)
        
        
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)

    def mptest_cache_failure_then_advance_multiple_timeslices(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all()
        self.fetch_campaigns()

        eq_(budget_service.remaining_ts_budget(self.cheap_c), 199)

        budget_service._delete_memcache(self.cheap_c)
        # Memcache miss -> restart timeslice at last snapshot (199)
        budget_service._advance_all()
        self.fetch_campaigns()
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 298)
        
    def mptest_budget_logging_basic(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 99)
        
        budget_service._advance_all()
        self.fetch_campaigns()
        
        slicer = BudgetSlicer.get_or_insert_for_campaign(self.cheap_c)
        eq_(slicer.timeslice_snapshot, 199)
        
        last_log = slicer.timeslice_logs.order("-end_date").get()
        eq_(last_log.spending, 1)
        
    def mptest_budget_logging_multiple(self):
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 1), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 98)

        budget_service._advance_all()
        self.fetch_campaigns()

        last_log = budget_service.last_log(self.cheap_c)
        eq_(last_log.spending, 2)    
 
        eq_(budget_service._apply_if_able(self.cheap_c, 10), True)
        eq_(budget_service._apply_if_able(self.cheap_c, 10), True)
        eq_(budget_service.remaining_ts_budget(self.cheap_c), 178)

        budget_service._advance_all()
        self.fetch_campaigns()

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
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1400)
        
        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 800)
     
    def mptest_daily_budget_allatonce_cache_miss(self):
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
        budget_service._delete_memcache(self.cheap_c)
        
        # Fall back to snapshot
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1400)

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 800)

    def mptest_daily_budget_allatonce_cache_miss(self):
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
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 2400)

        eq_(budget_service._apply_if_able(self.cheap_c, 600), True)
        eq_(budget_service.remaining_daily_budget(self.cheap_c), 1800)


class TestBudgetEndToEnd(unittest.TestCase):
    """
    Using the web UI, we have created an ad_unit with the only two 
    competitors being a cheap campaign ($10/ad) and an expensive
    campaign ($100/ad)
    """

    def setUp(self):
        # We simplify budget_service for testing purposes
        budgetmodels.DEFAULT_TIMESLICES = 10 # this means each campaign has 100 dollars per slice
        budgetmodels.DEFAULT_FUDGE_FACTOR = 0.0
        
        self.update_adgroups()
        self.fetch_campaigns()
        
        #unpause them and set the appropriate bids
        self.expensive_c.active = True
        self.expensive_c.budget_strategy = "evenly"

        self.expensive_c.put()
        
        self.cheap_c.active = True
        self.cheap_c.budget_strategy = "evenly"

        self.cheap_c.put()
        self.fetch_adunits()
        self.switch_adgroups_to_cpm()
        
        
   
    def tearDown(self):
        budget_service._flush_all()

    def update_adgroups(self):
        group_query = AdGroup.all().filter('name =', 'expensive') 

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.put()
        
        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.put()

    def switch_adgroups_to_cpc(self):
        group_query = AdGroup.all().filter('name =', 'expensive') 

        e_g = group_query.get()
        e_g.bid = 100000.0
        e_g.bid_strategy = "cpc"
        e_g.put()
        
        group_query = AdGroup.all().filter('name =', 'cheap')
        c_g = group_query.get()
        c_g.bid = 10000.0
        c_g.bid_strategy = "cpc"
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


    def fetch_campaigns(self):
        """Gets the campaigns from the database, updates their remaining budget.
        We should be able to call this at any time without effect"""
        self.camp_query = Campaign.all().filter('name =', 'expensive') 

        self.expensive_c = self.camp_query.get()
        self.camp_query = Campaign.all().filter('name =', 'cheap')
        self.cheap_c = self.camp_query.get()

    def fetch_adunits(self):
        ad_unit_query = AdUnit.all().filter('name =', 'Budget')
        self.budget_ad_unit = ad_unit_query.get()
                
        ad_unit_query = AdUnit.all().filter('name =', 'Fake')
        self.fake_ad_unit = ad_unit_query.get()
        
    def mptest_get_adunit(self):
        eq_(self.budget_ad_unit.name, 'Budget')
        eq_(self.fake_ad_unit.name, 'Fake')
   
    def mptests_adgroups(self):
        self.cheap_c.adgroups[0].bid = 10000.0 # $10 per imp or click
        self.cheap_c.adgroups[0].put()
        self.expensive_c.adgroups[0].bid = 100000.0 # $100 per imp/click
        self.expensive_c.adgroups[0].put()
        eq_(self.cheap_c.adgroups[0].bid, 10000.0)
        eq_(self.expensive_c.adgroups[0].bid, 100000.0)

    
    def mptest_simple_request(self):
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")


    
    def mptest_multiple_requests(self):
        # We have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.bid, 100000.0)
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We have enough budget for 10 cheap ads
        for i in xrange(10):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
        
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative, None)
    
    def mptest_multiple_requests_timeslice_advance(self):
        # We have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We use half our cheap campaign budget
        for i in xrange(5):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        # Advance all of our campaigns
        budget_service._advance_all()
        self.fetch_campaigns()
    
        # We again have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We now have a cheap campaign budget for 15 ads
        for i in xrange(15):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative, None)
    
    def mptest_multiple_requests_timeslice_advance_twice(self):
        # We have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We use half our cheap campaign budget
        for i in xrange(5):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        # Advance all of our campaigns
        budget_service._advance_all()
        budget_service._advance_all()
        self.fetch_campaigns()
    
        # We again have enough budget for two expensive ads
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We now have a cheap campaign budget for 25 ads
        for i in xrange(25):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative, None)
    
    def mptest_multiple_requests_cpc(self):
        self.switch_adgroups_to_cpc()
        
        # We have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We have enough budget for 10 cheap ads
        for i in xrange(10):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative, None)
    
    def mptest_multiple_requests_timeslice_advance_logging(self):
        # We have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We use half our cheap campaign budget
        for i in xrange(5):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        # Advance all of our campaigns
        budget_service._advance_all()
        self.fetch_campaigns()
        
        # We spent 50.0 on cheap_c last timeslice
        last_log = budget_service.last_log(self.cheap_c)
        eq_(last_log.spending, 50)
    
        # We again have enough budget for one expensive ad
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
    
        # We now have a cheap campaign budget for 15 ads
        for i in xrange(15):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "cheap")
    
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative, None)
        
        # Advance all of our campaigns
        budget_service._advance_all()
        self.fetch_campaigns()
        
        # We spent 150.0 on cheap_c last timeslice
        last_log = budget_service.last_log(self.cheap_c)
        eq_(last_log.spending, 150)
    
        # Test the generator function:
        log_generator = budget_service.log_generator(self.cheap_c)
        
        eq_(log_generator[0].spending,150)
        eq_(log_generator[1].spending,50)
    
    def mptest_allatonce(self):
        self.expensive_c.budget_strategy = "allatonce"
        self.expensive_c.put()

        self.cheap_c.budget_strategy = "allatonce"
        self.cheap_c.put()
   
        eq_(self.expensive_c.budget, 1000)
        eq_(budget_service.remaining_daily_budget(self.cheap_c),1000)     
        
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "expensive")
        
        self.fetch_campaigns()
        
        eq_(budget_service.remaining_daily_budget(self.expensive_c),900)
        
        # We have enough budget for 10 expensive ads
        for i in xrange(9):
            creative = run_auction(self.budget_ad_unit.key())
            eq_(creative.ad_group.campaign.name, "expensive")

        # We now use our cheap campaign budget
        creative = run_auction(self.budget_ad_unit.key())
        eq_(creative.ad_group.campaign.name, "cheap")

    