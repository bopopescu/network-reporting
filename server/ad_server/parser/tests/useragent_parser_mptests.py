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
        

        self.ipad_only_adgroup = AdGroup(target_ios=True,
                                         ios_version_min="2.0",
                                         ios_version_max="999",
                                         target_android=False,
                                         android_version_min="1.6",
                                         android_version_max="999")
        self.ipad_only_adgroup.put()                          
          
          
        self.recent_android_adgroup = AdGroup(target_ios=False,
                                         target_android=True,
                                         android_version_min="1.5.1",
                                         android_version_max="1.5.1")
        self.ipad_only_adgroup.put() 
        
        self.default_adgroup = AdGroup()
        self.default_adgroup.put()                                
                                         
    def tearDown(self):                  
        self.testbed.deactivate()
        
    ################# Unit Tests ################
        
    def mptest_ipad(self):
        user_agent = "Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"
        assert(get_os(user_agent) == ("iOS",'3.2'))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.ipad_only_adgroup))
        
    def mptest_iphone(self):
        user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 2.0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"
        assert(get_os(user_agent) == ("iOS",'2.0'))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.ipad_only_adgroup))
        
    def mptest_android(self):
        user_agent = "Mozilla/5.0 (Linux; U; Android 1.5.1; en-us; VM670 Build/FRG83) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1"
        assert(get_os(user_agent) == ("android",'1.5.1'))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.recent_android_adgroup))
        
    def mptest_none(self):
        user_agent = ""
        assert(get_os(user_agent) == (None,None))
        
        filter1 = os_filter(user_agent)[0]
        assert(filter1(self.default_adgroup))
        
        