import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup
import logging

from datetime import date, datetime, timedelta

from google.appengine.ext import testbed

from account.models import Account
from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkScrapeStats, \
     AdNetworkManagementStats

USERNAME = 'user1'
PASSWORD = 'pass1'

class TestModels(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def login_credentials_mptest(self):
        """
        Create fake login credentials and verify that encryption works.
        """
        # Create default models.
        acct = Account()
        acct.put()
        creds = AdNetworkLoginCredentials(account=acct,
                                          ad_network_name='network1',
                                          username=USERNAME,
                                          password=PASSWORD,
                                          client_key='key1')
        creds.put()

        # Make sure iv's have been set.
        assert getattr(creds, 'username_iv', None)
        assert getattr(creds, 'password_iv', None)

        # Verify that username and password have been encrypted.
        assert creds._username != USERNAME
        assert creds._password != PASSWORD

        # Verify that decryption works.
        assert creds.username == USERNAME
        assert creds.password == PASSWORD

