import os
import sys
sys.path.append(os.environ['PWD'])

import unittest
from nose.tools import eq_
from nose.tools import with_setup

from google.appengine.ext import testbed
from google.appengine.api import memcache
from ad_server.memcache_mangler import ClearHandler

class TestMemcache(unittest.TestCase):
    
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
  
    def mptest_flush(self):
        memcache.add("thing", 15)
        eq_(memcache.get("thing"), 15)
        
        memcache.flush_all()
        eq_(memcache.get("thing"), None)
    
    def mptest_delete(self):
        memcache.add("thing", 15)
        eq_(memcache.get("thing"), 15)

        memcache.delete("thing")
        eq_(memcache.get("thing"), None)


    def mptest_delete_no_namespace(self):
        memcache.add("thing", 15)
        eq_(memcache.get("thing"), 15)

        memcache.delete("thing", namespace=None)
        eq_(memcache.get("thing"), None)
