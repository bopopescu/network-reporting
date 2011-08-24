from __future__ import with_statement
import os
import sys      
import datetime

sys.path.append(os.environ['PWD'])
import common.utils.test.setup
 
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
from common.utils import simplejson

from advertiser.models import (AdMobCreative,
                               AdSenseCreative,
                               HtmlCreative,     
                               ImageCreative,
                               TextAndTileCreative, 
                               TextCreative
                               )

from ad_server.renderers.creative_renderer import BaseCreativeRenderer
from ad_server.renderers.admob import AdMobRenderer   
from ad_server.renderers.text_and_tile import TextAndTileRenderer    
from ad_server.renderers.adsense import AdSenseRenderer
                                                             
 
from ad_server.renderers.header_context import HeaderContext

# RENDERERS = {
#     "admob": AdMobRenderer,
#     "adsense":AdSenseRenderer, 
#     "clear":BaseCreativeRenderer, 
#     "html":BaseCreativeRenderer,
#     "html_full":BaseCreativeRenderer, 
#     "iAd":BaseCreativeRenderer, 
#     "image":BaseCreativeRenderer,
#     "text":BaseCreativeRenderer, 
#     "text_icon":TextAndTileRenderer, 
#     "admob_native":BaseCreativeRenderer,
#     "custom_native":BaseCreativeRenderer, 
#     "millennial_native":BaseCreativeRenderer,
# } 

class RenderingTestBase(object):
    """ This does not inherit from TestCase because we use Nose's generator function with it.
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

        
        self.host = "app.mopub.com"
        self.url = """app.mopub.com/m/ad?test_url"""
          
        self.keywords = ["awesome","stuff"]
        
        self.version_number = 2 # Not sure what this is used for
        
        self.track_url = "test_track_url"
        
        self.on_fail_exclude_adgroups = ["test_on_fail_adgroup1", "test_on_fail_adgroup2"]
        

        self.request = fake_request(self.adunit.key())
        adunit_id = str(self.adunit.key())

        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)      
        
        self.dt = datetime.datetime(1955,5,5,5,5)

    def tearDown(self):
        self.testbed.deactivate()
   
    def render_320x50_creative(self, network_type):
        """ For now just test the renderer. Next test headers too.
            Uses a default value for html_data. """
        self.adunit = AdUnit(account=self.account, 
                             app_key=self.app, 
                             name="Test AdUnit",
                             format="320x50")
        self.adunit.put()
        self.adgroup.network_type = network_type  
        self.adgroup.put()

        self.creative = self.adgroup.default_creative()   
        self.creative.html_data = "fake data" # TODO: Use the actual serverside methods to build this 

        self.creative.put()    
        
        self._compare_rendering_with_examples(network_type, suffix="")  
        
        
        
    def render_full_creative(self, network_type):
        """ Tests both the rendering of the creative payload 
            Uses a default value for html_data. """
        self.adunit = AdUnit(account=self.account, 
                     app_key=self.app, 
                     name="Test AdUnit",
                     format="full")
        self.adunit.put()
        self.adgroup.network_type = network_type  
        self.adgroup.put()

        self.creative = self.adgroup.default_creative()   
        self.creative.html_data = "fake data" # TODO: Use the actual serverside methods to build this 

        self.creative.put() 
        
        self._compare_rendering_with_examples(network_type, suffix="_full")
        
    def _compare_rendering_with_examples(self, name, suffix="", reset_example=False):
        """ For now just test the renderer. Next test headers too.
            Uses a default value for html_data. """
                                                                                                              
        rendered_creative, header_context = self.creative.Renderer.render(  
                                       creative=self.creative,
                                       now=self.dt,
                                       adunit=self.adunit, 
                                       keywords=self.keywords, 
                                       request_host=self.host, # Needed for serving static files
                                       request_url=self.url, # Needed for onfail urls          
                                       version_number=self.version_number,
                                       track_url=self.track_url,   
                                       on_fail_exclude_adgroups=self.on_fail_exclude_adgroups,
                                       random_val="0932jfios")   
                                       
   

        if reset_example:
            with open('ad_server/renderers/tests/example_renderings/%s%s.rendering' % (name, suffix), 'w') as f:   
                f.write(rendered_creative)         

        with open('ad_server/renderers/tests/example_renderings/%s%s.rendering' % (name, suffix), 'r') as f:   
            example_creative = f.read()   
            
                
        # Used to initialize header examples
       
        if reset_example:
            with open('ad_server/renderers/tests/example_renderings/%s%s.headers' % (name, suffix), 'w') as f: 
                header_json = header_context.to_json() # We serialize the headers    
                f.write(header_json)         

        with open('ad_server/renderers/tests/example_renderings/%s%s.headers' % (name, suffix), 'r') as f:   
            example_headers_string = f.read()
            example_headers = HeaderContext.from_json(unicode(example_headers_string))
        
        print "running file name: %s" % name
        eq_(header_context, example_headers)             
        
         
                    
      
             
class RenderingTests(RenderingTestBase, unittest.TestCase):  
    """ Inherits that setUp and tearDown methods from RenderingTestBase. """  


    # image, text and text_icon adtypes are not tested as defaults
    def mptest_image_adtype(self):
        """ Make a one-off test for image creatives. """
        self.creative = ImageCreative(name="image dummy",
                                      image_blob="blobby",
                                      ad_type="image", 
                                      format="320x50", 
                                      format_predicates=["format=320x50"],
                                      ad_group=self.adgroup)

        self.creative.image_width = 320
        self.creative.image_height = 50
        self.creative.put()    

        self._compare_rendering_with_examples("image_adtype", suffix="")#, reset_example=False)  

    def mptest_text_adtype(self):
        """ Make a one-off test for image creatives. """
        self.creative = TextCreative(name="image dummy",
                                            headline="HEADLINE!!", 
                                            line1="Sweet line",
                                            line2="Awesome line",
                                            ad_type="text", 
                                            format="320x50", 
                                            format_predicates=["format=320x50"],
                                            ad_group=self.adgroup)
        self.creative.put()    

        self._compare_rendering_with_examples("text_adtype", suffix="")#, reset_example=False)  


    def mptest_text_icon_adtype(self):
        """ Make a one-off test for image creatives. """
        self.creative = TextAndTileCreative(name="image dummy",
                                            image_blob="blobby", 
                                            line1="Sweet line",
                                            line2="Awesome line",
                                            ad_type="text_icon", 
                                            format="320x50", 
                                            format_predicates=["format=320x50"],
                                            ad_group=self.adgroup) 
                                            
                                                                                    
        self.creative.put()         
        self._compare_rendering_with_examples("text_icon_adtype", suffix="")#), reset_example=False)

##### TEST GENERATORS ######     

network_names = ("adsense",
                 "brightroll",
                 "jumptap",
                 "ejam",
                 "chartboost",
                 "millennial",
                 "inmobi",
                 "greystripe",
                 "appnexus",
                 "custom_native",
                 "custom",
                 "admob_native",
                 "millennial_native",
                 "iAd"
                 )    


                                                         
def mptest_full_network_generator():
    """ Uses Nose's built in generator system to run multiple tests.
        Tests each of the network's default creatives, """
    test = RenderingTestBase()  
    
    for network_name in network_names:
        test.setUp()                 
        yield test.render_full_creative, network_name
        test.tearDown()
                               
def mptest_320x50_network_generator():  
    """ Uses Nose's built in generator system to run multiple tests. """     
    test = RenderingTestBase()
    for network_name in network_names:
        test.setUp()  
        yield test.render_320x50_creative, network_name
        test.tearDown()
       
    
    
    
    
            
      
