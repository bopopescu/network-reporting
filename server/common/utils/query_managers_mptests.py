import os
import sys
sys.path.append(os.environ['PWD'])

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

from advertiser.query_managers import AdGroupQueryManager

from publisher.query_managers import AdUnitContextQueryManager
  
from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR
  
class TestQueryManagers(unittest.TestCase):
    """ Make sure that adunit_context is appropriately removed from the cache """

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        
        # Set up useful datetime
        self.dt = datetime.datetime(1987,4,4,4,4)# save some test time
        self.one_hour_ago = self.dt - datetime.timedelta(hours=1)
        
        # Set up default models
        self.account = Account()
        self.account.put()
        
        self.app = App(account=self.account, name="Test App")
        self.app.put()
        
        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit")
        self.adunit.put()
        
        self.campaign = Campaign(name="Test Campaign")
        self.campaign.put()
        
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
        
    def tearDown(self):
        self.testbed.deactivate()
        
        
    def mptest_adgroup_qm(self):
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.adgroups), 1)
        
        self.adgroup2 = AdGroup(account=self.account, 
                               campaign=self.campaign, 
                               site_keys=[self.adunit.key()],
                               bid_strategy="cpc",
                               bid=100.0)
                
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.adgroups), 1)
                               
        # Adds to the datastore and deletes context from cache                       
        AdGroupQueryManager.put(self.adgroup2)
        
        # Now we rebuild with the new adgroup
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.adgroups), 2)
        
    def mptest_stats(self):
        eq_(True, True)
        
        
        
        
        
        
        
        
        
        
        
        
