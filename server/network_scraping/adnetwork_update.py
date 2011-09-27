import logging
import os, sys
sys.path.append(os.environ['PWD'])

from datetime import date
import simplejson as json

from account.models import NetworkConfig

from network_scraping.models import *
from network_scraping.admob_scraper import AdMobScraper
from network_scraping.jumptap_scraper import JumpTapScraper
from network_scraping.network_scrape_record import NetworkScrapeRecord

from publisher.models import App

class Network:
    def __init__(self, constructor):
        self.constructor = constructor

# dictionary of Networks
networks = {'admob' : Network(constructor = AdMobScraper, get_pub_id = get_pub_id),
            'jumptap' : Network(constructor = JumpTapScraper, get_pub_id = get_jump_tap_pub_id)}

def update_ad_networks():
    today = date.today()

    # log in to ad networks and update stats for each user 
    for login_info in AdNetworkLoginInfo.all():

        scraper = networks[login_info.ad_network].constructor(json.loads(login_info.dictionary))

        # returns a list of NetworkScrapeRecord objects of stats for each app for today
        stats_list = scraper.get_site_stats(today)

        for stats in stats_list:
    
            # Add the current day to the db
            # Using GQL to get the ad_network object that corresponds to the login_info
            query = AdNetworkAppsMapper.all()
            # query on stats.publisher_id, adnetwork, account
            query.filter("ad_network_login =", login_info)
            query.filter("publisher_id =", stats.publisher_id)
            ad_network = query.get()
            
            if ad_network is None:
                # App is not registered in our network but is still in ad_network
                logging.info('%(account)s has app %(app)s on %(ad_network)s that\'s not in MoPub' %
                             dict(account = login_info.account, app = stats.app_name, ad_network = login_info.ad_network))
                continue
        
            AdNetworkScrapeStats(ad_network = ad_network,
                                 attempts = stats.attempts,
                                 impressions = stats.impressions,
                                 fill_rate = float(stats.fill_rate),
                                 clicks = stats.clicks,
                                 ctr = float(stats.ctr),
                                 ecpm = float(stats.ecpm)
                                 ).put()

            # Update the aggregate
            old_impressions_total = ad_network.impressions
    
            ad_network.attempts += stats.attempts
            ad_network.impressions += stats.impressions
            ad_network.fill_rate = ad_network.impressions / float(ad_network.attempts)
            ad_network.clicks += stats.clicks
            ad_network.ctr = ad_network.clicks / float(ad_network.impressions)
            ad_network.ecpm = (ad_network.ecpm * old_impressions_total + stats.ecpm * stats.impressions) / float(ad_network.impressions)
            
def get_pub_id(pub_id):
    return pub_id
    
def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter("name =", app_name)
    query.filter("account =", account)
    return query.get().network_config.jumptap_pub_id