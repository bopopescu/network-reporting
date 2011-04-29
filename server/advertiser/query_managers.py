import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db

from common.utils.query_managers import QueryManager, CachedQueryManager
from common.utils.decorators import wraps_nonlists

from advertiser.models import Campaign
from advertiser.models import AdGroup
from advertiser.models import Creative, TextCreative, \
                              TextAndTileCreative, \
                              HtmlCreative,\
                              ImageCreative

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

NAMESPACE = None

class CampaignQueryManager(QueryManager):
    Model = Campaign

    @classmethod
    def get_campaigns(cls,account=None,adunit=None,deleted=False,limit=50):
        campaigns = Campaign.all()
        if not (deleted == None):
            campaigns = campaigns.filter("deleted =",deleted)
        if account:
            campaigns = campaigns.filter("account =",account)
        return campaigns.fetch(limit)        
        
    @classmethod
    @wraps_nonlists
    def put(cls, campaigns):
        put_response = db.put(campaigns)

        # Clear cache
        adunits = []
        for campaign in campaigns:
            logging.info(campaign.name)
            for adgroup in campaign.adgroups:
                logging.info(adgroup.name)
                adunits.extend(adgroup.site_keys)
                
        adunits = AdUnitQueryManager.get(adunits)    
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        return put_response
    

class AdGroupQueryManager(QueryManager):
    Model = AdGroup   
        
    @classmethod
    def get_adgroups(cls,campaign=None,campaigns=None,adunit=None,account=None,deleted=False,limit=50):
        adgroups = AdGroup.all()
        if not (deleted == None):
            adgroups = adgroups.filter("deleted =",deleted)
        if account:
            adgroups = adgroups.filter("account =",account)      
            
        if campaigns:
            adgroups = adgroups.filter("campaign IN",campaigns)
        elif campaign:      
            adgroups = adgroups.filter("campaign =",campaign)      
        if adunit:
            if isinstance(adunit,db.Model):
                adunit_key = adunit.key()
            else:
                adunit_key = adunit      
            adgroups = adgroups.filter("site_keys =",adunit_key)
        return adgroups.fetch(limit)
        
    @classmethod
    @wraps_nonlists
    def put(self, adgroups):
        put_response = db.put(adgroups)
        
        # Clear cache
        adunits = []
        for adgroup in adgroups:
            adunits.extend(adgroup.site_keys)
        adunits = AdUnitQueryManager.get(adunits)    
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
  
        return put_response

      
class CreativeQueryManager(QueryManager):
    Model = Creative

    @classmethod
    def get_creatives(cls,adgroup=None,ad_type=None,ad_types=None,account=None,deleted=False,limit=50):
        creatives = Creative.all()
        if not (deleted == None):
            creatives = creatives.filter("deleted =", deleted)
        if account:
            creatives = creatives.filter("account =", account)    
        if adgroup:
            creatives = creatives.filter("ad_group =", adgroup)
        if ad_types:
            creatives = creatives.filter("ad_types IN", ad_types)
        if ad_type:
            creatives = creatives.filter("ad_type =", ad_type)

        return creatives.fetch(limit)      

    @classmethod
    def put(cls, creatives):
        if not isinstance(creatives, (list, tuple)):
            creatives = [creatives]
    
        put_response = db.put(creatives)
    
        for creative in creatives:
            # update cache
            adunits = AdUnitQueryManager.get(creative.ad_group.site_keys)
            if adunits:
                AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
                
        return put_response

    @classmethod
    def delete(cls,creatives):
        """ Instead of deleting the entire object, we set a property to deleted """
        if not isinstance(creatives, (list, tuple)):
            creatives = [creatives]
            
        update_list = []    
        for c in creatives:
            c.deleted = True
            update_list.append(c)
        db.put(update_list)
        
class TextCreativeQueryManager(CreativeQueryManager):
    Model = TextCreative
class TextAndTileCreativeQueryManager(CreativeQueryManager):
    Model = TextAndTileCreative
class HtmlCreativeQueryManager(CreativeQueryManager):
    Model = HtmlCreative
class ImageCreativeQueryManager(CreativeQueryManager):
    Model = ImageCreative
