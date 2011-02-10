import logging

from common.utils.cachedquerymanager import CachedQueryManager
from advertiser.query_managers import CampaignStatsCounter

from google.appengine.ext import db

from publisher.models import App, Site
from advertiser.models import Campaign, AdGroup, Creative

class AppQueryManager(CachedQueryManager):
    Model = App
    
    def get_apps(self,account=None,deleted=False,limit=50):
        apps = App.all().filter("deleted =",deleted)
        if account:
            apps = apps.filter("account =",account)
        return apps.fetch(limit)  
        
    def put_apps(self,apps):
        return db.put(apps)    

class AdServerAdUnitQueryManager(object):
    Model = Site

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

class AdUnitQueryManager(CachedQueryManager):
    Model = Site
    
    def __init__(self,key=None):
        if isinstance(key,db.Key):
            self.key = str(key)
        else:
            self.key = key  
        self.adunit = None
        return super(AdUnitQueryManager,self).__init__()
  
    def get_adunits(self,app=None,account=None,deleted=False,limit=50):
        adunits = Site.all()
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
              self.adunit = "None!"
        return self.adunit
        
    def get_adunit(self):
        if not self.adunit:
            self.get_by_key(self.key,cache=True)
        if self.adunit == "NONE!":
            return None
        else:  
            return self.adunit
    
    def get_adgroups(self,limit=30):
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