import logging

from google.appengine.ext import db

from account.models import Account, NetworkConfig
from common.utils import date_magic
from common.utils.query_managers import CachedQueryManager
from network_scraping.models import AdNetworkLoginInfo, AdNetworkAppMapper, AdNetworkScrapeStats
from publisher.models import App

class Stats(object):
    pass

class AdNetworkReportQueryManager(CachedQueryManager):

    def __init__(self, account=None):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        elif account is None:
            self.account = None
        else:
            self.account = Account.get_by_key_name(account) #db.Key(account) 
        
    def get_ad_network_mappers(self):
        """ Get the aggregate stats for the different apps given an account """
        for l in AdNetworkLoginInfo.all().filter('account =', self.account):
            for n in AdNetworkAppMapper.all().filter('ad_network_login =', l):
                yield n
                
    def get_ad_network_aggregates(self, ad_network_app_mapper, start_date, end_date):
        q = AdNetworkScrapeStats.all()
        q.filter('ad_network_app_mapper =', ad_network_app_mapper)
        q.filter('date IN', date_magic.gen_days(start_date, end_date))
        
        aggregate_stats = Stats()
        aggregate_stats.revenue = 0
        aggregate_stats.attempts = 0
        aggregate_stats.impressions = 0
        aggregate_stats.clicks = 0
        aggregate_stats.ecpm = 1
        for stats in q:
            old_impressions_total = stats.impressions
    
            aggregate_stats.revenue += stats.revenue
            aggregate_stats.attempts += stats.attempts
            aggregate_stats.impressions += stats.impressions
            aggregate_stats.clicks += stats.clicks
            
            if aggregate_stats.impressions != 0:
                aggregate_stats.ecpm = (aggregate_stats.ecpm * old_impressions_total + stats.ecpm * stats.impressions) / float(aggregate_stats.impressions)
            else:
                aggregate_stats.ecpm = float('NaN')
            
        if aggregate_stats.attempts != 0:
            aggregate_stats.fill_rate = aggregate_stats.impressions / float(aggregate_stats.attempts)
        else:
            aggregate_stats.fill_rate = float('NaN')
        if aggregate_stats.impressions != 0:
            aggregate_stats.ctr = aggregate_stats.clicks / float(aggregate_stats.impressions)
        else:
            aggregate_stats.ctr = float('NaN')
        
        return aggregate_stats

    def get_ad_network_app_stats(self, ad_network_app_mapper):
        """ Get the AdNetworkStats for a given ad_network_app_mapper sorted
        chronologically by day, newest first (decending order) """
        q = AdNetworkScrapeStats.all()
        q.filter('ad_network_app_mapper =', ad_network_app_mapper)
        q.order('-date')
        return q
        
    # (ad_network_app_mapper_key) or (publisher_id, login_info)
    def get_ad_network_app_mapper(self, ad_network_app_mapper_key = None, publisher_id = None, login_info = None):
        """ Get the AdNetworkAppMapper for a given publisher id and 
        login info """
        
        if ad_network_app_mapper_key:
            return db.get(ad_network_app_mapper_key)
        elif publisher_id and login_info:
            query = AdNetworkAppMapper.all()
            query.filter('publisher_id =', publisher_id)
            query.filter('ad_network_login =', login_info)
            return query.get()
        return None
        
    def get_apps_with_publisher_ids(self, ad_network_name):
        """ Get generator of applications with publisher ids for the account on the ad_network """
        for n in NetworkConfig.all().filter('%s_pub_id !=' % ad_network_name, None):
            for a in App.all().filter('account =', self.account).filter('network_config =', n):
                yield (a, eval('n.%s_pub_id' % ad_network_name))
        
def get_pub_id(pub_id, login_info):
    return pub_id

def get_pub_id_from_name(app_name, login_info):
    query = App.all()
    query.filter('name =', app_name)
    query.filter('account =', login_info.account)
    app = query.get()

    if app:
        if login_info.ad_network_name == 'jumptap':
            return app.network_config.jumptap_pub_id
        elif login_info.ad_network_name == 'iad':
            return app.network_config.iad_pub_id
    else:
        return None