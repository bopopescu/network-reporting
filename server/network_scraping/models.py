from google.appengine.ext import db

from account.models import Account
from publisher.models import App

class AdNetworkLoginInfo(db.Model):
    #(account,ad_network_name)
    
    account = db.ReferenceProperty(Account, collection_name='login_info')
    ad_network = db.StringProperty()
    dictionary = db.StringProperty()

class AdNetworkAppsMapper(db.Model):
    #(ad_network_name,publisher_id) -> application
    ad_network_login = db.ReferenceProperty(AdNetworkLoginInfo, collection_name='ad_networks')
    ad_network_name = db.StringProperty()

    application = db.ReferenceProperty(App, collection_name='ad_networks')
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
    
    ad_network = db.ReferenceProperty(AdNetwork, collection_name='ad_network_stats')
    date = db.DateProperty(auto_now_add=True)
    
    # stats info for a specific day
    attempts = db.IntegerProperty()
    impressions = db.IntegerProperty()
    fill_rate = db.FloatProperty()
    clicks = db.IntegerProperty()
    ctr = db.FloatProperty()
    ecpm = db.FloatProperty()
