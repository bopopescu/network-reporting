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



# We simplify budget_service for testing purposes
budget_service.TEST_MODE = True
budget_service.TIMESLICES = 10 # this means each campaign has 100 dollars per slice
budget_service.FUDGE_FACTOR = 0.0

class TestBudgetIntegration(unittest.TestCase):
    
    def setUp(self):
        query = Campaign.all().filter('name =', 'expensive') # 100.00 bid with 1000 budget
        self.expensive_c = query.get()
        query = Campaign.all().filter('name =', 'cheap') # 1.00 bid with 1000 budget
        self.cheap_c = query.get()
    
        self.expensive_a = self.expensive_c.adgroups[0]
        self.cheap_a = self.cheap_c.adgroups[0]
    
    def mptest_load_campaigns(self):
        eq_(1000,self.expensive_c.budget)
        eq_(1000,self.cheap_c.budget)

    def mptest_load_adgroups(self):
        eq_(1000,self.expensive_a.budget)
        eq_(1000,self.cheap_a.budget)
        
    def mptest_bids(self):
        eq_(100,self.expensive_a.bid)
        eq_(1,self.cheap_a.bid)
        
    def mptest_basic(self):
        # We can do the bid one time
        eq_(budget_service._apply_if_able(self.expensive_a), True)
        
        # But it uses up all the timeslice's money and fails the second             
        eq_(budget_service._apply_if_able(self.expensive_a), False)
                                  
             
    def mptest_basic_cheap(self):
        # We can do the cheap bidding 100 times
        for i in xrange(100):
            eq_(budget_service._apply_if_able(self.cheap_a), True)

        # But it uses up all the timeslice's money and fails the 101st time             
        eq_(budget_service._apply_if_able(self.cheap_a), False)

    def mptest_rollover(self):
         pass
             
                      
                              
