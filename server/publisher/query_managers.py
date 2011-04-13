import logging

from common.utils.cachedquerymanager import CachedQueryManager
from advertiser.query_managers import CampaignStatsCounter

from google.appengine.ext import db

from publisher.models import App
from publisher.models import Site as AdUnit
from advertiser.models import Campaign, AdGroup, Creative
import datetime
from reporting.query_managers import StatsModelQueryManager
from google.appengine.api import memcache

class AdUnitContext(object):
    """All the adunit information necessary
    to run the auction """

    def __init__(self, adunit, eligible_campaigns,
                               eligible_adgroups, 
                               eligible_creatives):
        self.adunit = adunit
        
        # Triggers dereferencing of references
        # We ask both Account and App for an arbitrary property
        self.adunit.account.active
        self.adunit.app_key.deleted
        
        self.eligible_campaigns = eligible_campaigns
        self.eligible_adgroups = eligible_adgroups
        self.eligible_creatives = eligible_creatives
        
        # creative_ctr is a mapping from creative keys to CreativeCTR objects
        self.creative_ctrs = {}
        for c in eligible_creatives:
            self.creative_ctrs[c.key()] = CreativeCTR(c, adunit)
        
    def key(self):
        """ Since we want a 1-1 mapping from adunits to adunit_contexts, we
        appropriate the key from the adunit """
        return self.adunit.key()    

    def get_ctr(self, creative, date=datetime.date.today(), date_hour=None, min_sample_size=1000):
        
        creative_ctr = self.creative_ctrs.get(creative.key())
        try:
            # Use daily if passed a date_hour
            if date_hour is not None:
                return creative_ctr.get_or_update_hourly_ctr(date_hour=date_hour, min_sample_size=min_sample_size)
            else:
                return creative_ctr.get_or_update_daily_ctr(date=date, min_sample_size=min_sample_size)
        except AttributeError:
            # If we couldn't find the creative, return None
            return None
                    
    def get_creatives_for_adgroups(self,adgroups,limit=30):
        """ Get only the creatives for the requested adgroups """
        adgroup_keys = [adgroup.key() for adgroup in adgroups]
        creatives = self.eligible_creatives
        # we must use get_value_for_datastore so we don't auto dereference
        creatives = [creative for creative in self.eligible_creatives
                              if creative.ad_group.key() in adgroup_keys]

        return creatives
        
    @classmethod
    def rollup(cls, adunit):
        """ Takes an adunit, fetches all the appropriate information from the
        database, and then returns an adunit_context object """
        
        eligible_adgroups = cls.fetch_adgroups(adunit)
        eligible_campaigns = cls.fetch_campaigns(eligible_adgroups)
        eligible_creatives = cls.fetch_creatives(eligible_adgroups)
        
        adunit_context = cls(adunit, 
                             eligible_campaigns, 
                             eligible_adgroups, 
                             eligible_creatives)
        return adunit_context
        
    @classmethod
    def fetch_adgroups(cls, adunit, limit=30):
        logging.info("getting adgroups from db")
        eligible_adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                  filter("active =",True).\
                                  filter("deleted =",False).\
                                  fetch(limit)
        return eligible_adgroups

    @classmethod
    def fetch_creatives(cls, eligible_adgroups, limit=30):
        logging.info("getting creatives from db")
        eligible_creatives = Creative.all().filter("ad_group IN", eligible_adgroups).\
                    filter("active =",True).filter("deleted =",False).\
                    fetch(limit)
                    
        # re-write creative so that ad_group is actually the object already in memory
        for creative in eligible_creatives:
            creative.ad_group = [ag for ag in eligible_adgroups 
                        if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]
        # [creative.ad_group.key() for creative in self.adunit.eligible_creatives]
        
        return eligible_creatives

    @classmethod
    def fetch_campaigns(cls, eligible_adgroups):  
        # campaign exclusions... budget + time
        logging.info("attach eligible campaigns")
        eligible_campaigns = []
        for adgroup in eligible_adgroups:
            campaign = db.get(adgroup.campaign.key())
            eligible_campaigns.append(campaign)

        # attach sharded counter to all campaigns for budgetary
        # @Nafis: is this necessary?
        for campaign in eligible_campaigns:
            campaign.delivery_counter = CampaignStatsCounter(campaign)
        return eligible_campaigns
        
