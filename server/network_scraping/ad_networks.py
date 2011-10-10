from network_scraping import query_managers
from network_scraping.admob_scraper import AdMobScraper
from network_scraping.iad_scraper import IAdScraper
from network_scraping.jumptap_scraper import JumpTapScraper
from network_scraping.inmobi_scraper import InMobiScraper
from network_scraping.mobfox_scraper import MobFoxScraper


class AdNetwork(object):
    def __init__(self, constructor, get_pub_id):
        self.constructor = constructor
        self.get_pub_id = get_pub_id

# dictionary of supported ad networks
ad_networks = {'admob' : AdNetwork(constructor = AdMobScraper, get_pub_id = query_managers.get_pub_id),
            'jumptap' : AdNetwork(constructor = JumpTapScraper, get_pub_id = query_managers.get_pub_id_from_name),
            'iad' : AdNetwork(constructor = IAdScraper, get_pub_id = query_managers.get_pub_id),
            'inmobi' : AdNetwork(constructor = InMobiScraper, get_pub_id = query_managers.get_pub_id),
            'mobfox' : AdNetwork(constructor = MobFoxScraper, get_pub_id = query_managers.get_pub_id)}