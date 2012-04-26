import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.parser.useragent_parser import get_os
from advertiser.models import AdGroup
from ad_server.filters.filters import os_filter

import logging

  
class TestUseragentParser(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        
        self.other_only_adgroup = AdGroup(target_ipad=False,
                                         target_ipod=False,
                                         target_iphone=False,
                                         target_android=False,
                                         target_other=True,
                                         device_targeting=True)
        self.other_only_adgroup.put()                          
        

        self.ipad_only_adgroup = AdGroup(target_ipad=True,
                                         target_ipod=False,
                                         target_iphone=False,
                                         target_other=False,
                                         ios_version_min="2.0",
                                         ios_version_max="999",
                                         target_android=False,
                                         android_version_min="1.6",
                                         android_version_max="999",
                                         device_targeting=True)
        self.ipad_only_adgroup.put()                          
          
          
        self.recent_android_adgroup = AdGroup(target_ipad=False,
                                         target_ipod=False,
                                         target_iphone=False,
                                         target_android=True,
                                         target_other=False,
                                         android_version_min="1.5.1",
                                         android_version_max="1.5.1",
                                         device_targeting=True)
        self.ipad_only_adgroup.put() 
        
        self.default_adgroup = AdGroup()
        self.default_adgroup.put()                                
                                         
    def tearDown(self):                  
        self.testbed.deactivate()
        
    ################# Unit Tests ################
        
        
    def mptest_uses_default_device_targeting(self):
        
        eq_(self.default_adgroup.uses_default_device_targeting, True)
        eq_(self.ipad_only_adgroup.uses_default_device_targeting, False)
        eq_(self.recent_android_adgroup.uses_default_device_targeting, False)
        eq_(self.other_only_adgroup.uses_default_device_targeting, False)
        
    def mptest_ipad(self):
        user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"
        assert(get_os(user_agent) == ("iOS",'iPad','3.2'))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.ipad_only_adgroup))

    def mptest_ipod(self):
        user_agent = "Mozilla/5.0 (iPod; CPU iPhone OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 Safari/7534.48.3"
        assert(get_os(user_agent) == ('iOS', 'iPod', '5.0.1'))
        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.ipad_only_adgroup))

    def mptest_ipod_touch(self):
        user_agent = "Mozilla/5.0 (iPod touch; CPU iPhone OS 5_0_1 like Mac OS X) AppleWebKit/534.46 (KHTML, like Gecko) Version/5.1 Mobile/9A405 Safari/7534.48.3"
        assert(get_os(user_agent) == ('iOS', 'iPod', '5.0.1'))
        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.ipad_only_adgroup))
    
    def mptest_iphone(self):
        user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 2.0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
        assert(get_os(user_agent) == ("iOS",'iPhone','2.0'))
        
        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.ipad_only_adgroup))
        
    def mptest_android(self):
        user_agent = "Mozilla/5.0 (Linux; U; Android 1.5.1; en-us; VM670 Build/FRG83) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
        assert(get_os(user_agent) == ("android",None,'1.5.1'))
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.recent_android_adgroup))
        
    def mptest_none(self):
        """ Everything should pass the default adgroup"""
        user_agent = ''
        assert(get_os(user_agent) == (None,None,None))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.default_adgroup))

    def mptest_none_to_ipad(self):
        """ Other should not pass ipad only """
        user_agent = ''
        assert(get_os(user_agent) == (None,None,None))

        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.ipad_only_adgroup))        
        
    def mptest_too_low_version(self):
        user_agent = "Mozilla/5.0 (Linux; U; Android 1.2.1; en-us; VM670 Build/FRG83) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
        assert(get_os(user_agent) == ("android",None,'1.2.1'))
        
        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.recent_android_adgroup))  
        
        
        
    def mptest_other_fail(self):
        user_agent = "Mozilla/5.0 (Linux; U; Android 1.2.1; en-us; VM670 Build/FRG83) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
        assert(get_os(user_agent) == ("android",None,'1.2.1'))
        
        filter1 = os_filter(user_agent)[0]
        assert(not filter1(self.other_only_adgroup))  
        
        
    def mptest_other_success(self):
        """ Everything should pass the default adgroup"""
        user_agent = ''
        assert(get_os(user_agent) == (None,None,None))

        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.other_only_adgroup))
        
