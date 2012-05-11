import os, sys
from datetime import date, datetime

sys.path.append(os.environ['PWD'])
import unittest
from nose.tools import assert_almost_equal

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
from publisher.models import App

USERNAME = 'user'
PASSWORD = 'pass'
CLIENT_KEY = 'key'
NETWORK = 'network'
APP_NAME = 'app'
PUB_ID = 'pub_id'

TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)

REVENUE = 9594.91
ATTEMPTS = 5556480
IMPRESSIONS = 5555226
CPM = 1.73
FILL_RATE = .9998
CLICKS = 117950
CPC = .08
CTR = .0212
DELTA = 2

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
                                          ad_network_name=NETWORK,
                                          username=USERNAME,
                                          password=PASSWORD,
                                          client_key=CLIENT_KEY)
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

    def ad_network_app_mapper_mptest(self):
        acct = Account()
        acct.put()
        creds = AdNetworkLoginCredentials(account=acct,
                                          ad_network_name=NETWORK,
                                          username=USERNAME,
                                          password=PASSWORD,
                                          client_key=CLIENT_KEY)
        creds.put()
        app = App(name=APP_NAME)
        app.put()

        mapper1 = AdNetworkAppMapper(ad_network_name=NETWORK,
                publisher_id=PUB_ID,
                ad_network_login=creds,
                application=app)
        mapper1.put()
        mapper2 = AdNetworkAppMapper.get_by_publisher_id(PUB_ID,
                NETWORK)
        assert mapper1
        assert mapper2
        assert mapper1.key() == mapper2.key()

        assert mapper1.has_potential_errors()

        AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY).put()
        assert not mapper1.has_potential_errors()

    def ad_network_scrape_stats_mptest(self):
        acct = Account()
        acct.put()
        creds = AdNetworkLoginCredentials(account=acct,
                                          ad_network_name=NETWORK,
                                          username=USERNAME,
                                          password=PASSWORD,
                                          client_key=CLIENT_KEY)
        creds.put()
        app = App(name=APP_NAME)
        app.put()

        mapper = AdNetworkAppMapper(ad_network_name=NETWORK,
                publisher_id=PUB_ID,
                ad_network_login=creds,
                application=app)
        mapper.put()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper,
                date=TODAY)
        stats1.put()
        assert stats1

        assert stats1.revenue == 0
        assert stats1.attempts == 0
        assert stats1.impressions == 0
        assert stats1.clicks == 0
        # Test properties too
        assert stats1.cpm == 0
        assert stats1.fill_rate == 0
        assert stats1.cpc == 0
        assert stats1.ctr == 0

        # Set stats properties to test values
        stats1.revenue = REVENUE
        stats1.attempts = ATTEMPTS
        stats1.impressions = IMPRESSIONS
        stats1.clicks = CLICKS

        # Sanity checks
        assert stats1.revenue == REVENUE
        assert stats1.attempts == ATTEMPTS
        assert stats1.impressions == IMPRESSIONS
        assert stats1.clicks == CLICKS
        # Test properties too
        assert_almost_equal(stats1.cpm, CPM, DELTA)
        assert_almost_equal(stats1.fill_rate, FILL_RATE, DELTA)
        assert_almost_equal(stats1.cpc, CPC, DELTA)
        assert_almost_equal(stats1.ctr, CTR, DELTA)

        stats2 = AdNetworkScrapeStats.get_by_app_mapper_and_day(mapper,
                TODAY)
        assert stats2

        assert stats1.key() == stats2.key()

        stats3 = AdNetworkScrapeStats.get_by_app_mapper_and_day(mapper,
                YESTERDAY)
        assert not stats3

        stats4 = AdNetworkScrapeStats.get_by_app_mapper_and_days(mapper,
                [TODAY])[0]
        assert stats4

        stats5 = AdNetworkScrapeStats.get_by_app_mapper_and_days(mapper,
                [YESTERDAY])[0]
        assert stats5
        # Stats that don't exist for certain days should be created and set
        # to 0
        assert stats5.revenue == 0
        assert stats5.attempts == 0
        assert stats5.impressions == 0
        assert stats5.clicks == 0

        stats_list, sync_date = AdNetworkScrapeStats. \
                get_by_app_mapper_and_days(mapper.key(), [TODAY, YESTERDAY],
                        include_last_day=True)
        assert sync_date == TODAY
        stats6 = stats_list[0]
        stats7 = stats_list[1]
        assert stats6.key() == stats1.key()
        assert stats7.revenue == 0
        assert stats7.attempts == 0
        assert stats7.impressions == 0
        assert stats7.clicks == 0

