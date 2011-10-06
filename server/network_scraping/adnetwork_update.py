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
    # Assumes it is being called from ./run_tests.sh from server dir
    sys.path.append(os.environ['PWD'])

from common.utils import date_magic

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.api import mail

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

from network_scraping.query_managers import *

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-experimental'
    host = '38.latest.mopub-experimental.appspot.com'
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

def update_ad_networks(start_date = None, end_date = None):
    yesterday = date.today() - timedelta(days = 1)
    
    if start_date is None and end_date is None:
        start_date = yesterday
        end_date = yesterday

    for test_date in date_magic.gen_days(start_date, end_date):
        # log in to ad networks and update stats for each user 
        for login_info in AdNetworkLoginInfo.all():

            scraper = networks[login_info.ad_network_name].constructor(login_info)

            # returns a list of NetworkScrapeRecord objects of stats for each app for the test_date
            try:
                stats_list = scraper.get_site_stats(test_date)
            except Exception:
                logging.error("Couldn't get get stats for %s network for %s account." % (login_info.ad_network_name, login_info.account.title))
                logging.error("Can try again later or perhaps %s changed it's API or site." % login_info.ad_network_name)
                pass

            for stats in stats_list:
    
                ''' Add the current day to the db '''
            
                publisher_id = networks[login_info.ad_network_name].get_pub_id(stats.app_tag, login_info)
            
                # Using GQL to get the ad_network_app_mapper object that corresponds to the login_info and stats
                manager = AdNetworkReportQueryManager(login_info.account)
                ad_network_app_mapper = manager.get_ad_network_app_mapper(publisher_id = publisher_id,
                                                               login_info = login_info)
            
                if ad_network_app_mapper is None:
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
        
                AdNetworkScrapeStats(ad_network_app_mapper = ad_network_app_mapper,
                                     date = test_date,
                                     revenue = float(stats.revenue),
                                     attempts = stats.attempts,
                                     impressions = stats.impressions,
                                     fill_rate = float(stats.fill_rate),
                                     clicks = stats.clicks,
                                     ctr = float(stats.ctr),
                                     ecpm = float(stats.ecpm)
                                     ).put()
                 
                # Only email publisher if they want email and the information is relevant (ie. yesterdays stats)
                if ad_network_app_mapper.send_email and test_date == yesterday:
                    mail.send_mail(sender='olp@mopub.com', 
                                   to='tiago@mopub.com',
                                   subject="Test Email", 
                                   body="""Scrape stats for %(test_date)s for application %(app)s:
                                           revenue: %(revenue).2f
                                           attempts: %(attempts)d
                                           impressions: %(impressions)d
                                           fill_rate: %(fill_rate).2f
                                           clicks: %(clicks)d
                                           ctr: %(ctr)d
                                           ecpm: %(ecpm).2f""" %
                                           dict([('test_date', test_date.strftime("%m/%d/%Y")), ('app', ad_network_app_mapper.application.name)] + stats.__dict__.items()))
                
if __name__ == "__main__":
    setup_remote_api()
    update_ad_networks()                
                
