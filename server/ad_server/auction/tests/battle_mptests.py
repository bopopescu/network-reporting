########## Set up Django ###########
import sys
import os
import datetime

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

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
                                          
from server.ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from server.ad_server.handlers import adhandler
from server.ad_server.handlers.adhandler import AdHandler   

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
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
################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request

from ad_server.auction.battles import (Battle, 
                                       GteeBattle, 
                                       GteeHighBattle,
                                       GteeLowBattle 
                                      )
  
from ad_server.auction.client_context import ClientContext


class TestAdAuction(unittest.TestCase):
    """
    Using the web UI, we have created an ad_unit with the only two 
    competitors being a cheap campaign ($10/ad) and an expensive
    campaign ($100/ad)
    """

    def setUp(self):
        
    
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

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
        self.expensive_c = Campaign(name="expensive",
                                    budget=1000.0,
                                    budget_strategy="allatonce",
                                    campaign_type="gtee")
        self.expensive_c.put()

        self.expensive_adgroup = AdGroup(account=self.account, 
                                          name="expensive",
                                          campaign=self.expensive_c, 
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=100000.0) # 100 per click
        self.expensive_adgroup.put()   

        self.expensive_creative = Creative(account=self.account,
                                ad_group=self.expensive_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear")
        self.expensive_creative.put()

        # Make cheap campaign
        self.cheap_c = Campaign(name="cheap",
                                budget=1000.0,
                                budget_strategy="allatonce",
                                campaign_type="gtee")
        self.cheap_c.put()

        self.cheap_adgroup = AdGroup(account=self.account, 
                              name="cheap",
                              campaign=self.cheap_c, 
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm",
                              bid=10000.0)
        self.cheap_adgroup.put()


        self.cheap_creative = Creative(account=self.account,
                                ad_group=self.cheap_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear")
        self.cheap_creative.put()
    
        
        self.request = fake_request(self.adunit.key())
        self.adunit_id = str(self.adunit.key())
         
        self.user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"

        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)   
        
        self.client_context = ClientContext(adunit=self.adunit,
                	                        keywords=["rocks", "paper"],
                                            country_code=None,
                	                        excluded_adgroup_keys=[],
                	                        raw_udid="awesome_test_udid",
                	                        mopub_id="awesome_test_mopub_id",
                	                        ll=None,
                	                        request_id="random_awesome_request_id",
                	                        now=datetime.datetime.now(),
                	                        user_agent=self.user_agent,       
                	                        experimental=False,
                	                        geo_predicates=["country_name=US","country_name=*"])
   
    def tearDown(self):
        self.testbed.deactivate()

    def mptest_basic(self):
        gtee_battle = GteeBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)            
         
    def mptest_gtee_high_priority(self):   
        self.expensive_c.campaign_type = "gtee_high"
        self.expensive_c.put()  
        
        # Clear the adunit context cache         
        self.refresh_context(self.adunit)

        # for c in self.adunit_context.campaigns:
        #     print c.campaign_priority   

        gtee_battle = GteeHighBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)
    
    def mptest_gtee_low_priority(self):   
        self.expensive_c.campaign_type = "gtee_low"
        self.expensive_c.put()  
    
        # Clear the adunit context cache         
        self.refresh_context(self.adunit)                                  
    
        gtee_battle = GteeLowBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)
                                                      

############### HELPER FUNCTIONS ###########                          
                                           
    def refresh_context(self, adunit):
        """ Refreshes self.adunit_context when it has been changed"""
        AdUnitContextQueryManager.cache_delete_from_adunits(adunit)
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(str(adunit.key()))         
 
def eq_obj(obj1, obj2): 
    """ Convenience func """
    eq_(obj1.key(), obj2.key())      