import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup

from datetime import date, datetime, timedelta

from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager
from ad_network_reports.update_ad_networks import update_ad_networks
from common.utils import date_magic
from pytz import timezone
from google.appengine.ext import testbed

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkScrapeStats, \
     AdNetworkManagementStats
from ad_network_reports.mptests.load_test_data import load_test_data

# TODO: Improve testing
class TestUpdate(unittest.TestCase):
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

    def ad_network_reports_mptest(self):
        # Create default models.
        account = load_test_data()

        # Call the method we are testing.
        update_ad_networks()

        test_network_app_mappers = list(AdNetworkMapperManager.
                get_ad_network_mappers(account))
        print 'App Mapper\'s len: %d' % len(test_network_app_mappers)
        assert len(test_network_app_mappers) > 0

        # Was a day created for each app for the account?
        pacific = timezone('US/Pacific')
        yesterday = (datetime.now(pacific) - timedelta(days=1)).date()
        print "YESTERDAY: %s" % yesterday.strftime('%Y %m %d')
        for mapper1 in test_network_app_mappers:
            mapper2 = AdNetworkMapperManager.get_ad_network_mapper(
                    ad_network_app_mapper_key=mapper1.key())
            stats = AdNetworkStatsManager.get_stats_list_for_mapper_and_days(
                    mapper1.key(), [yesterday])
            if mapper2.application:
                print "network name:%s application name: %s" % \
                        (mapper2.ad_network_name, mapper2.application.name)
            else:
                print "network name:%s" % mapper2.ad_network_name
            print stats[0].__dict__
            assert stats[0].date == yesterday

