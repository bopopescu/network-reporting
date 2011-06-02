import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from advertiser.models import AdGroup
from ad_server.filters.filters import kw_filter, format_filter

import unittest
from google.appengine.ext import testbed
from publisher.models import App
from publisher.models import Site as AdUnit
from advertiser.models import Creative, Campaign
from account.models import Account


#def kw_filter_mptest():
#    adgroup = AdGroup(keywords=[('m_age:19 AND m_gender:m'), # OR
#                                ('m_age:20 AND m_gender:f')])
#    
#    # True means this filter would like to reject the value                            
#    inputs_expected = {('m_age:19','m_gender:m','color:blue'):True,
#                       ('m_age:22','m_gender:f','color:blue'):False,
#                       ('m_age:19','m_gender:f'):False,
#                       ('m_age:20','m_gender:f','color:green'):True,
#                      }
#    
#    for keywords,match in inputs_expected.iteritems():
#        f,log_message,removed_list = kw_filter(keywords)
#        print keywords, f(adgroup)
#        assert f(adgroup) == match

class CustomSizeUnitTests(unittest.TestCase):
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
        
        self.campaign = Campaign(name="Test Campaign")
        self.campaign.put()

   #     self.network_config = NetworkConfig(ejam_pub_id = '23710')
    #    self.network_config.put()
        
        self.adunit1 = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit 1", format="custom", custom_width=120., custom_height=200.)#, network_config=self.network_config)
        self.adunit1.put()
        
        self.adunit2 = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit 2", format="custom", custom_width=300., custom_height=400.)#, network_config=self.network_config)
        self.adunit2.put()
        
        self.adunit3 = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit 3", format="320x50")#, network_config=self.network_config)
        self.adunit3.put()
        
        self.adgroup = AdGroup(account=self.account, 
                               campaign=self.campaign, 
                               site_keys=[self.adunit1.key(), self.adunit2.key(),self.adunit3.key()],
                               )
        self.adgroup.put()
        
        self.creative1 = Creative(account=self.account, ad_group = self.adgroup, name="Test Creative 1", format="custom", custom_width=120., custom_height=200.)
        self.creative1.put()
        
        self.creative2 = Creative(account=self.account, ad_group = self.adgroup, name="Test Creative 2", format="custom", custom_width=300., custom_height=400.)
        self.creative2.put()
        
        self.creative3 = Creative(account=self.account, ad_group = self.adgroup, name="Test Creative 3", format="custom", custom_width=320., custom_height=50.)
        self.creative3.put()
        
    def tearDown(self):
        self.testbed.deactivate()

    def mptest_filter_basictest(self):
        print format_filter(self.adunit1)
        print "hi"
        #assert()