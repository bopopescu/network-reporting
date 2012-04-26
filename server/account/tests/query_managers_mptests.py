import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import new
import unittest
from nose.tools import eq_
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import testbed
from ad_server.optimizer import optimizer


from advertiser.models import AdGroup, Creative, Campaign

from account.models import Account

from publisher.models import App

import datetime

import logging

from account.query_managers import AccountQueryManager
  


class TestAccountQueryManager(unittest.TestCase):
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
        
        # Set up default models
        self.account = Account(company="awesomecorp")
        self.account.put()
        
        self.user1 = fake_user_factory("Long.Johnson@gmail.com")
        self.user2 = fake_user_factory("Don.Piano@mopub.com")
        # self.user1 = users.User("tomfeelslucky@gmail.com")
        # self.user2 = users.User("tom@mopub.com")
        # self.user1.put()
        # self.user2.put()
        
        self.app = App(account=self.account, name="Test App")
        self.app.put()
        
    def tearDown(self):
        self.testbed.deactivate()
    

    # def mptest_get_basic(self):
    #     # Create an account with the default user and put it in both memcache and the datastore
    #     account = AccountQueryManager.get_current_account(user=self.user1)
    #     
    #     eq_(account.company, "awesomecorp")
    #     
        
        
        
        
        
 
