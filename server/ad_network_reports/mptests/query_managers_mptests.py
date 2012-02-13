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
     AdNetworkNetworkStats, \
     AdNetworkAppStats, \
     AdNetworkManagementStats
from ad_network_reports.query_managers import AdNetworkAggregateManager
from publisher.models import App

USERNAME = 'user'
PASSWORD = 'pass'
CLIENT_KEY = 'key'

NETWORK1 = 'network1'
APP_NAME1 = 'app1'
PUB_ID1 = 'pub_id1'
NETWORK2 = 'network2'
APP_NAME2 = 'app2'
PUB_ID2 = 'pub_id2'

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

    def ad_network_network_stats_basic_put_mptest(self):
        acct, mapper1, mapper2 = setup_network_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)
        stats1.put()
        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper2,
                date=TODAY)
        stats2.put()
        AdNetworkAggregateManager.create_stats(acct, TODAY, [stats1, stats2],
                network=NETWORK1).put()
        network_stats = AdNetworkNetworkStats.get_by_network_and_day(acct,
                                                                     NETWORK1,
                                                                     TODAY)
        assert network_stats

        assert network_stats.revenue == 0
        assert network_stats.attempts == 0
        assert network_stats.impressions == 0
        assert network_stats.clicks == 0
        # Test properties too
        assert network_stats.cpm == 0
        assert network_stats.fill_rate == 0
        assert network_stats.cpc == 0
        assert network_stats.ctr == 0

    def ad_network_app_stats_basic_put_mptest(self):
        acct, app, mapper1, mapper2 = setup_app_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)
        stats1.put()
        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper2,
                date=TODAY)
        stats2.put()
        AdNetworkAggregateManager.create_stats(acct, TODAY, [stats1, stats2],
                app=app).put()
        app_stats = AdNetworkAppStats.get_by_app_and_day(acct,
                                                         app,
                                                         TODAY)
        assert app_stats

        assert app_stats.revenue == 0
        assert app_stats.attempts == 0
        assert app_stats.impressions == 0
        assert app_stats.clicks == 0
        # Test properties too
        assert app_stats.cpm == 0
        assert app_stats.fill_rate == 0
        assert app_stats.cpc == 0
        assert app_stats.ctr == 0

    def ad_network_network_stats_put_mptest(self):
        acct, mapper1, mapper2 = setup_network_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)
        stats1.put()
        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper2,
                date=TODAY)

        # Set stats properties to test values
        stats2.revenue = REVENUE
        stats2.attempts = ATTEMPTS
        stats2.impressions = IMPRESSIONS
        stats2.clicks = CLICKS

        stats2.put()
        AdNetworkAggregateManager.create_stats(acct, TODAY, [stats1, stats2],
                network=NETWORK1).put()
        network_stats = AdNetworkNetworkStats.get_by_network_and_day(acct,
                                                                     NETWORK1,
                                                                     TODAY)
        assert network_stats

        assert network_stats.revenue == REVENUE
        assert network_stats.attempts == ATTEMPTS
        assert network_stats.impressions == IMPRESSIONS
        assert network_stats.clicks == CLICKS
        # Test properties too
        assert_almost_equal(network_stats.cpm, CPM, DELTA)
        assert_almost_equal(network_stats.fill_rate, FILL_RATE, DELTA)
        assert_almost_equal(network_stats.cpc, CPC, DELTA)
        assert_almost_equal(network_stats.ctr, CTR, DELTA)

    def ad_network_app_stats_put_mptest(self):
        acct, app, mapper1, mapper2 = setup_app_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)
        stats1.put()
        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper2,
                date=TODAY)

        # Set stats properties to test values
        stats2.revenue = REVENUE
        stats2.attempts = ATTEMPTS
        stats2.impressions = IMPRESSIONS
        stats2.clicks = CLICKS

        stats2.put()

        AdNetworkAggregateManager.create_stats(acct, TODAY, [stats1, stats2],
                app=app).put()
        app_stats = AdNetworkAppStats.get_by_app_and_day(acct,
                                                         app,
                                                         TODAY)

        assert app_stats

        assert app_stats.revenue == REVENUE
        assert app_stats.attempts == ATTEMPTS
        assert app_stats.impressions == IMPRESSIONS
        assert app_stats.clicks == CLICKS
        # Test properties too
        assert_almost_equal(app_stats.cpm, CPM, DELTA)
        assert_almost_equal(app_stats.fill_rate, FILL_RATE, DELTA)
        assert_almost_equal(app_stats.cpc, CPC, DELTA)
        assert_almost_equal(app_stats.ctr, CTR, DELTA)

    def ad_network_network_stats_update_mptest(self):
        acct, mapper1, mapper2 = setup_network_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)

        # Set stats properties to test values
        stats1.revenue = REVENUE
        stats1.attempts = ATTEMPTS
        stats1.impressions = IMPRESSIONS
        stats1.clicks = CLICKS

        # Update stats
        AdNetworkAggregateManager.update_stats(acct, mapper1, TODAY, stats1,
                network=NETWORK1)
        stats1.put()

        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)

        # Set stats properties to test values
        stats2.revenue = REVENUE
        stats2.attempts = ATTEMPTS
        stats2.impressions = IMPRESSIONS
        stats2.clicks = CLICKS

        # Update stats
        AdNetworkAggregateManager.update_stats(acct, mapper1, TODAY, stats2,
                network=NETWORK1)
        stats2.put()

        network_stats = AdNetworkNetworkStats.get_by_network_and_day(acct,
                                                                     NETWORK1,
                                                                     TODAY)
        assert network_stats

        assert network_stats.revenue == REVENUE
        assert network_stats.attempts == ATTEMPTS
        assert network_stats.impressions == IMPRESSIONS
        assert network_stats.clicks == CLICKS

    def ad_network_app_stats_update_mptest(self):
        acct, app, mapper1, mapper2 = setup_app_models()

        stats1 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)

        # Set stats properties to test values
        stats1.revenue = REVENUE
        stats1.attempts = ATTEMPTS
        stats1.impressions = IMPRESSIONS
        stats1.clicks = CLICKS

        # Update stats
        AdNetworkAggregateManager.update_stats(acct, mapper1, TODAY, stats1,
                app=app)
        stats1.put()

        stats2 = AdNetworkScrapeStats(ad_network_app_mapper=mapper1,
                date=TODAY)

        stats2.revenue = REVENUE
        stats2.attempts = ATTEMPTS
        stats2.impressions = IMPRESSIONS
        stats2.clicks = CLICKS

        # Update stats
        AdNetworkAggregateManager.update_stats(acct, mapper1, TODAY, stats2,
                app=app)
        stats2.put()

        app_stats = AdNetworkAppStats.get_by_app_and_day(acct,
                                                         app,
                                                         TODAY)

        assert app_stats

        assert app_stats.revenue == REVENUE
        assert app_stats.attempts == ATTEMPTS
        assert app_stats.impressions == IMPRESSIONS
        assert app_stats.clicks == CLICKS

