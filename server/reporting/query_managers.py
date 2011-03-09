import logging
import time
import datetime
from common.utils.cachedquerymanager import CachedQueryManager

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
    
    def __init__(self, account):
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
        
        # get or insert from db in order to update as transaction
        def _txn(stats):
            self._update_db(all_stats_deltas)
        return db.run_in_transaction(_txn,all_stats_deltas)
        
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
        # initialize the object dictionary 
        stats_dict = {}
        for stat in stats:
            stats_dict[stat.key().name()] = stat
        
        def _get_stat(pub=None,adv=None,date_hour=None,date=None):
            """get or creates the stat from the local dictionary"""
            key = StatsModel.get_key_name(publisher=pub,
                                          advertiser=adv,
                                          date=date,
                                          date_hour=date_hour) 
            if not key in stats_dict:
                stat =  StatsModel(publisher=pub,
                                   advertiser=adv,
                                   date=date,
                                   date_hour=date_hour)
                stats_dict[key] = stat
            else:
                stat = stats_dict[key]
            return stat        
             
        
        # TODO: Clean this function up a bit
        def make_above_stat(stat,attribute='date'):
            
            if attribute == 'advertiser' and not stat.advertiser:
                return None
            if attribute == 'publisher' and not stat.publisher:
                return None

            properties = stat._properties
            attrs = dict([(k,getattr(stat,k)) for k in properties])    
            
            if attribute == "publisher" and stat.publisher:    
                attrs.update(publisher=stat.publisher.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'publisher')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date_hour=new_stat.date)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat

            if attribute == "advertiser" and stat.advertiser:
                attrs.update(advertiser=stat.advertiser.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'advertiser')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date_hour=new_stat.date)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat

            if attribute == 'date':
                # NOTE: This is a Pacific TimeZone day
                day = stat.date.date() # makes date object
                date = datetime.datetime(day.year,day.month,day.day) # makes datetime obj
                properties = stat._properties
                attrs = dict([(k,getattr(stat,k)) for k in properties])    
                attrs.update(date=date)
                new_stat = StatsModel(**attrs)
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat
        
        # publisher roll ups
        for stat in stats:
            make_above_stat(stat,'publisher')
                
        # advertiser rollups        
        stats = stats_dict.values()
        for stat in stats:
            make_above_stat(stat,'advertiser')
        
        # time rollups
        stats = stats_dict.values()
        for stat in stats:
            make_above_stat(stat,'date')
        return stats_dict.values()
    
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