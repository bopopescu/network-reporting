import logging
from copy import copy

from ad_network_reports.query_managers import \
        AdNetworkReportManager
from ad_network_reports.scrapers.admob_scraper import AdMobScraper
from ad_network_reports.scrapers.iad_scraper import IAdScraper
from ad_network_reports.scrapers.inmobi_scraper import InMobiScraper
from ad_network_reports.scrapers.jumptap_scraper import JumpTapScraper
from ad_network_reports.scrapers.mobfox_scraper import MobFoxScraper
from Crypto.Cipher import AES

class AdNetwork(object):
    """Base class AdNetwork is a factory for subclasses."""
    def __new__(cls, login_credentials):
        return super(AdNetwork, cls).__new__(AD_NETWORKS[login_credentials.
            ad_network_name], login_credentials)

    def __init__(cls, login_credentials):
        cls.login_credentials = copy(login_credentials)

    def create_scraper(cls):
        return cls.scraper(cls.login_credentials)

    def append_extra_info(cls):
        pass

class AdMobAdNetwork(AdNetwork):
    scraper = AdMobScraper

class JumpTapAdNetwork(AdNetwork):
    scraper = JumpTapScraper

    def append_extra_info(self):
        """Get extra information required for the Jumptap scraper.

        Return app level publisher ids and adunit level publisher ids appended
        to login credentials.
        """
        super(self.__class__, self).append_extra_info()
        account = self.login_credentials.account
        self.login_credentials = (self.login_credentials, [mapper.publisher_id
            for mapper in self.login_credentials.ad_network_app_mappers])

class IAdAdNetwork(AdNetwork):
    scraper = IAdScraper

class InMobiAdNetwork(AdNetwork):
    scraper = InMobiScraper

class MobFoxAdNetwork(AdNetwork):
    scraper = MobFoxScraper

    def append_extra_info(self):
        """Get extra information required for the Mobfox scraper.

        Return app level publisher ids appended to login credentials.
        """
        super(self.__class__, self).append_extra_info()
        account = self.login_credentials.account
        self.login_credentials = (self.login_credentials, [mapper.publisher_id
            for mapper in self.login_credentials.ad_network_app_mappers])

# dictionary of supported ad networks
AD_NETWORKS = {'admob' : AdMobAdNetwork,
               'jumptap' : JumpTapAdNetwork,
               'iad' : IAdAdNetwork,
               'inmobi' : InMobiAdNetwork,
               'mobfox' : MobFoxAdNetwork}