class CreativeCTR(object):
    """ The relevant CTR information for a creative"""
    def __init__(self, creative, adunit):
        self.creative = creative
        self.adunit = adunit
        self.hourly_ctr = None
        self.daily_ctr = None
        self.hourly_ctr_expiration_datetime = None
        self.daily_ctr_expiration_date = None
        
    def get_or_update_hourly_ctr(self, date_hour=datetime.datetime.now(), min_sample_size=1000):
        """ Get's the hourly ctr value, updates it if expired, 
            ctr is defined as clicks/impressions*100
            date_hour is a datetime object"""
        if not self.hourly_ctr_expiration_datetime or \
        date_hour >= self.hourly_ctr_expiration_datetime:
            # Update both the hourly and daily ctrs
            self._update_hourly_ctr(date_hour=date_hour, min_sample_size=min_sample_size)
            # self._update_daily_ctr(date=date_hour.date(), min_sample_size=min_sample_size)

            return self.hourly_ctr

        # If not expired
        return self.hourly_ctr
    
    def _update_hourly_ctr(self, date_hour=datetime.datetime.now(), min_sample_size=1000):

        last_full_hour = date_hour - datetime.timedelta(hours=1)
        # logging.info("Using date: %s, %s, %s" % (last_full_hour, self.adunit, self.creative))
        
        smqm = StatsModelQueryManager(self.adunit.account)

        qm_stats = smqm.get_stats_for_hours(publisher=self.adunit,
                                         advertiser=self.creative,
                                         date_hour=last_full_hour)

        stats = qm_stats # qm_stats is a list of stats of length 1

        # Make sure we have enough impressions
        if stats.impression_count >= min_sample_size:
            self.hourly_ctr = stats.ctr
  
        # Whether or not we updated the ctr, set the new expiration date
        self.hourly_ctr_expiration_datetime = date_hour + datetime.timedelta(hours=1)
    

    def get_or_update_daily_ctr(self, date=datetime.date.today(), min_sample_size=1000):
        """ Get's the daily ctr value, updates it if expired, 
            ctr is defined as clicks/impressions*100"""
        # Do calculations if expired
        if self.daily_ctr_expiration_date is None or date >= self.daily_ctr_expiration_date:
            self._update_daily_ctr(date=date, min_sample_size=min_sample_size)

            # Daily ctr has been updated if possible, return it
            return self.daily_ctr

        # If not expired
        return self.daily_ctr
        

    def _update_daily_ctr(self, date=datetime.date.today(), min_sample_size=1000):
          """ Updates the daily ctr value if we have enough impressions """
          smqm = StatsModelQueryManager(self.adunit.account)

          qm_stats = smqm.get_stats_for_days(publisher=self.adunit,
                                           advertiser=self.creative,
                                           days=[date])

          stats = qm_stats[0] # qm_stats is a list of stats of length 1
          # Make sure we have enough impressions
          if stats.impression_count >= min_sample_size:
              self.daily_ctr = stats.ctr

          # Whether or not we updated the ctr, set the new expiration date
          self.daily_ctr_expiration_date = date

        
class AdUnitContextQueryManager(CachedQueryManager):
    Model = AdUnitContext

    def cache_get(self,adunit_key):
        """ Takes an AdUnit key, gets or builds the context """
        adunit_context = memcache.get(adunit_key)
        if adunit_context is None:
            # get adunit from db
            adunit = AdUnit.get(adunit_key)
            # wrap context
            adunit_context = AdUnitContext.rollup(adunit)
            # put context in cache
            memcache.set(str(adunit_context.key()), adunit_context)
        return adunit_context

class AppQueryManager(CachedQueryManager):
    Model = App
    
    def get_apps(self,account=None,deleted=False,limit=50):
        apps = self.Model.all().filter("deleted =",deleted)
        if account:
            apps = apps.filter("account =",account)
        return apps.fetch(limit)  
        
    def put_apps(self,apps):
        return db.put(apps)    

