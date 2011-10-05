# import os, sys
# sys.path.append(os.environ['PWD'])

from google.appengine.ext import db

from account.models import Account
from common.utils.query_managers import CachedQueryManager
from network_scraping.models import AdNetworkLoginInfo, AdNetworkAppMapper, AdNetworkScrapeStats
from publisher.models import App

class AdNetworkReportQueryManager(CachedQueryManager):

    def __init__(self, account=None, offline=True):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        elif account is None:
            self.account = None
        else:
            self.account = Account.get_by_key_name(account) #db.Key(account) 
        
    def get_ad_network_totals(self):
        """ Get the aggregate stats for the different apps given an account """
        for l in AdNetworkLoginInfo.all().filter('account =', self.account):
            for n in AdNetworkAppMapper.all().filter('ad_network_login =', l):
                yield n

    def get_ad_network_app_stats(self, ad_network_app_mapper):
        """ Get the AdNetworkStats for a given ad_network_app_mapper sorted
        chronologically by day, newest first (decending order) """
        q = AdNetworkScrapeStats.all()
        q.filter('ad_network_app_mapper =', ad_network_app_mapper)
        q.order('-date')
        return q
        
    # (ad_network_app_mapper_key) or (publisher_id, login_info)
    def get_ad_network_app_mapper(self, *args, **kwargs):
        """ Get the AdNetworkAppMapper for a given publisher id and 
        login info """
        ad_network_app_mapper_key = kwargs.get('ad_network_app_mapper_key', None)
        publisher_id = kwargs.get('publisher_id', None)
        login_info = kwargs.get('login_info', None)
        
        if ad_network_app_mapper_key:
            return db.get(ad_network_app_mapper_key)
        elif publisher_id and login_info:
            query = AdNetworkAppMapper.all()
            query.filter('publisher_id =', publisher_id)
            query.filter('ad_network_login =', login_info)
            return query.get()
        return None
        
def get_pub_id(pub_id, login_info):
    return pub_id

def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter('name =', app_name)
    query.filter('account =', login_info.account)
    publisher_id = query.get()

    if publisher_id:
        return publisher_id.network_config.jumptap_pub_id
    else:
        return None