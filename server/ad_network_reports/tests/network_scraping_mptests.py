import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup
import logging

from google.appengine.ext import db

from datetime import date, datetime, timedelta
from sets import Set

from ad_network_reports.query_managers import AdNetworkReportQueryManager
from ad_network_reports.update_ad_networks import update_ad_networks
from account.models import Account, NetworkConfig
from common.utils import date_magic
from publisher.models import App
from pytz import timezone
from google.appengine.ext import testbed

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkScrapeStats, \
     AdNetworkManagementStats
from ad_network_reports.tests.load_test_data import load_test_data
from ad_network_reports.scrapers.admob_scraper import AdMobScraper
from ad_network_reports.scrapers.jumptap_scraper import JumpTapScraper
from ad_network_reports.scrapers.iad_scraper import IAdScraper
from ad_network_reports.scrapers.inmobi_scraper import InMobiScraper
from ad_network_reports.scrapers.mobfox_scraper import MobFoxScraper

import ad_network_reports.query_managers

TEST_JUMPTAP_PUB_ID = '12345'
TEST_ADMOB_PUB_ID = 'a14a9ed9bf1fdcd'
TEST_IAD_PUB_ID = '362641118' # NOT IN NetworkConfig
TEST_INMOBI_PUB_ID ='4028cb962b75ff06012b792fc5fb0045'
TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

class NetworkConfidential(object):
    pass

class TestAccountQueryManager(unittest.TestCase):
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

    def admob_mptest(self):
        nc = NetworkConfidential()
        nc.username = 'adnetwork@com2usamerica.com'
        nc.password = '4w47m82l5jfdqw1x'
        nc.client_key = 'ka820827f7daaf94826ce4cee343837a'
        nc.ad_network_name = 'admob'
        scraper = AdMobScraper(nc)
        scraper.get_site_stats(date.today() - timedelta(days=1))

    def jumptap_mptest(self):
        nc = NetworkConfidential()
        nc.username = 'com2ususa'
        nc.password = 'com2us1001'
        publisher_ids = [u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app',
                u'pa_com2us_usa_inc__slice_it__drd_app']
        adunit_publisher_ids = iter([
            u'pa_com2us_usa_inc__op_3d_lab_a_tes_drd_app_banner',
            u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app_home_me_banner',
            u'pa_com2us_usa_inc__op_3d_lab_i_tes_iph_app_home_me_medrect',
            u'pa_com2us_usa_inc_slice_it_drd_app_banner',
            u'pa_com2us_usa_inc__slice_it__drd_app_banner2'])
        #iter([])
        nc.ad_network_name = 'jumptap'
        scraper = JumpTapScraper((nc, publisher_ids, adunit_publisher_ids))
        scraper.get_site_stats(date.today() - timedelta(days = 1))

    def iad_mptest(self):
        nc = NetworkConfidential()
        nc.username = 'chesscom'
        nc.password = 'Faisal1Chess'
        nc.ad_network_name = 'iad'
        scraper = IAdScraper(nc)
        scraper.get_site_stats(date.today() - timedelta(days = 1))

    def inmobi_mptest(self):
        nc = NetworkConfidential()
        # access_id
        nc.username = '4028cb972fe21753012ffb7680350267'
        # secret_key
        nc.password = '0588884947763'
        nc.ad_network_name = 'inmobi'
        scraper = InMobiScraper(nc)
        scraper.get_site_stats(date.today() - timedelta(days=1))

    def mobfox_mptest(self):
        nc = NetworkConfidential()
        publisher_ids = ['ddcc935d2bc034b2823e04b24ff544a9',
                'e884e3c21a498d57f7d1cb1400c5ab9b']
        scraper = MobFoxScraper((nc, publisher_ids))
        scraper.get_site_stats(date.today() - timedelta(days=1))

    def ad_network_reports_mptest(self):
        # Create default models.
        account = load_test_data()

        # Call the method we are testing.
        update_ad_networks()

        # Verify results.
        manager = AdNetworkReportQueryManager(account)

        test_network_app_mappers = list(manager.get_ad_network_mappers())
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
