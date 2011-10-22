from ad_network_reports.query_managers import AdNetworkReportQueryManager
from ad_network_reports.scrapers.admob_scraper import AdMobScraper
from ad_network_reports.scrapers.iad_scraper import IAdScraper
from ad_network_reports.scrapers.inmobi_scraper import InMobiScraper
from ad_network_reports.scrapers.jumptap_scraper import JumpTapScraper
from ad_network_reports.scrapers.mobfox_scraper import MobFoxScraper

class AdNetwork(object):
    def __init__(self, constructor, append_extra_info):
        self.constructor = constructor
        self.append_extra_info = append_extra_info

def append_extra_info(login_credentials):
    """Allow for generic scraping approach to work.

    Return login credentials.
    """
    return login_credentials

def append_extra_mobfox_info(login_credentials):
    """Get extra information required for the Mobfox scraper.

    Return app level publisher ids appended to login credentials.
    """
    manager = AdNetworkReportQueryManager(login_credentials.account)
    return (login_credentials, manager.get_app_publisher_ids(login_credentials.
        ad_network_name))

def append_extra_jumptap_info(login_credentials):
    """Get extra information required for the Jumptap scraper.

    Return app level publisher ids and adunit level publisher ids appended to
    login credentials.
    """
    manager = AdNetworkReportQueryManager(login_credentials.account)
    return (login_credentials, manager.get_app_publisher_ids(login_credentials
        .ad_network_name), manager.get_adunit_publisher_ids(login_credentials.
            ad_network_name))

# dictionary of supported ad networks
AD_NETWORKS = {'admob' : AdNetwork(constructor=AdMobScraper,
                                append_extra_info=append_extra_info),
               'jumptap' : AdNetwork(constructor=JumpTapScraper,
                                append_extra_info=append_extra_jumptap_info),
               'iad' : AdNetwork(constructor = IAdScraper,
                                append_extra_info=append_extra_info),
               'inmobi' : AdNetwork(constructor = InMobiScraper,
                                append_extra_info=append_extra_info),
               'mobfox' : AdNetwork(constructor = MobFoxScraper,
                                append_extra_info=append_extra_mobfox_info)}
