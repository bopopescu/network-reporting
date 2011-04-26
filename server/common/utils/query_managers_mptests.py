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

from publisher.query_managers import AdUnitContextQueryManager
  
from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR
  
class TestAccountQueryManager(unittest.TestCase):

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
        
        # Set up QM
        self.smqm = StatsModelQueryManager(self.account)
        
        # Roll up adunit context
        self.adunit_context = AdUnitContext.wrap(self.adunit)
        
    def tearDown(self):
        self.testbed.deactivate()
        
        
    def mptest_stats(self):
        apps = StatsModel.all().fetch(10)
        
        logging.info(apps)
        eq_(len(apps),0)
