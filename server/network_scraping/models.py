from google.appengine.ext import db

from account.models import Account
from publisher.models import App

import logging

class AdNetworkLoginInfo(db.Model):
    #(account,ad_network_name)
    
    account = db.ReferenceProperty(Account, required = True, collection_name='login_info')
    ad_network_name = db.StringProperty(required = True)
    
    # needed for all networks but mobfox
    username = db.StringProperty()
    password = db.StringProperty()
    
    # needed for admob and mobfox
    client_key = db.StringProperty()
    
    # needed for mobfox
    publisher_ids = db.StringListProperty()
    
    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = 'k:%s:%s' % (kwargs['account'].key(), kwargs['ad_network_name'])
        super(AdNetworkLoginInfo, self).__init__(*args, **kwargs)

class AdNetworkAppMapper(db.Model):
    #(ad_network_name,publisher_id) -> application
    ad_network_name = db.StringProperty(required = True)
    publisher_id = db.StringProperty(required = True)
    
    ad_network_login = db.ReferenceProperty(AdNetworkLoginInfo, collection_name='ad_network_app_mappers')
    application = db.ReferenceProperty(App, collection_name='ad_network_app_mappers')
    
    # aggregate stats info
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()
    
    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = 'k:%s:%s' % (kwargs['ad_network_name'], kwargs['publisher_id'])
        super(AdNetworkAppMapper, self).__init__(*args, **kwargs)
    
class AdNetworkScrapeStats(db.Model):
    #(AdNetworkAppMapper, date)
    
    ad_network_app_mapper = db.ReferenceProperty(AdNetworkAppMapper, required = True, collection_name='ad_network_stats')
    date = db.DateProperty(required = True)
    
    # stats info for a specific day
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()
    
    def __init__(self, *args, **kwargs):
        if not kwargs.get('key', None):
            kwargs['key_name'] = 'k:%s:%s' % (kwargs['ad_network_app_mapper'].key(), kwargs['date'].strftime('%Y-%m-%d'))
        super(AdNetworkScrapeStats, self).__init__(*args, **kwargs)
   