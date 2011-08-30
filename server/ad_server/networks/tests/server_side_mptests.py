
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
                                          
from server.ad_server.main import  ( AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from server.ad_server.handlers.adhandler import AdHandler    
                                     
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache  
from google.appengine.api import urlfetch       
from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.brightroll import BrightRollServerSide   
from ad_server.networks.admob import AdMobServerSide  
from ad_server.networks.ejam import EjamServerSide

################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request

from account.models import Account, NetworkConfig    

from ad_server.auction.client_context import ClientContext      



""" This module is where all of our system and end-to-end tests can live. """

class TestNetworkConfig(unittest.TestCase):
    """ This cannot be tested until appengine properly implements init_user_stub """

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()
        
        # Set up useful datetime
        self.dt = datetime.datetime(1987,4,4,4,4)# save some test time
        
        # Set up network config
        self.account_network_config = NetworkConfig(
                                brightroll_pub_id="account-brightroll",
                                millennial_pub_id="account-millennial",
                                jumptap_pub_id="account-jumptap")
        self.account_network_config.put()
        
        self.app_network_config = NetworkConfig(
                                jumptap_pub_id="app-jumptap",
                                millennial_pub_id="app-millennial")
                                
        self.app_network_config.put()

        # Set up default models
        self.account = Account(company="awesomecorp", 
                               network_config=self.account_network_config)
        self.account.put()

        self.app = App(account=self.account, name="Test App",
                               network_config=self.app_network_config)
        self.app.put()

        
        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit")
        self.adunit.put()    
        
        self.client_context = ClientContext(adunit=self.adunit,
                                            country_code="US", # Two characater country code.  
                                            raw_udid="fake_udid",   
                                            request_id="fake_request_id",
                                            now=datetime.datetime.now(),
                                            user_agent="Mozilla/5.0 (iPad; U; CPU OS 3.2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10")   
        
            
    def tearDown(self):
        self.testbed.deactivate()
        
        ############### ServerSide Tests ###############
  
    def mptest_admob(self):
        """ Make sure we go to lowest available level. Here app level """
        server_side = AdMobServerSide(self.client_context, self.adunit) 
        pub_id = server_side.get_pub_id()
        
        eq_(pub_id, "app-admob")
    
    
    def mptest_millennial(self):
        """ Make sure we go to lowest available level. Here app level """
        server_side = MillennialServerSide(self.client_context, self.adunit) 
        pub_id = server_side.get_pub_id()
        
        eq_(pub_id, "app-millennial")
        
    def mptest_brightroll(self):
        """ Make sure we go to lowest available level. Here account level """
        server_side = BrightRollServerSide(self.client_context, self.adunit) 
        pub_id = server_side.get_pub_id()
    
        eq_(pub_id, "account-brightroll")
    
    def mptest_jumptap(self):
        """ Jumptap requires multiple pub ids"""
        server_side = JumptapServerSide(self.client_context, self.adunit) 
        key_values = server_side.get_key_values()
        eq_(key_values["pub"],"account-jumptap")
        eq_(key_values["site"],"app-jumptap")
        
    
    def mptest_jumptap_no_adunit(self):
        """ Make sure that the key value dictionary sent to jumptap does not
        contain any keys for unspecified pub ids """
        server_side = JumptapServerSide(self.client_context, self.adunit) 
        key_values = server_side.get_key_values()
    
        try:
            adunit_pub_id = key_values["spot"] # this should raise a keyerror
        except KeyError:
            pass
        else:
            # If no key error was thrown, fail
            eq_(adunit_pub_id, "A key error should have been raised")        
            
            
            
            
####### These tests actively ping the servers for a response        

class MoceanUnitTests(unittest.TestCase):
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

        self.network_config = NetworkConfig(ejam_pub_id = '23710')
        self.network_config.put()

        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit", network_config=self.network_config)
        self.adunit.put()

    def tearDown(self):
        self.testbed.deactivate()

    def mptest_mocean_basictest(self):     
        
       self.client_context = ClientContext(adunit=self.adunit,
                                            country_code="US", # Two characater country code.  
                                            raw_udid="fake_udid",   
                                            request_id="fake_request_id",
                                            now=datetime.datetime.now(),
                                            user_agent='FakeAndroidOS')
       
       mocean = EjamServerSide(self.client_context, self.adunit)
       url = mocean.url
       url += "&test=1"
       print url
       
       response = urlfetch.fetch(url)
       
       print response.content
       
       response_tuple = mocean.bid_and_html_for_response(response)
       
       print response_tuple
       assert(response_tuple[1])