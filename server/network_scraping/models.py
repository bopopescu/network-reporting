from google.appengine.ext import db

from account.models import Account
from publisher.models import App

import logging

class AdNetworkLoginInfo(db.Model):
    #(account,ad_network_name)
    
    account = db.ReferenceProperty(Account, collection_name='login_info')
    ad_network_name = db.StringProperty()
    
    # needed for all networks but mobfox
    username = db.StringProperty()
    password = db.StringProperty()
    
    # needed for admob and mobfox
    client_key = db.StringProperty()
    
    # needed for mobfox
    publisher_ids = db.StringListProperty()

class AdNetworkAppMapper(db.Model):
    #(ad_network_name,publisher_id) -> application
    ad_network_login = db.ReferenceProperty(AdNetworkLoginInfo, collection_name='ad_network_app_mappers')
    ad_network_name = db.StringProperty()
    
    application = db.ReferenceProperty(App, collection_name='ad_network_app_mappers')
    # Is this needed for admob?
    publisher_id = db.StringProperty()
    
    # aggregate stats info
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()
    
class AdNetworkScrapeStats(db.Model):
    #(AdNetwork, date)
    #(AdNetworkName, App, date)
    
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper, collection_name='ad_network_stats')
    date = db.DateProperty()
    
    # stats info for a specific day
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()
   
# Query functions
''' Get the aggregate stats for the different apps given an account '''
def get_ad_network_totals(account):
    for l in AdNetworkLoginInfo.all().filter('account =', account):
        for n in AdNetworkAppMapper.all().filter('ad_network_login =', l):
            yield n

''' Get the AdNetworkStats for a given ad_network_app_mapper sorted chronologically by day '''
def get_ad_network_app_stats(ad_network_app_mapper):
    q = AdNetworkScrapeStats.all()
    q.filter('ad_network_app_mapper =', ad_network_app_mapper)
    return q
    
def get_jump_tap_pub_id(app_name, login_info):
    query = App.all()
    query.filter("name =", app_name)
    query.filter("account =", login_info.account)
    publisher_id = query.get()

    if publisher_id:
        return publisher_id.network_config.jumptap_pub_id
    else:
        return None
        
def get_ad_network_app_mapper(publisher_id, login_info):
    query = AdNetworkAppMapper.all()
    query.filter("ad_network_login =", login_info)
    query.filter("publisher_id =", publisher_id)
    return query.get()