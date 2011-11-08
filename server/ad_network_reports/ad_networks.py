import logging

from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        KEY
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
        cls.login_credentials = login_credentials

    def create_scraper(cls):
        return cls.scraper(cls.login_credentials)

    def append_extra_info(cls):
        """Decode password prior to sending it to the scarper."""
        if cls.login_credentials.password:
            password_aes_cfb = AES.new(KEY, AES.MODE_CFB, cls.
                    login_credentials.password_iv)
            cls.login_credentials.password = password_aes_cfb.decrypt(cls.
                    login_credentials.password)
        if cls.login_credentials.username:
            username_aes_cfb = AES.new(KEY, AES.MODE_CFB, cls.
                    login_credentials.username_iv)
            cls.login_credentials.username = username_aes_cfb.decrypt(cls.
                    login_credentials.username)

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
        manager = AdNetworkReportQueryManager(self.login_credentials.account)
        self.login_credentials = (self.login_credentials, manager.
                get_app_publisher_ids(self.login_credentials.ad_network_name),
                manager.get_adunit_publisher_ids(self.login_credentials.
                    ad_network_name))

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
        manager = AdNetworkReportQueryManager(self.login_credentials.account)
        self.login_credentials = (self.login_credentials, manager.
                get_app_publisher_ids(self.login_credentials.ad_network_name))

# dictionary of supported ad networks
AD_NETWORKS = {'admob' : AdMobAdNetwork,
               'jumptap' : JumpTapAdNetwork,
               'iad' : IAdAdNetwork,
               'inmobi' : InMobiAdNetwork,
               'mobfox' : MobFoxAdNetwork}