class AdUnitQueryManager(CachedQueryManager):
    Model = AdUnit
    
    def __init__(self,key=None):
        if isinstance(key,db.Key):
            self.key = str(key)
        else:
            self.key = key  
        self.adunit = None
        return super(AdUnitQueryManager,self).__init__()
  
    def get_adunits(self,app=None,account=None,keys=None,deleted=False,limit=50):
        if keys:
            return self.Model.get(keys)
        
        adunits = AdUnit.all()
        if not deleted == None:
            adunits = adunits.filter("deleted =",deleted)
        if app:
            adunits = adunits.filter("app_key =",app)
        if account:
            adunits = adunits.filter("account =",account)      
        return adunits.fetch(limit)
        
    def put_adunits(self,adunits):
        db.put(adunits)    
               
    def get_by_key(self,key,none=False,cache=False):
        if not cache:
          return super(AdUnitQueryManager, self).get_by_key(key)    

        if isinstance(key,(set,list)):
            key = [str(k) for k in key]

        adunits = self.cache_get(key)
        if adunits:
            self.adunit = adunits[0]
            # trigger dereference to attach account info
            if self.adunit:
              self.adunit.account.active
        else:
            if none:
              self.adunit = None
            else:
              self.adunit = "Does not exist"
        return self.adunit
        
    def get_adunit(self):
        if not self.adunit:
            self.get_by_key(self.key,cache=True)
        if self.adunit == "Does not exist":
            return None
        else:  
            return self.adunit
    
    def get_adgroups(self,limit=30):
        # Deprecated, use AdUnitContext
        if not self.adunit:
            self.get_adunit()

        adunit = self.adunit  
        if not hasattr(adunit,'eligible_adgroups'):
            logging.info("getting adgroups from db")
            adunit.eligible_adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                      filter("active =",True).\
                                      filter("deleted =",False).\
                                      fetch(limit)
            self._attach_campaign_info(adunit)                            
            self.cache_put(adunit)
        return adunit.eligible_adgroups
    
    def _attach_campaign_info(self,adunit):  
        # Deprecated, use AdUnitContext
        # campaign exclusions... budget + time
        if not hasattr(adunit,'eligible_campaigns'):
            logging.info("attach eligible campaigns")
            adunit.eligible_campaigns = []
            for adgroup in adunit.eligible_adgroups:
                adgroup.campaign = db.get(adgroup.campaign.key())
                adunit.eligible_campaigns.append(adgroup.campaign)
      
            # attach sharded counter to all campaigns for budgetary
            for campaign in adunit.eligible_campaigns:
                campaign.delivery_counter = CampaignStatsCounter(campaign)
    
    def get_creatives_for_adgroups(self,adgroups,limit=30):
        # Deprecated, use AdUnitContext
        if not hasattr(self.adunit,'eligible_adgroups'):
            self.get_adgroups()
      
        # put all the creatives into memcache if not already there 
        if not hasattr(self.adunit,'eligible_creatives'):
            logging.info("getting creatives from db")
            self.adunit.eligible_creatives = Creative.all().filter("ad_group IN",self.adunit.eligible_adgroups).\
                        filter("active =",True).filter("deleted =",False).\
                        fetch(limit)
            # re-write creative so that ad_group is actual the object already in memory
            for creative in self.adunit.eligible_creatives:
                creative.ad_group = [ag for ag in self.adunit.eligible_adgroups 
                            if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]
            # [creative.ad_group.key() for creative in self.adunit.eligible_creatives]
            self.cache_put(self.adunit)
    
        # get only the creatives for the requested adgroups
        adgroup_keys = [adgroup.key() for adgroup in adgroups]
        creatives = self.adunit.eligible_creatives
        # we must use get_value_for_datastore so we don't auto dereference
        creatives = [creative for creative in self.adunit.eligible_creatives
                              if creative.ad_group.key() in adgroup_keys]
      
        return creatives                  











class AdServerAdUnitQueryManager(object):
    # Deprecated, This should be removed
    # Jim put this together when he thought cache was broken
    Model = AdUnit

    def __init__(self, key=None):
        if isinstance(key, db.Key):
            self.key = key
        else:
            self.key = db.Key(key)
        self.adunit = db.get(self.key)

    def get_adunit(self):
        return self.adunit

    def get_adgroups(self,limit=30):
        adunit = self.adunit  
        if not hasattr(adunit,'eligible_adgroups'):
            logging.info("getting adgroups from db")
            adunit.eligible_adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                      filter("active =",True).\
                                      filter("deleted =",False).\
                                      fetch(limit)
        self._attach_campaign_info(adunit)                            
        return adunit.eligible_adgroups

    def _attach_campaign_info(self,adunit):  
        # campaign exclusions... budget + time
        if not hasattr(adunit,'eligible_campaigns'):
            adunit.eligible_campaigns = []
        for adgroup in adunit.eligible_adgroups:
            adgroup.campaign = db.get(adgroup.campaign.key())
            adunit.eligible_campaigns.append(adgroup.campaign)

        # attach sharded counter to all campaigns for budgetary
        for campaign in adunit.eligible_campaigns:
            campaign.delivery_counter = CampaignStatsCounter(campaign)

    def get_creatives_for_adgroups(self,adgroups,limit=30):
        if not hasattr(self.adunit,'eligible_adgroups'):
            self.get_adgroups()

        # put all the creatives into memcache if not already there 
        if not hasattr(self.adunit,'eligible_creatives'):
            logging.info("getting creatives from db")
            self.adunit.eligible_creatives = Creative.all().filter("ad_group IN",self.adunit.eligible_adgroups).\
                        filter("active =",True).filter("deleted =",False).\
                        fetch(limit)

        # re-write creative so that ad_group is actual the object already in memory
        for creative in self.adunit.eligible_creatives:
            creative.ad_group = [ag for ag in self.adunit.eligible_adgroups 
                        if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]

        # get only the creatives for the requested adgroups
        adgroup_keys = [adgroup.key() for adgroup in adgroups]
        creatives = self.adunit.eligible_creatives

        # we must use get_value_for_datastore so we don't auto dereference
        creatives = [creative for creative in self.adunit.eligible_creatives
                              if creative.ad_group.key() in adgroup_keys]

        return creatives
