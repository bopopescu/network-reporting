import os
import sys
sys.path.append(os.environ['PWD'])

import new
import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.optimizer import optimizer


from advertiser.models import AdGroup, Creative, Campaign

from account.models import Account, NetworkConfig

from publisher.models import App, AdUnit

import datetime

import logging

from account.query_managers import AccountQueryManager

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
                                jumptap_pub_id="account-jumptap")
        self.account_network_config.put()
        
        self.app_network_config = NetworkConfig(
                                jumptap_pub_id="app-jumptap")
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
        eq_(self.adunit.get_pub_id("brightroll"), "account-brightroll")

    def mptest_app(self):
        # Get the network info from an account
        eq_(self.adunit.get_pub_id("jumptap"), "app-jumptap")

    def mptest_app_delete(self):
        # Get the network info from an account  
        self.app_network_config.jumptap_pub_id = None
        eq_(self.adunit.get_pub_id("jumptap"), "account-jumptap")

    def mptest_add_adunit(self):
        self.adunit_network_config = NetworkConfig(
                                jumptap_pub_id="adunit-jumptap")
        self.adunit_network_config.put()
        
        self.adunit.network_config = self.adunit_network_config
        self.adunit.put()
        
        eq_(self.adunit.get_pub_id("jumptap"), "adunit-jumptap")
        
        
        
        


