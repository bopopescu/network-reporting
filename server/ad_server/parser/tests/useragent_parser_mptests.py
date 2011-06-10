import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.parser.useragent_parser import get_os_version, get_os

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
                                         ios_version_min=2.0,
                                         ios_version_max=999,
                                         target_android=False,
                                         android_version_min=1.6,
                                         android_version_max=999)
        self.ipad_only_adgroup.put()                          
          
          
        self.recent_android_adgroup = AdGroup(target_ios=False,
                                         target_android=True,
                                         android_version_min=2.3,
                                         android_version_max=999)
        self.ipad_only_adgroup.put()                                 
                                         
    def tearDown(self):                  
        self.testbed.deactivate()
        
    ################# Unit Tests ################
        
    def mptest_ipad(self):
        user_agent = "Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10"
        
        eq_(get_os(user_agent), "iOS")
        eq_(get_os_version(user_agent), 'iphone__3_2')
        
    def mptest_iphone(self):
        user_agent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 3_0 like Mac OS X; en-us) AppleWebKit/528.18 (KHTML, like Gecko) Version/4.0 Mobile/7A341 Safari/528.16"

        eq_(get_os(user_agent), "iOS")
        eq_(get_os_version(user_agent), 'iphone__3_0')
        
        
    def mptest_iphone(self):
        user_agent = "Some android agent"

        eq_(get_os(user_agent), "android")
        eq_(get_os_version(user_agent), 'android__2_0')     
        
    ################# Integration Tests ################
        
    def mptest_filter(self):
        
        
        