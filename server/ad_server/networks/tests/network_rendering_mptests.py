import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from ad_server.networks.rendering import CreativeRenderer
import unittest

from account.models import Account 
from publisher.models import App, AdUnit 
from advertiser.models import Creative, Campaign, AdGroup 

from publisher.query_managers import AdUnitContextQueryManager                                

from google.appengine.ext import testbed
                                                     
from google.appengine.ext.webapp import Response

from google.appengine.api import urlfetch   

from common.utils.system_test_framework import run_auction, fake_request  
    
from nose.tools import eq_    

class RenderingTests(unittest.TestCase):
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
                               
        self.campaign = Campaign(name="Test Campaign")
        self.campaign.put()                  
                            
        self.app = App(account=self.account, name="Test App")
        self.app.put()
        
        self.adunit = AdUnit(account=self.account, 
                             app_key=self.app, 
                             name="Test AdUnit",
                             format="320x50")
        self.adunit.put()           
        
        self.adgroup = AdGroup(account=self.account, 
                               campaign=self.campaign, 
                               site_keys=[self.adunit.key()],
                               bid_strategy="cpc",
                               bid=100.0)
        self.adgroup.put()
         
        self.creative = Creative(account=self.account,
                                 ad_group=self.adgroup,
                                 tracking_url="test-tracking-url")
        self.creative.put()

        
        self.host = "app.mopub.com"
        self.url = """app.mopub.com/m/ad?test_url"""
          
        self.keywords = ["awesome","stuff"]
        
        self.version_number = 2 # Not sure what this is used for
        
        self.track_url = "test_track_url"
        
        self.on_fail_exclude_adgroups = ["test_on_fail_adgroup1", "test_on_fail_adgroup2"]
        

        self.request = fake_request(self.adunit.key())
        adunit_id = str(self.adunit.key())

        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)      

    def tearDown(self):
        self.testbed.deactivate()
    
    def mptest_admob_rendering(self):
        """ For now just test the renderer. Next test headers too. """
        
        self.creative.ad_type = "admob"       
             
                          
        response = Response() # We can use a vanilla response, as we don't use anything from it
        rendered_creative = CreativeRenderer.render(response,   
                                       creative=self.creative,
                                       adunit=self.adunit, 
                                       keywords=self.keywords, 
                                       request_host=self.host, # Needed for serving static files
                                       request_url=self.url, # Needed for onfail urls          
                                       version_number=self.version_number,
                                       track_url=self.track_url,   
                                       on_fail_exclude_adgroups=self.on_fail_exclude_adgroups,
                                       random_val="0932jfios")   
                                       
        # Used to initialize admob_example
        
        # with open('ad_server/networks/tests/admob.example', 'w') as f:   
        #     f.write(rendered_creative)        
        
        with open('ad_server/networks/tests/admob.example', 'r') as f:   
            example_creative = f.read()
                                       
                                       
        eq_(rendered_creative, example_creative)