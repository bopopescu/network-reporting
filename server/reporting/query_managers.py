import datetime
import logging
import time

from google.appengine.ext import db
from google.appengine.ext.db import InternalError, Timeout
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

import reporting.models as reporting_models

from common.utils.cachedquerymanager import CachedQueryManager
from reporting.models import SiteStats, StatsModel
from advertiser.models import Creative
from publisher.models import Site as AdUnit


# maximum number of objects per batch put
LIMIT = 200
# object cache miss sentinel for StatsModelQueryManager
SENTINEL = '!!!'
# max number of retries for offline batch put
MAX_RETRIES = 3


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
    
    def __init__(self, account, offline=False):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        else:
            self.account = db.Key(account)
            
        self.offline = offline
            
        self.stats = []
        self.obj_cache = {}
        
    def get_stats_for_apps(self, apps, num_days=30):
        days = StatsModel.lastdays(num_days)
        account_app_dict = {}
        # we bucket the apps per account since we know 
        # behind the scenes this is how our data is stored
        for app in apps:
            if not app.account.key() in account_app_dict:
                account_app_dict[app.account.key()] = []
            account_app_dict[app.account.key()].append(app)

        stats = []
        for account,apps in account_app_dict.iteritems():
            stats += self.get_stats_for_days(publishers=apps,account=account,num_days=num_days)
            
        return stats    
            
    def get_stats_for_days(self, publisher=None, publishers=None, advertiser=None, days=None, num_days=None, account=None, country=None, offline=False):
        offline = offline or self.offline
        if isinstance(publisher,db.Model):
          publisher = publisher.key()
          
        if isinstance(advertiser,db.Model):
          advertiser = advertiser.key()

        if num_days:
            days = StatsModel.lastdays(num_days)
        else:
            days = days or []
        
        account = account or self.account

        if account:
            parent = db.Key.from_path(StatsModel.kind(),StatsModel.get_key_name(account=account,offline=offline))
        else:
            parent = None

        # in order to use the keys for a lookup we need the parent, 
        # publisher or advertiser and days 
        # NOTE: publisher=None and advertiser=None and day=Something is actually valid
        #       this is basically the rollup for the entire account, but just not supported 
        #       in this QM
        if not publishers and publisher:
            publishers = [publisher]
        
        keys = [db.Key.from_path(StatsModel.kind(),
                                 StatsModel.get_key_name(publisher=publisher,
                                                         advertiser=advertiser,
                                                         account=account,
                                                         date=d,
                                                         country=country,
                                                         offline=offline),
                                  parent=parent)
                    for d in days
                        for publisher in publishers]

        stats = StatsModel.get(keys) # db get
        stats = [s or StatsModel() for s in stats]
        return stats            
    
    def accumulate_stats(self, stat):
        self.stats.append(stat)
    
    
    def put_stats(self, stats=None ,rollup=True, offline=False):
        offline = offline or self.offline
        
        stats = stats or self.stats
        if isinstance(stats,db.Model):
            stats = [stats]
        if rollup:
            all_stats_deltas = self._get_all_rollups(stats, offline)
        else:
            all_stats_deltas = stats
        
        all_stats_deltas = self._place_stats_under_account(all_stats_deltas, offline=offline)
        
        # get or insert from db in order to update as transaction
        def _txn(stats, offline):
            return self._update_db(stats, offline)
        
        if offline:
            return self._update_db(all_stats_deltas, offline)
        else:
            return db.run_in_transaction(_txn, all_stats_deltas, offline)    
        
        
    def _update_db(self, stats, offline):
        offline = offline or self.offline
        key_list = []
        
        if offline:
            all_stats = stats
            page_count = 0
            retries = 0

            while stats and retries <= MAX_RETRIES:
                try:
                    db.put(stats[:LIMIT])
                    stats = stats[LIMIT:]
                    page_count += 1
                    retries = 0
                except (InternalError, Timeout, CapabilityDisabledError):
                    retries += 1
            return [s.key() for s in all_stats[:LIMIT*page_count]] # only return the ones that were successully batch put

        for s in stats:
            stat = db.get(s.key())    # get datastore's stat using key of s
            if stat:    # if exists, update with delta s
                stat += s
            else:       # if doesn't exist, make it with delta s
                stat = s
            key_list.append(stat.put())
        return key_list
        
                
    def _get_all_rollups(self, stats, offline):
        offline = offline or self.offline
        
        # initialize the object dictionary 
        stats_dict = {}
        for stat in stats:
            stats_dict[stat.key().name()] = stat
        
        
        def _get_refprop_from_cache(entity, prop):
            if prop:
                model = entity.__class__
                key = getattr(model,prop).get_value_for_datastore(entity)
                value = self.obj_cache.get(key,SENTINEL)
                if value == SENTINEL:
                    value = getattr(entity,prop)
                    self.obj_cache[key] = value
                return value    
            return None            
        
        
        def _get_stat(pub=None,adv=None,date_hour=None,date=None,month=None,country=None):
            """get or creates the stat from the local dictionary"""
            key = StatsModel.get_key_name(publisher=pub,
                                          advertiser=adv,
                                          date=date,
                                          date_hour=date_hour,
                                          month=month,
                                          country=country) 

            if not key in stats_dict:
                stat =  StatsModel(publisher=pub,
                                   advertiser=adv,
                                   date=date,
                                   date_hour=date_hour,
                                   month=month,
                                   country=country)
                stats_dict[key] = stat
            else:
                stat = stats_dict[key]
            return stat        
             
        
        # TODO: Clean this function up a bit
        def make_above_stat(stat,attribute='date'):
            stat.advertiser = _get_refprop_from_cache(stat, 'advertiser')
            stat.publisher = _get_refprop_from_cache(stat, 'publisher')
            
            if attribute == 'advertiser' and not stat.advertiser:
                return None
            if attribute == 'publisher' and not stat.publisher:
                return None
            if attribute == 'country' and not stat.country:
                return None   
            if attribute == 'date' and stat.month: # stops at the month rollup
                return None

            properties = stat.properties()
            attrs = dict([(k,getattr(stat,k)) for k in properties])  
            
            dynamic_properties = stat.dynamic_properties()
            attrs.update(dict([(k,getattr(stat,k)) for k in dynamic_properties]))
                        
            if attribute == "publisher" and stat.publisher:    
                # owner_name prop returns a string that's the owner, i.e. creative.owner_name = 'ad_group'
                stat.publisher.owner = _get_refprop_from_cache(stat.publisher, stat.publisher.owner_name)
                
                attrs.update(publisher=stat.publisher.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'publisher')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat

            if attribute == "advertiser" and stat.advertiser:
                # owner_name prop returns a string that's the owner, i.e. creative.owner_name = 'ad_group'
                stat.advertiser.owner = _get_refprop_from_cache(stat.advertiser, stat.advertiser.owner_name)
                
                attrs.update(advertiser=stat.advertiser.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'advertiser')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country)
                prev_stat += new_stat
                # if owner is None, undo the increment of request count
                # publisher-* is already accounted for
                if not new_stat.advertiser:
                    prev_stat.request_count -= new_stat.request_count
                stats_dict[prev_stat.key().name()] = prev_stat
                
            
            if attribute == "country" and stat.country:
                country = attrs.get("country")
                attrs.update(country=None)
                new_stat = StatsModel(**attrs)
                
                # updating the geo properties of the model
                new_stat.update_geo(country,
                                    reporting_models.GEO_REQUEST_COUNT,
                                    attrs['request_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_IMPRESSION_COUNT,
                                    attrs['impression_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_CLICK_COUNT,
                                    attrs['click_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_CONVERSION_COUNT,
                                    attrs['conversion_count'])
                
                # we don't need to do a recursive call because
                # we only have 2 levels, if we want to add something
                # like regions we'd do it here
                # make_above_stat(new_stat,'country')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat                      

            if attribute == 'date':
                # NOTE: This is a Pacific TimeZone day
                if stat.date_hour:
                    day = stat.date_hour.date() # makes date object
                    date = datetime.datetime(day.year,day.month,day.day) # makes datetime obj
                    # add date and remove date_hour
                    attrs.update(date=date)
                    del attrs['date_hour']
                if stat.date:
                    date = stat.date
                    month = datetime.datetime(date.year,date.month,1) # makes a date obj for 1st of month
                    attrs.update(month=month)
                    del attrs['date']
                        
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'date')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat
        
        # publisher roll ups
        for stat in stats:
            make_above_stat(stat,'publisher')
                
        # # advertiser rollups        
        stats = stats_dict.values()
        for stat in stats:
            make_above_stat(stat,'advertiser')
            
        # country rollups
        stats = stats_dict.values()
        for stat in stats:
            make_above_stat(stat,'country')
            
        # remove all the country level stats
        # because we are storing this data in dynamic properties
        stats = stats_dict.values()
        for stat in stats:
            if stat.country:
                del stats_dict[stat.key().name()]
        
        # time rollups
        if not offline: # do not rollup on date if it's offline, since aws-logging data is already cumulative
            stats = stats_dict.values()
            for stat in stats:
                make_above_stat(stat,'date')
        
        return stats_dict.values()
    
    
    def _place_stats_under_account(self, stats, account=None, offline=False):
        """
        rewrites all the stats objects in order to place them
        under the StatsModel object for the account
        """
        offline = offline or self.offline
        
        account = account or self.account
        account_stats = StatsModel(account=account, offline=offline) 
        properties = StatsModel.properties()
        properties = [k for k in properties]
        new_stats = [account_stats]
        
        for s in stats:
            # get all the properties of the object
            # StatsModel.prop.get_value_for_datastore(s) for each property of s
            props = {}
            
            for k in properties:
                props[k] = getattr(s,'_%s'%k) # gets underlying data w/ no derefernce
            
            for k in s.dynamic_properties():
                props[k] = getattr(s,k)    
                
            props.update(account=account)
            new_stat = StatsModel(parent=account_stats.key(),
                                  key_name=s.key().name(),
                                  **props)
            new_stats.append(new_stat)
        return new_stats
