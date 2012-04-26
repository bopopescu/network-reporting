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

from reporting.models import StatsModel

from reporting.query_managers import StatsModelQueryManager

from publisher.models import App
from publisher.models import Site as AdUnit

import datetime

import logging

from publisher.query_managers import AdUnitContextQueryManager
  
from ad_server.adunit_context.adunit_context import AdUnitContext, CreativeCTR
  
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
        
    def mptest_stats_exist(self):
        self._set_statsmodel_click_count(self.adunit, self.creative, 65, dt=self.dt)
        self._set_statsmodel_click_count(self.adunit, self.creative, 66, dt=self.dt)
        apps = StatsModel.all().fetch(100)
        
        assert apps
        
    def mptest_get_stats_for_days(self):
        self._set_statsmodel_click_count(self.adunit, self.creative, 65, dt=self.dt)
    
                
        qm_stats = self.smqm.get_stats_for_days(publisher=self.adunit,
                                            advertiser=self.creative,
                                            days=[self.dt.date()],
                                            use_mongo=False)
        
        
        stats = qm_stats[0] # qm_stats is a list of stats of length 1
        
        eq_(stats.click_count, 65)
    
    def mptest_get_stats_for_days_ctr(self):
        self._set_statsmodel_click_count(self.adunit, self.creative, 25, dt=self.dt)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 100, dt=self.dt)
    
        qm_stats = self.smqm.get_stats_for_days(publisher=self.adunit,
                                            advertiser=self.creative,
                                            days=[self.dt.date()],
                                            use_mongo=False)
        stats = qm_stats[0] # qm_stats is a list of stats of length 1
    
        logging.warning(stats)
    
        eq_(stats.click_count, 25)
        eq_(stats.impression_count, 100)
        eq_(stats.ctr, .25)
        
        
    def mptest_context(self):
        # Test that we have the appropriate rollups
        eq_(self.adunit_context.adunit, self.adunit)
        eq_(self.adunit_context.campaigns[0].key(), self.campaign.key())
        eq_(self.adunit_context.adgroups[0].key(), self.adgroup.key())
        eq_(self.adunit_context.creatives[0].tracking_url, "test-tracking-url")
       
       
    def mptest_creative_ctrs_key(self):
         creative_ctr = CreativeCTR(self.creative, self.adunit)
         eq_(creative_ctr.creative.key(), self.creative.key())
                 
    def mptest_adunit_context_rollup(self):
        daily_CTR = .65
      
        # Set up test
        self._set_statsmodel_click_count(self.adunit, self.creative, 650, dt=self.dt)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1000, dt=self.dt)
      
        # The adunit has been updated, so we roll up the adunit_context
        self.adunit_context = AdUnitContext.wrap(self.adunit)
      
        ctr = self.adunit_context._get_ctr(self.creative, date=self.dt.date())
        eq_(ctr, daily_CTR)
      
    def mptest_adunit_context_multiple_dates(self):
        """Tests for the case in which both hours are unset and have insufficient samples,
        we then fall back to the daily """
        
        # Set up test
        self._set_statsmodel_click_count(self.adunit, self.creative, 100, dt=self.dt)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1000, dt=self.dt)
        
        self._set_statsmodel_click_count(self.adunit, self.creative, 200, dt=datetime.datetime.now())
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1000, dt=datetime.datetime.now())
    
        ctr = self.adunit_context._get_ctr(self.creative, date=self.dt.date())
        today_ctr = self.adunit_context._get_ctr(self.creative, date=datetime.date.today())
        eq_(ctr, .10)
        eq_(today_ctr, .20)
    
    def mptest_hour_default(self):
        self._set_statsmodel_click_count(self.adunit, self.creative, 1, dt=self.dt)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 2, dt=self.dt)
        test_dt = datetime.datetime(1987,4,4,4,4) # save some test time
    
        # There are 2 impressions for the current hour, so we don't have enough to calculate CTR
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=test_dt, default_ctr=.01)
        eq_(ctr, .01)
        
        # Right now we are using a global default CTR of 0.005
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=test_dt)
        eq_(ctr, .005)
    
    def mptest_hour_failure_day_success(self):
        """Tests for the case in which the hour has insufficient samples,
        we then fall back to the daily """
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)
        
        # Set up test
        
        self._set_statsmodel_click_count(self.adunit, self.creative, 100, dt=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, dt=two_hours_ago)
    
        self._set_statsmodel_click_count(self.adunit, self.creative, 100, dt=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 800, dt=one_hour_ago)
        
    
        # There are only 800 samples for the hour in the datastore so we fall back to daily
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=self.dt)
        
        # The total is 200 clicks and 2000 impressions
        eq_(ctr, .10)
        
    def mptest_hourly_smqm(self):
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        #  two_hours_ago = self.dt - datetime.timedelta(hours=2)
    
        # Set up test
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, date_hour=one_hour_ago)
    
    
        qm_stats = self.smqm.get_stats_for_hours(publisher=self.adunit,
                                         advertiser=self.creative,
                                         date_hour=one_hour_ago)
        stats = qm_stats # qm_stats is a list of stats of length 1
        eq_(stats.impression_count, 1200)
        
    def mptest_hour_simple(self):
        """Tests that adunit context can correctly calculate the ctr of an hour """
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)
        
        # Set up test
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, date_hour=one_hour_ago)
         
        qm_stats = self.smqm.get_stats_for_hours(publisher=self.adunit,
                                         advertiser=self.creative,
                                         date_hour=one_hour_ago)
        stats = qm_stats # qm_stats is a list of stats of length 1
        eq_(stats.impression_count, 1200)
        
        # The previous hour has sufficient samples
        ctr = self.adunit_context._get_ctr(self.creative, date_hour=self.dt)
        eq_(ctr, .50)
        
        
    def mptest_hour_overwrite(self):
        """Tests for the case in which the previous hour had sufficient samples,
        but it is overwritten """
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)
          
        # Set up test
    
        self._set_statsmodel_click_count(self.adunit, self.creative, 200, date_hour=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 2000, date_hour=two_hours_ago)
        
        
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=two_hours_ago)
        # The total is 200 clicks and 2000 impressions
        eq_(ctr, .10)
    
        self._set_statsmodel_click_count(self.adunit, self.creative, 1500, date_hour=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1500, date_hour=one_hour_ago)
    
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=one_hour_ago)
        # Uses the complete preceding hour 200/2000
        eq_(ctr, .1)
       
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=self.dt)
    
        # The total is 1500 clicks and 1500 impressions
        eq_(ctr, 1.0)
    
    def mptest_stats_rollup(self):
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)
          
        # Set up test
    
        self._set_statsmodel_click_count(self.adunit, self.creative, 0, date_hour=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 600, date_hour=two_hours_ago)
        
        
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 600, date_hour=one_hour_ago)
        
        
        qm_stats = self.smqm.get_stats_for_days(publisher=self.adunit,
                                            advertiser=self.creative,
                                            days=[self.dt.date()],
                                            use_mongo=False)
       
        stats = qm_stats[0] # qm_stats is a list of stats of length 1
        eq_(stats.impression_count, 1200)
    
        ctr = self.adunit_context._get_ctr(self.creative, date=self.dt.date())
        eq_(ctr, 0.5)
        
        # There are insufficient datapoints to use hourly, so we use daily
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=self.dt)
        eq_(ctr, 0.5)
        
    def mptest_stats_daily_rollover(self):
        self.dt = datetime.datetime(1987,4,4,1,4) # shortly after midnight
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)
        yesterday = self.dt - datetime.timedelta(days=1)
        # Set up test
       
        self._set_statsmodel_click_count(self.adunit, self.creative, 0, date_hour=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 600, date_hour=two_hours_ago)
       
       
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 600, date_hour=two_hours_ago)
       
       
        qm_stats = self.smqm.get_stats_for_days(publisher=self.adunit,
                                            advertiser=self.creative,
                                            days=[yesterday],
                                            use_mongo=False)
       
        stats = qm_stats[0] # qm_stats is a list of stats of length 1
        eq_(stats.impression_count, 1200)
       
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=yesterday)
       
        # There are insufficient datapoints to use hourly, so we use daily
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=self.dt)
        eq_(ctr, 0.5)
        
      
       
    def mptest_cache_simple(self):
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        # Put in some arbitrary data
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, date_hour=one_hour_ago)
        
        # Cache it
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(str(self.adunit.key()))
        
        ctr = self.adunit_context._get_ctr(self.creative, date_hour=self.dt)
        eq_(ctr, 0.5)
    
        
    def mptest_cache_update(self):
        # Put in some arbitrary data
        self._set_statsmodel_click_count(self.adunit, self.creative, 600, date_hour=self.dt)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, date_hour=self.dt)
            
        # Cache context
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
            
        new_creative = Creative(account=self.account,
                                           ad_group=self.adgroup,
                                           tracking_url="test-tracking-url-2", 
                                           cpc=.03)
        new_creative.put()
    
        self._set_statsmodel_click_count(self.adunit, new_creative, 12, date_hour=self.one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, new_creative, 1200, date_hour=self.one_hour_ago)
    
        # get Cache context, make sure it is updated
                      
        # First we get a cache hit, so there is no value for this element
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
     
        ctr = adunit_context._get_ctr(new_creative, date_hour=self.dt)
    
        eq_(ctr, None)
     
     
        # Clear the cache manually, now we have the information for the new creative
        AdUnitContextQueryManager.cache_delete_from_adunits(self.adunit)
        
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(self.adunit.key())
    
        ctr = adunit_context._get_ctr(new_creative, date_hour=self.dt)
        
        eq_(ctr, 0.01)

    def mptest_ecpm_calc_cpm(self):
        # Set to cpm 
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
                               bid_strategy="cpm",
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
        
        # Check
        eq_(self.adunit_context.adgroups[0].bid_strategy, "cpm")

        # ecpm for a group with a set cpm is just cpm
        ecpm = optimizer.get_ecpm(self.adunit_context, self.creative)
        eq_(ecpm, 100)

    def mptest_ecpm_calc_cpc(self):
        one_hour_ago = self.dt - datetime.timedelta(hours=1)
        two_hours_ago = self.dt - datetime.timedelta(hours=2)

        # Set up test
        self._set_statsmodel_click_count(self.adunit, self.creative, 100, dt=two_hours_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 1200, dt=two_hours_ago)
        self._set_statsmodel_click_count(self.adunit, self.creative, 100, dt=one_hour_ago)
        self._set_statsmodel_impression_count(self.adunit, self.creative, 800, dt=one_hour_ago)


        # There are only 800 samples for the hour in the datastore so we fall back to daily
        ctr = optimizer.get_ctr(self.adunit_context, self.creative, dt=self.dt)
        # The total is 200 clicks and 2000 impressions
        eq_(ctr, .10)
        
        # Make sure we are using cpc
        eq_(self.adunit_context.adgroups[0].bid_strategy, "cpc")

        # ecpm for a group with a cpc is cpc * ctr *1000
        ecpm = optimizer.get_ecpm(self.adunit_context, self.creative, dt=self.dt)
        eq_(ecpm, 100*.1*1000)

    
############# Testing Helper Functions ###############
    
    def _set_statsmodel_click_count(self, adunit, creative, count, dt=None, date_hour=None):
        stats = StatsModel(publisher=adunit, advertiser=creative, date=dt, date_hour=date_hour)
    
        stats.click_count = count
        logging.info(stats)
    
        self.smqm.put_stats(stats)
    
    def _set_statsmodel_impression_count(self, adunit, creative, count, dt=None, date_hour=None):
        stats = StatsModel(publisher=adunit, advertiser=creative, date=dt, date_hour=date_hour)
    
        stats.impression_count = count
        logging.info(stats)
    
        self.smqm.put_stats(stats)
