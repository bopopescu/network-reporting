########## Set up Django ###########
import sys
import os
import datetime
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from account.models import Account, NetworkConfig

from publisher.models import App
from publisher.models import Site as AdUnit

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                )             
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )
from ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from ad_server.handlers import adhandler
from ad_server.handlers.adhandler import AdHandler   

from account.query_managers import AccountQueryManager
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache

from google.appengine.ext import testbed
################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request
 
from ad_server.auction.battles import (Battle, 
                                       GteeBattle, 
                                       GteeHighBattle,
                                       GteeLowBattle,
                                       PromoBattle,
                                       MarketplaceBattle,  
                                       NetworkBattle,
                                       BackfillPromoBattle,        
                                      )
  
from ad_server.auction.client_context import ClientContext   

from advertiser.models import (DummyServerSideSuccessCreative, 
                               DummyServerSideFailureCreative,
                               MarketplaceCreative,   
                              )   
from ad_server.optimizer import optimizer

optimizer.SAMPLING_FRACTION = 0 # Don't sample during tests

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

        # Set up app network config.
        self.network_config = NetworkConfig(account=self.account)
        AccountQueryManager.update_config_and_put(self.account, self.network_config)

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
                                ad_type="clear")
        self.cheap_creative.put()
                    
                    
                    
         
        self.dummy_network_c = Campaign(name="dummy_network",
                                        campaign_type="network") 
                                       
        self.dummy_network_c.put()

        self.dummy_adgroup = AdGroup(account=self.account, 
                              name="dummy_network",
                              campaign=self.dummy_network_c, 
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm", 
                              bid=100000.0, # 100 per click  
                              network_type="dummy") # dummy networks go to the DummyServerSide 
                              
        self.dummy_adgroup.put()             
                    
        # We don't build our dummy creative here, but rather in individual tests                              
    
        
        self.request = fake_request(self.adunit.key())
        self.adunit_id = str(self.adunit.key())
         
        self.user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"  
        
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

    def _client_context_mk_dict(self):   
        """ REMOVED (append mptest to function def to add back)"""
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)
        mk_dict = self.client_context.make_marketplace_dict(self.adunit_context)
        expected_dict = {'price_floor': 0.25,
                         'app_name': 'Test App',
                         'mopub_id': 'awesome_test_udid',
                         'app_id': 'agltb3B1Yi1pbmNyCQsSA0FwcBgDDA',
                         'height': 50,
                         'paid': 0,
                         'keywords': ['rocks', 'paper'],
                         'pub_rev_share': 0.90000000000000002,
                         'adunit_id': 'agltb3B1Yi1pbmNyCgsSBFNpdGUYBAw',
                         'pub_id': 'agltb3B1Yi1pbmNyDQsSB0FjY291bnQYAgw',
                         'format': '320x50',
                         'width': 320,
                         'user_agent': 'Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us)'\
                             ' AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10'
                         }
        eq_(mk_dict, expected_dict)

    def mptest_client_context_from_request(self):
        """stub of a test. from_request currently just returns an empty client_context"""
        client_context_1 = ClientContext.from_request(self.request)
        client_context_2 = ClientContext()
        eq_(client_context_1, client_context_2)
        
    def mtest_basic(self): 
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id) 
        gtee_battle = GteeBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)            
         
    def mptest_gtee_high_priority(self):         
        self.expensive_c.campaign_type = "gtee_high"
        self.expensive_c.put()  
        
        # Clear the adunit context cache         
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)


        gtee_battle = GteeHighBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)
    
    def mptest_gtee_low_priority(self):   
        self.expensive_c.campaign_type = "gtee_low"
        self.expensive_c.put()  
    
        # Clear the adunit context cache         
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)                                 
    
        gtee_battle = GteeLowBattle(self.client_context, self.adunit_context)
        creative = gtee_battle.run() 
        eq_obj(creative, self.expensive_creative)
        
        
    def mptest_network_basic(self):                                                        
        self.dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear") 

        self.dummy_network_creative.put()
               
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)   
    
        network_battle = NetworkBattle(self.client_context, self.adunit_context)
        creative = network_battle.run() 
        eq_obj(creative, self.dummy_network_creative)   
        
        eq_(creative.html_data, "<html> FAKE RESPONSE </html>")     
        
        
    def mptest_network_min_cpm_success(self):   
        """ We can add in a minimum cpm, do this and let it pass """
                                                             
        self.dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear") 

        self.dummy_network_creative.put()   
        
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)         
                                                                                 
        # ecpm if 100000
        eq_(optimizer.get_ecpm(self.adunit, self.expensive_creative), 100000)
         
        # We make the limit min below the ecpm
        network_battle = NetworkBattle(self.client_context,
                                       self.adunit_context,
                                       min_cpm=0.0)
        creative = network_battle.run() 
        eq_obj(creative, self.dummy_network_creative)   

        eq_(creative.html_data, "<html> FAKE RESPONSE </html>") 
    
    def mptest_network_min_cpm_failure(self):   
        """ We can add in a minimum cpm, do this and make it fail """

        self.dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear") 

        self.dummy_network_creative.put()   

        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)         

        # ecpm if 100000
        eq_(optimizer.get_ecpm(self.adunit, self.expensive_creative), 100000)

        # We make the min_cpm more than the ecpm
        network_battle = NetworkBattle(self.client_context,
                                       self.adunit_context,
                                       min_cpm=200000)
        creative = network_battle.run() 
        eq_(creative, None)                
        
    def mptest_network_failure(self):      
        
        self.dummy_network_creative = DummyServerSideFailureCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear") 

        self.dummy_network_creative.put()
        
        # Clear the adunit context cache         
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id)                 
          

        network_battle = NetworkBattle(self.client_context, self.adunit_context)
        creative = network_battle.run()  

        eq_(creative, None) 

    
        
    def mptest_network_multiple(self):
        
        self.dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                ad_type="clear") 
        
        self.dummy_network_creative.put()    
        
        self.cheaper_dummy_network_c = Campaign(name="cheaper_dummy_network",
                                        campaign_type="network")
        self.cheaper_dummy_network_c.put()
        
        self.cheaper_dummy_adgroup = AdGroup(account=self.account, 
                              name="cheaper_dummy_network",
                              campaign=self.cheaper_dummy_network_c, 
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm", 
                              bid=50000.0, # 50 per click, the other campaign has 100 per click  
                              network_type="dummy") # dummy networks go to the DummyServerSide 
        
        self.cheaper_dummy_adgroup.put()             
        
        
        self.cheaper_dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.cheaper_dummy_adgroup,
                                tracking_url="test-tracking-url",  
                                ad_type="clear")
        self.cheaper_dummy_network_creative.put()
        
        # Clear the adunit context cache                                   
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id) 
        
        # Both succeed, but the more expensive one wins over the cheaper
        
        network_battle = NetworkBattle(self.client_context, self.adunit_context)
        creative = network_battle.run() 
        eq_obj(creative, self.dummy_network_creative)   

        eq_(creative.html_data, "<html> FAKE RESPONSE </html>")
        
    def mptest_network_fallback(self):

        self.dummy_network_creative = DummyServerSideFailureCreative(account=self.account,
                                ad_group=self.dummy_adgroup,
                                tracking_url="test-tracking-url", 
                                ad_type="clear") 

        self.dummy_network_creative.put()    

        self.cheaper_dummy_network_c = Campaign(name="cheaper_dummy_network",
                                        campaign_type="network")
        self.cheaper_dummy_network_c.put()

        self.cheaper_dummy_adgroup = AdGroup(account=self.account, 
                              name="cheaper_dummy_network",
                              campaign=self.cheaper_dummy_network_c, 
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm", 
                              bid=50000.0, # 50 per click, the other campaign has 100 per click  
                              network_type="dummy") # dummy networks go to the DummyServerSide 

        self.cheaper_dummy_adgroup.put()             


        self.cheaper_dummy_network_creative = DummyServerSideSuccessCreative(account=self.account,
                                ad_group=self.cheaper_dummy_adgroup,
                                tracking_url="test-tracking-url",  
                                ad_type="clear")
        self.cheaper_dummy_network_creative.put()

        # Clear the adunit context cache                                   
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id) 

        # Both succeed, and the more expensive one wins over the cheaper.  
        # However, due to the failure of the more expensive, we fall back to the cheaper.

        network_battle = NetworkBattle(self.client_context, self.adunit_context)
        creative = network_battle.run() 
        eq_obj(creative, self.cheaper_dummy_network_creative)   

        eq_(creative.html_data, "<html> FAKE RESPONSE </html>")


    def mptest_marketplace(self):   
        self.dummy_marketplace_c = Campaign(name="dummy_network",
                                        campaign_type="marketplace") 
                                       
        self.dummy_marketplace_c.put()

        self.dummy_marketplace_adgroup = AdGroup(account=self.account,    
                              campaign=self.dummy_marketplace_c, 
                              site_keys=[self.adunit.key()],
                              bid_strategy="cpm", 
                              bid=100000.0, # 100 per click  
                              network_type="dummy") # dummy networks go to the DummyServerSide 
                              
        self.dummy_marketplace_adgroup.put()
        
        self.dummy_marketplace_creative = MarketplaceCreative(account=self.account,
                                ad_group=self.dummy_marketplace_adgroup)  
                                
        self.dummy_marketplace_creative.put()
        
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit_id) 

        test_html = '<html>blah....</html>'
        content = '{"xhtml_real": "%s", "revenue": 10000.50}' % test_html
        marketplace_battle = MarketplaceBattle(self.client_context, self.adunit_context, [1,2,3,4])
        creative = marketplace_battle._process_marketplace_response(content, self.dummy_marketplace_creative)
        # creative = marketplace_battle.run() 
        eq_(creative.html_data, test_html)                                                



############### HELPER FUNCTIONS ###########                          
                                           
    def refresh_context(self, adunit):
        """ Refreshes self.adunit_context when it has been changed"""
        AdUnitContextQueryManager.cache_delete_from_adunits(adunit)
        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(str(adunit.key()))         
 
def eq_obj(obj1, obj2): 
    """ Convenience func """
    eq_(obj1.key(), obj2.key())      
