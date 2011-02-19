import logging

from common.utils.cachedquerymanager import CachedQueryManager
from advertiser.query_managers import CampaignStatsCounter

from google.appengine.ext import db

from reporting.models import SiteStats, StatsModel

class SiteStatsQueryManager(CachedQueryManager):
    def get_sitestats_for_days(self, site=None, owner=None, days=None):
        if isinstance(site,db.Model):
          site_key = site.key()
        else:
          site_key = site
        if isinstance(owner,db.Model):
          owner_key = owner.key()
        else:
          owner_key = owner
          
        days = days or None  
        keys = (SiteStats.get_key(site_key, owner_key, d) for d in days)
        stats = SiteStats.get(keys) # db get
        stats = [s or SiteStats() for s in stats]
        return stats
        
class StatsModelQueryManager(CachedQueryManager):
    Model = StatsModel
    def __init__(self, account=None):
        if isinstance(account, db.Key):
            self.account = account
        else:
            self.account = db.Key(account)
            
    def get_stats_for_days(self, publisher=None, advertiser=None, days=None, account=None):
        if isinstance(publisher,db.Model):
          publisher = publisher.key()

        if isinstance(advertiser,db.Model):
          advertiser = advertiser.key()

        days = days or []
        account = account or self.account

        keys = (StatsModel.get_key(publisher=publisher,advertiser=advertiser,account=account)
                    for d in days)
        stats = StatsModel.get(keys) # db get
        stats = [s or StatsModel() for s in stats]
        return stats            
        
    
    def put_stats(self,stats):
        if isinstance(stats,db.Model):
            stats = [stats]
        all_stats_deltas = self._get_all_rollups(stats)
        all_stats_deltas = self._place_stats_under_account(all_stats_deltas)
        
        # get or insert from db in order to update
        return self._update_db(all_stats_deltas)
        
    def _update_db(self,stats):
        for s in stats:
            stat = db.get(s.key())    
            if stat:
                stat += s
            else:
                stat = s
            stat.put()
            
        logging.info("putting in key_name: %s value: %s,%s"%(s.key().name(),s.request_count,s.impression_count))
        logging.info("putting in key_name: %s NEW value: %s,%s"%(s.key().name(),stat.request_count,stat.impression_count))
        
    def _get_all_rollups(self,stats):
        # TODO: make all the necessary rollups here
        # date-hour, date
        # AdUnit, App
        # Campaign, AdGroup, Creative
        # AdUnit-Creative, App-Creative, AdUnit-AdGroup, App-AdGroup
        # AdUnit-Campaign, App-Campaign
        # Account
        return stats    
    
    def _place_stats_under_account(self,stats,account=None):
        """
        rewrites all the stats objects in order to place them
        under the StatsModel object for the account
        
        """
        account = account or self.account
        account_stats = StatsModel(account=account) 
        properties = StatsModel._properties
        new_stats = [account_stats]
        
        for s in stats:
            # get all the properties of the object
            # StatsModel.prop.get_value_for_datastore(s) for each property of s
            props = {}
            for k in properties:
                props[k] = getattr(s,'_%s'%k) # gets underlying data w/ no derefernce
            new_stat = StatsModel(parent=account_stats.key(),
                                  key_name=s.key().name(),
                                  **props)
            new_stats.append(new_stat)
        return new_stats