import logging
import os, sys

EC2 = False

if EC2:
    sys.path.append('/home/ubuntu/mopub_experimental/server')
    sys.path.append('/home/ubuntu/google_appengine')
    sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
    sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
    sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
    sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
    sys.path.append('/home/ubuntu/google_appengine/lib/webob')
    sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')
else:
    # Assumes it is being called from server dir
    sys.path.append(os.environ['PWD'])

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from datetime import date, timedelta

from account.models import NetworkConfig

from network_scraping.models import *
from network_scraping.admob_scraper import AdMobScraper
from network_scraping.iad_scraper import IAdScraper
from network_scraping.jumptap_scraper import JumpTapScraper
from network_scraping.inmobi_scraper import InMobiScraper
from network_scraping.mobfox_scraper import MobFoxScraper
from network_scraping.network_scrape_record import NetworkScrapeRecord

import network_scraping.query_managers

from publisher.models import App

import network_scraping.query_managers

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-experimental'
    host = '38.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

def auth_func():
    return 'olp@mopub.com', 'N47935'

class Network(object):
    def __init__(self, constructor, get_pub_id):
        self.constructor = constructor
        self.get_pub_id = get_pub_id

# dictionary of Networks
networks = {'admob' : Network(constructor = AdMobScraper, get_pub_id = get_pub_id),
            'jumptap' : Network(constructor = JumpTapScraper, get_pub_id = get_jump_tap_pub_id),
            'iad' : Network(constructor = IAdScraper, get_pub_id = get_pub_id),
            'inmobi' : Network(constructor = InMobiScraper, get_pub_id = get_pub_id),
            'mobfox' : Network(constructor = MobFoxScraper, get_pub_id = get_pub_id)}

def update_ad_networks():
    yesterday = date.today() - timedelta(days = 1)

    # log in to ad networks and update stats for each user 
    for login_info in AdNetworkLoginInfo.all():

        scraper = networks[login_info.ad_network_name].constructor(login_info)

        # returns a list of NetworkScrapeRecord objects of stats for each app for yesterday
        stats_list = scraper.get_site_stats(yesterday)

        for stats in stats_list:
    
            ''' Add the current day to the db '''
            
            publisher_id = networks[login_info.ad_network_name].get_pub_id(stats.app_tag, login_info)
            
            # Using GQL to get the ad_network object that corresponds to the login_info and stats
            manager = AdNetworkReportQueryManager(login_info.account)
            ad_network = manager.get_ad_network_app_mapper(publisher_id = publisher_id,
                                                           login_info = login_info)
            
            if ad_network is None:
                # App is not registered in MoPub but is still in the ad network
                logging.info('%(account)s has pub id %(pub_id)s on %(ad_network)s that\'s NOT in MoPub' %
                             dict(account = login_info.account.title,
                                  pub_id = stats.app_tag,
                                  ad_network = login_info.ad_network_name))
                continue
            else:
                logging.info('%(account)s has pub id %(pub_id)s on %(ad_network)s that\'s in MoPub' %
                             dict(account = login_info.account.title,
                                  pub_id = stats.app_tag,
                                  ad_network = login_info.ad_network_name))
        
            AdNetworkScrapeStats(ad_network_app_mapper = ad_network,
                                 date = yesterday,
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
                
if __name__ == "__main__":
    setup_remote_api()
    update_ad_networks()                
                
