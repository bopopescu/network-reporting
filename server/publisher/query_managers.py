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

AdUnit = Site

class AdUnitContext(object):
    """All the adunit information necessary
    to run the auction. """
    
    @classmethod
    def wrap(cls, adunit):
        """ Factory method that takes an adunit, fetches all the appropriate information
        from the database, and then returns an adunit_context object """
        adgroups = cls.fetch_adgroups(adunit)
        campaigns = cls.fetch_campaigns(adgroups)
        creatives = cls.fetch_creatives(adgroups)
        
        adunit_context = cls(adunit, 
                             campaigns, 
                             adgroups, 
                             creatives)
        return adunit_context

    def __init__(self, adunit, campaigns, adgroups, creatives):
        self.adunit = adunit
        
        
        self.campaigns = campaigns
        self.adgroups = adgroups
        self.creatives = creatives
        
        # creative_ctr is a mapping from creative keys to CreativeCTR objects
        self.creative_ctrs = {}
        for c in creatives:
            self.creative_ctrs[c.key()] = CreativeCTR(c, adunit)
            
            
        # Triggers dereferencing of references so we can cache the whole object
        # We ask both Account and App for an arbitrary property 
        self.adunit.account.active
        self.adunit.app_key.deleted


    def _get_ctr(self, creative, date=datetime.date.today(), date_hour=None, min_sample_size=1000):
        '''Given a creative, calculates the CTR.  
        The date_hour parameter is the last full hour that has passed.
        If date_hour is specified, gets or updates the CTR for that hour. 
        If date_hour is not specified, use daily CTR.
        If sample size is insufficient, return None.'''
        
        creative_ctr = self.creative_ctrs.get(creative.key())
        try:
            # Use daily if date_hour is not specified
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
        creatives = self.creatives
        # we must use get_value_for_datastore so we don't auto dereference
        creatives = [creative for creative in self.creatives
                              if creative.ad_group.key() in adgroup_keys]

        return creatives
        
    @classmethod
    def fetch_adgroups(cls, adunit, limit=30):
        logging.info("getting adgroups from db")
        adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                  filter("active =",True).\
                                  filter("deleted =",False).\
                                  fetch(limit)
        return adgroups

    @classmethod
    def fetch_creatives(cls, adgroups, limit=30):
        logging.info("getting creatives from db")
        creatives = Creative.all().filter("ad_group IN", adgroups).\
                    filter("active =",True).filter("deleted =",False).\
                    fetch(limit)
                    
        # re-write creative so that ad_group is actually the object already in memory
        for creative in creatives:
            creative.ad_group = [ag for ag in adgroups 
                        if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]
        
        return creatives

    @classmethod
    def fetch_campaigns(cls, adgroups):  
        # campaign exclusions... budget + time
        logging.info("attach eligible campaigns")
        campaigns = []
        for adgroup in adgroups:
            campaign = db.get(adgroup.campaign.key())
            campaigns.append(campaign)

        # attach sharded counter to all campaigns for budgetary
        # @Nafis: is this necessary?
        for campaign in campaigns:
            campaign.delivery_counter = CampaignStatsCounter(campaign)
        return campaigns
        
        
    def key(self):
        """ Since we want a 1-1 mapping from adunits to adunit_contexts, we
        appropriate the key from the adunit, returns a string. """
        return "context:"+str(self.adunit.key())
        
    def get_creative_by_key(self,creative_key):
        creative = None
        for c in self.creatives:
            if str(creative_key) == str(c.key()):
                creative = c
                break
        return creative    
        
class CreativeCTR(object):
    """ The relevant CTR information for a creative-adunit pairing"""
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
    """ Keeps an up-to-date version of the AdUnit Context in memcache.
    Deleted from memcache whenever its components are updated."""
    Model = AdUnitContext

    def cache_get(self,adunit_key):
        """ Takes an AdUnit key, gets or builds the context """
        adunit_key = str(adunit_key).replace("'","")
        adunit_context_key = "context:"+str(adunit_key)
        adunit_context = memcache.get(adunit_context_key, namespace="context")
        if adunit_context is None:
            # get adunit from db
            adunit = AdUnit.get(adunit_key)
            # wrap context
            adunit_context = AdUnitContext.wrap(adunit)
            # put context in cache
            memcache.set(str(adunit_context.key()), adunit_context, namespace="context")
        return adunit_context
        
    def cache_delete_from_adunits(self, adunits):
        if not isinstance(adunits,list):
          adunits = [adunits]

        return memcache.delete_multi(["context:"+str(adunit.key()) for adunit in adunits],namespace="context")

