                 

########## Set up Django ###########
import sys
import os
import datetime
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from account.models import Account

from publisher.models import App
from publisher.models import Site as AdUnit

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )
from ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from ad_server.handlers import adhandler
from ad_server.handlers.adhandler import AdHandler                                     


from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache

from ad_server.auction.client_context import ClientContext

from ad_server.auction import ad_auction     
from google.appengine.ext import testbed
################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request     


from ad_server.auction.battles import (Battle, 
                                       GteeBattle, 
                                       GteeHighBattle,
                                       GteeLowBattle 
                                      )
                                            
from ad_server.main import AdImpressionHandler

class TestAdAuction(unittest.TestCase):


    def setUp(self):
        
    
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()


        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.adunit = AdUnit(account=self.account, 
                                     app_key=self.app, 
                                     name="Test AdUnit",
                                     format=u'320x50')
        self.adunit.put()
                                           

        self.frequency_c = Campaign(name="frequency",
                                    budget=1000.0,
                                    budget_strategy="evenly",
                                    campaign_type="gtee")
        self.frequency_c.put()

        self.frequency_adgroup = AdGroup(account=self.account, 
                                          name="frequency",
                                          campaign=self.frequency_c, 
                                          hourly_frequency_cap=2, 
                                          daily_frequency_cap=3,
                                          site_keys=[self.adunit.key()],
                                          bid_strategy="cpm",
                                          bid=100000.0) # 100 per click
        self.frequency_adgroup.put()



        self.frequency_creative = Creative(account=self.account,
                                ad_group=self.frequency_adgroup,
                                tracking_url="test-tracking-url", 
                                cpc=.03,
                                ad_type="clear")
        self.frequency_creative.put() 
        
        
                                       
       
        self.request = fake_request(self.adunit.key())
        adunit_id = str(self.adunit.key())

        self.adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)       
       
    def tearDown(self):
        self.testbed.deactivate()       
          
    def mptest_frequency_filter_hourly(self):
        """ Make sure that frequency filtering works properly for hourly limits """     
        
        # All the contexts use the same udid 
        raw_udid = "some_arbitrary_udid"      
          
        # Make multiple copies so that excluded_adgroup_keys doesn't cause trouble   
        client_context1 = self.make_test_context(udid=raw_udid)   
                                    
        client_context2 = self.make_test_context(udid=raw_udid)       
                                       
        client_context3 = self.make_test_context(udid=raw_udid)      
         


        # Unpack results
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context1, self.adunit_context)                    
                                       
        eq_obj(creative, self.frequency_creative)  
        
        # Increment count by 1
        AdImpressionHandler.increment_frequency_counts(creative=creative,
                                                       raw_udid=raw_udid)        
        
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context2, self.adunit_context)  
        
        
        eq_obj(creative, self.frequency_creative)     
        # Increment count by 1  
        AdImpressionHandler.increment_frequency_counts(creative=creative,
                                                       raw_udid=raw_udid)        
                                                       
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context3, self.adunit_context)  
        # Can only win twice            
        eq_(creative, None)           
        
        
        
               
    def mptest_frequency_filter_daily(self):
        """ Make sure that frequency filtering works properly for hourly limits """     
        
        # All the contexts use the same udid 
        raw_udid = "some_arbitrary_udid"      
        dt = datetime.datetime(1987,4,4,4,4)# save some test time 
        dt2 = dt+datetime.timedelta(hours=1)   
        dt3 = dt+datetime.timedelta(hours=2)   
        dt4 = dt+datetime.timedelta(hours=3)   
         
        # Make multiple copies so that excluded_adgroup_keys doesn't cause trouble   
        client_context1 = self.make_test_context(udid=raw_udid, dt=dt)   
                                    
        client_context2 = self.make_test_context(udid=raw_udid, dt=dt2)       
                                       
        client_context3 = self.make_test_context(udid=raw_udid,dt=dt3)  
        
        client_context4 = self.make_test_context(udid=raw_udid,dt=dt4)      
         


        # Unpack results
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context1, self.adunit_context)                    
                                       
        eq_obj(creative, self.frequency_creative)  
        
        # Increment count to 1
        AdImpressionHandler.increment_frequency_counts(creative=creative,
                                                       raw_udid=raw_udid,
                                                       now=dt)        
        
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context2, self.adunit_context)  
        
        
        eq_obj(creative, self.frequency_creative)     
        # Increment count to 2
        AdImpressionHandler.increment_frequency_counts(creative=creative,
                                                       raw_udid=raw_udid,
                                                       now=dt2)        
        
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context3, self.adunit_context)  
        
        
        eq_obj(creative, self.frequency_creative)     
        # Increment count to 3
        AdImpressionHandler.increment_frequency_counts(creative=creative,
                                                       raw_udid=raw_udid,
                                                       now=dt3)        
                                                                                 
        creative, on_fail_exclude_adgroups = ad_auction.run(client_context4, self.adunit_context)  
        # removed due to daily limit           
        eq_(creative, None)           
        

    def make_test_context(self, udid, dt=datetime.datetime.now()):
        return ClientContext(adunit=self.adunit,
                                           keywords=None,
                                           country_code=None,
                                           excluded_adgroup_keys=[],
                                           raw_udid=udid, 
                                           ll=None, 
                                           now=dt,
                                           request_id=None,            
                                           user_agent='FakeAndroidOS',
                                           experimental=False)       
        
def eq_obj(obj1, obj2):
    eq_(obj1.key(), obj2.key())          
