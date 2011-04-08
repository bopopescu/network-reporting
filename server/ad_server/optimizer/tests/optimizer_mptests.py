import os
import sys
sys.path.append(os.environ['PWD'])

import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.optimizer import optimizer

from advertiser.models import AdGroup, Creative


import datetime

  
class TestOptimizer(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        # Set up useful datetime
        dt = datetime.datetime(1987,4,4,4,4)# save some test time
        
        # Set up a default adunit
        

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_load_campaigns(self):
        eq_(1000,1000)
      
    def mptest_no_information(self):
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=self.dt)
        eq_(ctr, CTR)

    def mptest_hour_cache_success(self):
        CTR = .55
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, CTR, hour=self.dt.hour)
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, CTR)
  
    def mptest_hour_default(self):
        OLD_CTR = .99
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time

        # Set a CTR for the previous hour
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, OLD_CTR,
                                       hour=self.dt.hour - datetime.timedelta(hours=1))

        # There are zero impressions for the current hour, so we don't have enough to calculate CTR
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, OLD_CTR)
    
    def mptest_hour_first_time_cache_miss_zero_samples(self):
        OLD_CTR = .99
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time
        
        # Set a CTR for the previous hour
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, OLD_CTR,
                                       hour=self.dt.hour - datetime.timedelta(hours=1))
                                       
        # There are zero impressions for the current hour, so we don't have enough to calculate CTR
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, OLD_CTR)
    
    def mptest_hour_first_time_cache_miss_insufficient_samples(self):
        OLD_CTR = .99
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time

        # Set a CTR for the previous hour
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, OLD_CTR,
                                       hour=self.dt.hour - datetime.timedelta(hours=1))
                                       
        self._add_impression(click=True)

        # There is one impression for the current hour, but we need at least 5 to calculate CTR
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, OLD_CTR)  
        
    def mptest_hour_first_time_cache_miss_calculate_success(self):
        OLD_CTR = .99
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time

        # Set a CTR for the previous hour
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, OLD_CTR,
                                       hour=self.dt.hour - datetime.timedelta(hours=1))

        for i in xrange(5):
            self._add_impression(click=True)
        
        # We now have enough to calculate the ctr, do it
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, 1.00)  # they have all been successful
        
    def mptest_hour_first_time_cache_miss_calculate_success_do_not_recalc(self):
        OLD_CTR = .99
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time

        # Set a CTR for the previous hour
        optimizer._set_ctr_in_memcache(self.adunit, self.creative, OLD_CTR,
                                       hour=self.dt.hour - datetime.timedelta(hours=1))

        for i in xrange(5):
            self._add_impression(click=True)

        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, 1.00)  # they have all been successful

        for i in xrange(5):
            self._add_impression(click=False)

        # Even though there have been some failures, we use info from the cache
        ctr = optimizer._test_get_ctr(self.adunit, self.creative, dt=test_dt)
        eq_(ctr, 1.00)  # they have all been successful
    