import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup


import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.optimizer import optimizer

from advertiser.models import AdGroup, Creative, Campaign

from account.models import Account

from publisher.models import App
from publisher.models import Site as AdUnit

import datetime

import logging

from common.utils.decorators import (caches_page_until_session_post,
                                     key_from_view_function,
                                     clears_session_cache)
  
class TestCacheDecorators(unittest.TestCase):
    """ Make sure that adunit_context is appropriately removed from the cache """

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        
    def tearDown(self):
        self.testbed.deactivate()
        
        
    def mptest_build_key(self):
        pass
    
        
  