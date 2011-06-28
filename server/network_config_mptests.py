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
from server.ad_server.auction.ad_auction import AdAuction
                                     
############# Integration Tests #############
import unittest
from nose.tools import eq_
from nose.tools import with_setup
from budget import budget_service
from google.appengine.api import memcache
from budget.models import (Budget,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           )

from google.appengine.ext import testbed

from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.brightroll import BrightRollServerSide

################# End to End #################

from common.utils.system_test_framework import run_auction, fake_request

from account.models import Account, NetworkConfig


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
            
    def tearDown(self):
        self.testbed.deactivate()
    
    def mptest_account(self):
        # Get the network info from an account
        eq_(self.adunit.get_pub_id("brightroll_pub_id"), "account-brightroll")

    def mptest_app(self):
        # Get the network info from an account
        eq_(self.adunit.get_pub_id("jumptap_pub_id"), "app-jumptap")

    def mptest_app_delete(self):
        # Get the network info from an account  
        self.app_network_config.jumptap_pub_id = None
        eq_(self.adunit.get_pub_id("jumptap_pub_id"), "account-jumptap")

    def mptest_add_adunit(self):
        self.adunit_network_config = NetworkConfig(
                                jumptap_pub_id="adunit-jumptap")
        self.adunit_network_config.put()
        
        self.adunit.network_config = self.adunit_network_config
        self.adunit.put()
        
        eq_(self.adunit.get_pub_id("jumptap_pub_id"), "adunit-jumptap")
        
        
        
    ############### ServerSide Tests ###############
    
    def mptest_millennial(self):
        """ Make sure we go to lowest available level. Here app level """
        server_side = MillennialServerSide(fake_request(self.adunit), self.adunit) 
        pub_id = server_side.get_pub_id()
        
        eq_(pub_id, "app-millennial")
        
    def mptest_brightroll(self):
        """ Make sure we go to lowest available level. Here account level """
        server_side = BrightRollServerSide(fake_request(self.adunit), self.adunit) 
        pub_id = server_side.get_pub_id()
    
        eq_(pub_id, "account-brightroll")
    
    def mptest_jumptap(self):
        """ Jumptap requires multiple pub ids"""
        server_side = JumptapServerSide(fake_request(self.adunit), self.adunit) 
        key_values = server_side.get_key_values()
        eq_(key_values["pub"],"account-jumptap")
        eq_(key_values["site"],"app-jumptap")
        
    
    def mptest_jumptap_no_adunit(self):
        """ Make sure that the key value dictionary sent to jumptap does not
        contain any keys for unspecified pub ids """
        server_side = JumptapServerSide(fake_request(self.adunit), self.adunit) 
        key_values = server_side.get_key_values()
    
        try:
            adunit_pub_id = key_values["spot"] # this should raise a keyerror
        except KeyError:
            pass
        else:
            # If no key error was thrown, fail
            eq_(adunit_pub_id, "A key error should have been raised")