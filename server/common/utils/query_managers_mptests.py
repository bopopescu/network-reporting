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

from advertiser.query_managers import AdGroupQueryManager, CampaignQueryManager, CreativeQueryManager

from publisher.query_managers import AdUnitContextQueryManager, AdUnitQueryManager, AppQueryManager

from account.query_managers import AccountQueryManager
  
from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR
  
class TestQueryManagersAdunitContext(unittest.TestCase):
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
        self.account = Account(company="Test Company")
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
        
    def mptest_creative_qm(self):
        
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.creatives), 1)
        
        self.creative2 = Creative(account=self.account,
                                 ad_group=self.adgroup,
                                 tracking_url="test-tracking-url2")
                
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.creatives), 1)
                               
        # Adds to the datastore and deletes context from cache                       
        CreativeQueryManager.put(self.creative2)
        
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.creatives), 2)
   
    
    def mptest_campaign_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.campaigns[0].name, "Test Campaign")

        self.campaign.name = "Test Campaign Changed"

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.campaigns[0].name, "Test Campaign")

        # Adds to the datastore and deletes context from cache                       
        CampaignQueryManager.put(self.campaign)

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.campaigns[0].name, "Test Campaign Changed")

    def mptest_adunit_qm(self):
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.name, "Test AdUnit")

        old_key = self.adunit.key()

        self.adunit.name="Test AdUnit Changed"

        # Adds to the datastore and deletes context from cache                           
        AdUnitQueryManager.put(self.adunit)

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())

        eq_(old_key, self.adunit.key())

        eq_(context.adunit.name, "Test AdUnit Changed")

    def mptest_adunit_qm_deep_copy(self):
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.name, "Test AdUnit")

        old_key = self.adunit.key()

        # Get another copy of the adunit
        adunit_copy = AdUnitQueryManager.get(old_key)
        
        eq_(adunit_copy.key(), old_key)
        
        # Change the copy
        adunit_copy.name = "Test AdUnit Changed"

        context = AdUnitContextQueryManager.cache_get_or_insert(adunit_copy.key())
        eq_(context.adunit.name, "Test AdUnit")

        # Adds to the datastore and deletes context from cache                       
        AdUnitQueryManager.put(adunit_copy)

        context = AdUnitContextQueryManager.cache_get_or_insert(adunit_copy.key())
        eq_(context.adunit.name, "Test AdUnit Changed")
    
    def mptest_account_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.account.company, "Test Company")

        self.account = Account(company="Test Company")

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.account.company, "Test Company")

        # Adds to the datastore and deletes context from cache                       
        AccountQueryManager.put(self.account)

        # Now we rebuild with the new adgroup
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.account.company, "Test Company")
 
    def mptest_app_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.app_key.name, "Test App")

        self.app.name = "Test App Changed"

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.app_key.name, "Test App")

        # Adds to the datastore and deletes context from cache                       
        AppQueryManager.put(self.app)

        # Now we rebuild with the new adgroup
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.app_key.name, "Test App Changed")


    def mptest_adgroup_no_qm(self):
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.adgroups), 1)

        self.adgroup2 = AdGroup(account=self.account, 
                               campaign=self.campaign, 
                               site_keys=[self.adunit.key()],
                               bid_strategy="cpc",
                               bid=100.0)
                               
        # Adds to the datastore but does not delete context from cache                       
        self.adgroup2.put()

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.adgroups), 1)

    def mptest_creative_no_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.creatives), 1)

        self.creative2 = Creative(account=self.account,
                                 ad_group=self.adgroup,
                                 tracking_url="test-tracking-url2")

        # Adds to the datastore but does not delete context from cache                       
        self.creative2.put()

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(len(context.creatives), 1)

    def mptest_campaign_no_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.campaigns[0].name, "Test Campaign")

        self.campaign.name = "Test Campaign Changed"

        # Adds to the datastore but does not delete context from cache                       
        self.campaign.put()
        
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.campaigns[0].name, "Test Campaign")

    def mptest_adunit_no_qm(self):
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.name, "Test AdUnit")

        old_key = self.adunit.key()

        self.adunit.name="Test AdUnit Changed"

        # Adds to the datastore but does not delete context from cache                       
        self.adunit.put()

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        
        eq_(old_key, self.adunit.key())
        
        eq_(context.adunit.name, "Test AdUnit")

    def mptest_account_no_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.account.company, "Test Company")

        self.account = Account(company="Test Company")
        
        # Adds to the datastore but does not delete context from cache                       
        self.account.put()

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.account.company, "Test Company")


    def mptest_app_no_qm(self):

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.app_key.name, "Test App")

        self.app.name = "Test App Changed"

        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())

        # Adds to the datastore but does not delete context from cache                       
        self.app.put()
        
        context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
        eq_(context.adunit.app_key.name, "Test App")