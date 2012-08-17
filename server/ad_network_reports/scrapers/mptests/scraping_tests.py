"""
NOTE: Since these are so expensive they are not run by usual nose tests
"""

import os, sys
sys.path.append(os.environ['PWD'])
import unittest

# magic test import
import common.utils.test.setup
import logging

from datetime import date, datetime, timedelta

from google.appengine.ext import testbed

from ad_network_reports.scrapers.admob_scraper import AdMobScraper
from ad_network_reports.scrapers.jumptap_scraper import JumpTapScraper
from ad_network_reports.scrapers.iad_scraper import IAdScraper
from ad_network_reports.scrapers.inmobi_scraper import InMobiScraper
from ad_network_reports.scrapers.mobfox_scraper import MobFoxScraper

class NetworkConfidential(object):
    pass

class TestScrapers(unittest.TestCase):
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
        nc.username = 'chesscom'
        nc.password = 'Y7u8i9o0'

        publisher_ids = ['pa_chess_com_llc_chess_com_-_pla_iph_app',
                'pa_chess_com_llc_chess_com_-_and_drd_app']

        nc.ad_network_name = 'jumptap'

        adunit_publisher_ids = iter([])
        scraper = JumpTapScraper((nc, publisher_ids, adunit_publisher_ids))
        scraper.get_site_stats(date.today() - timedelta(days = 1))

    def iad_mptest(self):
        nc = NetworkConfidential()
        nc.username = '2_acrossair@acrossair.com'
        nc.password = 'imano@314'
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