class AppQueryManager(CachedQueryManager):
    Model = App
    
    def get_apps(self,account=None,deleted=False,limit=50):
        apps = self.Model.all().filter("deleted =",deleted)
        if account:
            apps = apps.filter("account =",account)
        return apps.fetch(limit)  

    def reports_get_apps(self, account=None, publisher=None, advertiser=None, deleted=False, limit=50):
        '''Given account or pub, or adv or some combination thereof return a list of apps that (correctly) 
        correspond to the inputs and things'''
        apps = self.model.all().filter("deleted =", deleted)
        if account:
            apps = apps.filter('account =', account)
        adunits = []
        #if advertiser is set, restrict apps to be only those apps that advertiser has an effect on
        if advertiser:
            if type(advertiser) != list:
                advertiser = [advertiser]
            for adv in advertiser:
                #get adgroups from campaigns
                if hasattr(adv, 'adgroups'):
                    adgroups = adv.adgroups
                # or creatives
                elif hasattr(adv, 'adgroup'):
                    adgroups = [adv.adgroup]
                else:
                    adgroups = advertiser
                #iterate over adgroups and accumulate site_keys
                for adgroup in adgroups:
                    for key in adgroup.site_keys:
                        if key not in adunits:
                            adunits.append(key)
            
            adunit_objs = AdUnit.get(adunits)

            apps = set()
            for adunit in adunit_objs:
                apps.add(adunit.app)
            return list(apps)    

            
            final_apps = []
            for app in apps:
                for au in app.adunits:
                    if au in adunits:
                        final_apps.append(app)
                        break
            return final_apps
        #if publisher has been set then everything makes no sense so just ignore it and pass it back or something
        # huh?
        if publisher:
            return [publisher]
        else:
            return apps
        
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
  
    def get_adunits(self,app=None,apps=None, account=None,keys=None,deleted=False,limit=50):
        if keys is not None:
            if type(keys) == list and len(keys) == 0:
                return []
            elif len(keys) > 0:
                return self.Model.get(keys)
            else:
                logging.error('len is negative?')

        adunits = AdUnit.all().filter("deleted =",deleted)
        if app:
            adunits = adunits.filter("app_key =",app)
        elif apps:
            adunits = adunits.filter("app_key in", apps)
        if account:
            adunits = adunits.filter("account =",account)      
        return adunits.fetch(limit)

    def reports_get_adunits(self, account=None, publisher=None, advertiser=None, deleted=False):
        '''Given an account or publisher or advertiser return a list of adunits targeted by 
        the advertiser(s) and/or linked to the publisher(s)'''
        adunits = Site.all().filter('deleted =', deleted)
        if account:
            #sanity check
            adunits = adunits.filter('account =', account)
        #do first
        if advertiser:
            #we have advertisers, so don't target ALL adunits for a user, target only
            # those that are specified by advertisers
            adunits = []
            #make advertiser a list (this has to do with how I plan on implementing network priority
            # and stuff) if it isn't already one
            if not type(advertiser) == list:
                advertiser = [advertiser]
            for adv in advertiser:
                # this is how campaigns reference adgroups
                if hasattr(adv, 'adgroups'):
                    adgroups = adv.adgroups
                # this is how creatives reference adgroups
                elif hasattr(adv, 'adgroup'):
                    adgroups = [adv.adgroup]
                else:
                    adgroups = advertiser
                # iterate over the adgroups (I think this is always just one though...?)
                for ag in adgroups:
                    #iterate over adgroup adunit targets
                    for key in ag.site_keys:
                        #if this isn't in the adunits list yet, put it there
                        if key not in adunits:
                            adunits.append(key)
            #turn string refs into actual objects
            adunits = AdUnit.get(adunits)
        #publisher can only be an app or adunit, and two adunits is dumb
        # also do publisher after because we can filter much faster with advertiser data than the deleted stuff
        if publisher:
            adunits = adunits.filter('app_key =', publisher)
        return adunits
        
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
    
    # def get_adgroups(self,limit=30):
    #      # Deprecated, use AdUnitContext
    #      if not self.adunit:
    #          self.get_adunit()
    # 
    #      adunit = self.adunit  
    #      if not hasattr(adunit,'eligible_adgroups'):
    #          logging.info("getting adgroups from db")
    #          adunit.eligible_adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
    #                                    filter("active =",True).\
    #                                    filter("deleted =",False).\
    #                                    fetch(limit)
    #          self._attach_campaign_info(adunit)                            
    #          self.cache_put(adunit)
    #      return adunit.eligible_adgroups
    #  
    #  def _attach_campaign_info(self,adunit):  
    #      # Deprecated, use AdUnitContext
    #      # campaign exclusions... budget + time
    #      if not hasattr(adunit,'eligible_campaigns'):
    #          logging.info("attach eligible campaigns")
    #          adunit.eligible_campaigns = []
    #          for adgroup in adunit.eligible_adgroups:
    #              adgroup.campaign = db.get(adgroup.campaign.key())
    #              adunit.eligible_campaigns.append(adgroup.campaign)
    #    
    #          # attach sharded counter to all campaigns for budgetary
    #          for campaign in adunit.eligible_campaigns:
    #              campaign.delivery_counter = CampaignStatsCounter(campaign)
    #  
    #  def get_creatives_for_adgroups(self,adgroups,limit=30):
    #      # Deprecated, use AdUnitContext
    #      if not hasattr(self.adunit,'eligible_adgroups'):
    #          self.get_adgroups()
    #    
    #      # put all the creatives into memcache if not already there 
    #      if not hasattr(self.adunit,'eligible_creatives'):
    #          logging.info("getting creatives from db")
    #          self.adunit.eligible_creatives = Creative.all().filter("ad_group IN",self.adunit.eligible_adgroups).\
    #                      filter("active =",True).filter("deleted =",False).\
    #                      fetch(limit)
    #          # re-write creative so that ad_group is actual the object already in memory
    #          for creative in self.adunit.eligible_creatives:
    #              creative.ad_group = [ag for ag in self.adunit.eligible_adgroups 
    #                          if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]
    #          # [creative.ad_group.key() for creative in self.adunit.eligible_creatives]
    #          self.cache_put(self.adunit)
    #  
    #      # get only the creatives for the requested adgroups
    #      adgroup_keys = [adgroup.key() for adgroup in adgroups]
    #      creatives = self.adunit.eligible_creatives
    #      # we must use get_value_for_datastore so we don't auto dereference
    #      creatives = [creative for creative in self.adunit.eligible_creatives
    #                            if creative.ad_group.key() in adgroup_keys]
    #    
    #      return creatives                  
    # 
    # 
 





