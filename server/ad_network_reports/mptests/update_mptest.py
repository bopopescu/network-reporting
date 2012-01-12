import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup

from datetime import date, datetime, timedelta

from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager
from ad_network_reports.update_ad_networks import update_all, \
        multiprocess_update_all
from common.utils import date_magic
from pytz import timezone
from google.appengine.ext import testbed

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkScrapeStats, \
     AdNetworkManagementStats
from ad_network_reports.mptests.load_test_data import load_test_data

INCLUDE_IAD = False

# TODO: Improve update testing
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

    def update_all_mptest(self):
        # Create default models.
        account = load_test_data(include_iad=INCLUDE_IAD)

        # Call the method we are testing.
        update_all()

        test_network_app_mappers = list(AdNetworkMapperManager.
                get_mappers(account))
        print 'App Mapper\'s len: %d' % len(test_network_app_mappers)
        assert len(test_network_app_mappers) > 0

        # Was a day created for each app for the account?
        pacific = timezone('US/Pacific')
        yesterday = (datetime.now(pacific) - timedelta(days=1)).date()
        print "YESTERDAY: %s" % yesterday.strftime('%Y %m %d')
        for mapper1 in test_network_app_mappers:
            mapper2 = AdNetworkMapperManager.get_ad_network_mapper(
                    ad_network_app_mapper_key=mapper1.key())
            stats = AdNetworkScrapeStats.all().filter('ad_network_app_mapper =',
                    mapper1).filter('date =', yesterday).get()
            if mapper2.application:
                print "network name:%s application name: %s" % \
                        (mapper2.ad_network_name, mapper2.application.name)
            else:
                print "network name:%s" % mapper2.ad_network_name
            print stats.__dict__
            assert stats.date == yesterday

    def multiprocess_update_all_mptest(self):
        # Create default models.
        account = load_test_data(include_iad=INCLUDE_IAD)

        # Call the method we are testing.
        multiprocess_update_all(processes=3)

        test_network_app_mappers = list(AdNetworkMapperManager.
                get_mappers(account))
        print 'App Mapper\'s len: %d' % len(test_network_app_mappers)
        assert len(test_network_app_mappers) > 0

        # TODO: figure out a way to verify data that spawned processes created