def setup_network_models():
    acct = Account()
    acct.put()
    creds = AdNetworkLoginCredentials(account=acct,
                                      ad_network_name=NETWORK1,
                                      username=USERNAME,
                                      password=PASSWORD,
                                      client_key=CLIENT_KEY)
    creds.put()
    app1 = App(name=APP_NAME1)
    app1.put()

    mapper1 = AdNetworkAppMapper(ad_network_name=NETWORK1,
            publisher_id=PUB_ID1,
            ad_network_login=creds,
            application=app1)
    mapper1.put()

    app2 = App(name=APP_NAME2)
    app2.put()

    mapper2 = AdNetworkAppMapper(ad_network_name=NETWORK1,
            publisher_id=PUB_ID2,
            ad_network_login=creds,
            application=app2)
    mapper2.put()
    return (acct, mapper1, mapper2)

def setup_app_models():
    acct = Account()
    acct.put()
    creds1 = AdNetworkLoginCredentials(account=acct,
                                      ad_network_name=NETWORK1,
                                      username=USERNAME,
                                      password=PASSWORD,
                                      client_key=CLIENT_KEY)
    creds1.put()
    creds2 = AdNetworkLoginCredentials(account=acct,
                                      ad_network_name=NETWORK2,
                                      username=USERNAME,
                                      password=PASSWORD,
                                      client_key=CLIENT_KEY)
    creds2.put()
    app = App(name=APP_NAME1)
    app.put()

    mapper1 = AdNetworkAppMapper(ad_network_name=NETWORK1,
            publisher_id=PUB_ID1,
            ad_network_login=creds1,
            application=app)
    mapper1.put()

    mapper2 = AdNetworkAppMapper(ad_network_name=NETWORK2,
            publisher_id=PUB_ID2,
            ad_network_login=creds2,
            application=app)
    mapper2.put()
    return (acct, app, mapper1, mapper2)

