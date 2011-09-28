import logging
import os, sys
sys.path.append(os.environ['PWD'])

from datetime import date

from account.models import NetworkConfig

from network_scraping.models import *
from network_scraping.admob_scraper import AdMobScraper
from network_scraping.iad_scraper import IAdScraper
from network_scraping.jumptap_scraper import JumpTapScraper
from network_scraping.network_scrape_record import NetworkScrapeRecord

from publisher.models import App

def get_pub_id(pub_id, login_info):
    return pub_id

def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter("name =", app_name)
    query.filter("account =", login_info.account)
    publisher_id = query.get()
    
    if publisher_id:
        return publisher_id.network_config.jumptap_pub_id
    else:
        return None

class Network:
    def __init__(self, constructor, get_pub_id):
        self.constructor = constructor
        self.get_pub_id = get_pub_id

# dictionary of Networks
networks = {'admob' : Network(constructor = AdMobScraper, get_pub_id = get_pub_id),
            'jumptap' : Network(constructor = JumpTapScraper, get_pub_id = get_jump_tap_pub_id),
            'iad' : Network(constructor = IAdScraper, get_pub_id = get_pub_id)}

def update_ad_networks():
    today = date.today()

    # log in to ad networks and update stats for each user 
    for login_info in AdNetworkLoginInfo.all():

        scraper = networks[login_info.ad_network_name].constructor(login_info)

        # returns a list of NetworkScrapeRecord objects of stats for each app for today
        stats_list = scraper.get_site_stats(today)

        for stats in stats_list:
    
            ''' Add the current day to the db '''
            
            publisher_id = networks[login_info.ad_network_name].get_pub_id(stats.app_tag, login_info)
            
            # Using GQL to get the ad_network object that corresponds to the login_info and stats
            query = AdNetworkAppMapper.all()
            query.filter("ad_network_login =", login_info)
            query.filter("publisher_id =", publisher_id)
            ad_network = query.get()
            
            if ad_network is None:
                # App is not registered in MoPub but is still in the ad network
                logging.info('%(account)s has pub id %(pub_id)s on %(ad_network)s that\'s NOT in MoPub' %
                             dict(account = login_info.account.title, pub_id = stats.app_tag, ad_network = login_info.ad_network_name))
                continue
            else:
                logging.info('%(account)s has pub id %(pub_id)s on %(ad_network)s that\'s in MoPub' %
                             dict(account = login_info.account.title, pub_id = stats.app_tag, ad_network = login_info.ad_network_name))
        
            AdNetworkScrapeStats(ad_network_app_mapper = ad_network,
                                 attempts = stats.attempts,
                                 impressions = stats.impressions,
                                 fill_rate = float(stats.fill_rate),
                                 clicks = stats.clicks,
                                 ctr = float(stats.ctr),
                                 ecpm = float(stats.ecpm)
                                 ).put()

            ''' Update the aggregate '''
            
            old_impressions_total = ad_network.impressions
    
            ad_network.attempts += stats.attempts
            ad_network.impressions += stats.impressions
            if ad_network.attempts != 0:
                ad_network.fill_rate = ad_network.impressions / float(ad_network.attempts)
            else:
                ad_network.fill_rate = float('NaN')
            ad_network.clicks += stats.clicks
            if ad_network.impressions != 0:
                ad_network.ctr = ad_network.clicks / float(ad_network.impressions)
                ad_network.ecpm = (ad_network.ecpm * old_impressions_total + stats.ecpm * stats.impressions) / float(ad_network.impressions)
            else:
                ad_network.ctr = float('NaN')
                ad_network.ecpm = float('NaN')