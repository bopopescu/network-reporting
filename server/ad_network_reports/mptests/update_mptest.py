import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup
import logging

from datetime import date, datetime, timedelta

from ad_network_reports.query_managers import AdNetworkReportQueryManager
from ad_network_reports.update_ad_networks import update_ad_networks
from common.utils import date_magic
from pytz import timezone
from google.appengine.ext import testbed

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkScrapeStats, \
     AdNetworkManagementStats
from ad_network_reports.mptests.load_test_data import load_test_data

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

        # Verify results.
        manager = AdNetworkReportQueryManager(account)

        test_network_app_mappers = list(manager.get_ad_network_mappers())
        logging.info('App Mapper\'s len: %d' % len(test_network_app_mappers))
        assert len(test_network_app_mappers) > 0
        #assert len(test_network_app_mappers) == len(entities)

        logging.warning([a.key().name for a in test_network_app_mappers])

        # Was a day created for each app for the account?
        pacific = timezone('US/Pacific')
        yesterday = (datetime.now(pacific) - timedelta(days=1)).date()
        logging.info("YESTERDAY: %s" % yesterday.strftime('%Y %m %d'))
        for n in test_network_app_mappers:
            n = manager.get_ad_network_mapper(ad_network_app_mapper_key =
                    n.key())
            stats = manager.get_stats_list_for_mapper_and_days(n.key(), [yesterday])
            if n.application:
                logging.warning( "network name:%s application name: %s" %
                        (n.ad_network_name, n.application.name))
            else:
                logging.warning( "network name:%s" % n.ad_network_name)
            logging.warning(str(stats[0].__dict__))
            assert stats[0].date == yesterday

        # Do aggregate statistics work?
        aggregates, daily_stats, networks, apps = manager.get_index_data(
                date_magic.gen_days(date.today() - timedelta(days=8),
                    date.today() - timedelta(days=1)))
        logging.info(manager.get_chart_stats_for_all_networks(date_magic.gen_days(
            date.today() - timedelta(days=8), date.today() - timedelta(days=1))))

