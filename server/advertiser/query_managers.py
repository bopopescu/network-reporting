import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db

from common.utils.query_managers import QueryManager, CachedQueryManager
from common.utils.decorators import wraps_first_arg

from advertiser.models import Campaign
from advertiser.models import AdGroup
from advertiser.models import Creative, TextCreative, \
                              TextAndTileCreative, \
                              HtmlCreative,\
                              ImageCreative

from publisher.models import App
from publisher.models import Site as AdUnit
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

NAMESPACE = None

CAMP_PRIORITIES = ('gtee', 'gtee_high', 'gtee_low', 'promo', 'network', 'backfill_promo')

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
    @wraps_first_arg
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
    

    @classmethod 
    def reports_get_campaigns(cls, account=None, publisher=None, advertiser=None, deleted=False, by_priority=False):
        if advertiser:
            # advertiser as list means priority level, return all these camps 
            # because we want stuff for those campaigns individually
            if type(advertiser) == list:
                return advertiser
            else:
                logging.error("this makes no sensssseeeee")
                return advertiser

        if publisher:
            #publisher is either an app or an adunit, assume it's an adunit first and make it a list
            adunits = [publisher]
            if hasattr(publisher, 'all_adunits'):
                #if it's not an adunit, make it  
                adunits = publisher.all_adunits
            adgroups = AdGroup.all().filter('site_keys IN', [a for a in adunits])
            #adgroups = AdGroup.all().filter('site_keys IN', [a.key() for a in adunits])
            adgroups = [a for a in adgroups if a.deleted == deleted]
            camps = [adgroup.campaign for adgroup in adgroups]
            if by_priority:
                temp = []
                for p in CAMP_PRIORITIES:
                    priority_camps = [c for c in camps if c.campaign_type == p]
                    if len(priority_camps) > 0:
                        temp.append(priority_camps)
                camps = temp
            return camps

        camps = Campaign.all().filter('deleted =', deleted)
        if account:
            camps = camps.filter('account = ', account)
        #turn a list of campaigns into a list of lists where each list is all
        #campagins at a given priority level
        if by_priority:
            temp = []
            for p in CAMP_PRIORITIES:
                priority_camps = [c for c in camps if c.campaign_type == p]
                if len(priority_camps) > 0:
                    temp.append(priority_camps)
            camps = temp
        return camps

class AdGroupQueryManager(QueryManager):
    Model = AdGroup   
        
    @classmethod
    def get_adgroups(cls, campaign=None, campaigns=None, adunit=None, app=None, account=None, deleted=False, limit=50):
        adgroups = AdGroup.all()
        if deleted:
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
        
        if app:
            adgroups_dict = {}
            adunits = AdUnitQueryManager.get_adunits(app=app)
            for adunit in adunits:
                adgroups_per_adunit = cls.get_adgroups(adunit=adunit, limit=limit)
                for adgroup in adgroups_per_adunit:
                    adgroups_dict[adgroup.key()] = adgroup
            return adgroups_dict.values()[:limit]
            
        return adgroups.fetch(limit)
        
    @classmethod
    @wraps_first_arg
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

    def put_creatives(self,creatives):
        return db.put(creatives)

    @classmethod
    def reports_get_creatives(cls, account=None, publisher=None, advertiser=None, deleted=False):
        adgroups = []
        if advertiser:
            if type(advertiser) != list:
                advertiser = [advertiser]
            for adv in advertiser:
                adgroups += adv.adgroups

        if publisher:
            adunits = [publisher]
            if hasattr(publisher, 'all_adunits'):
                adunits = [au for au in publisher.all_adunits]
            pub_ags = AdGroup.all().filter('site_keys IN', adunits)
            pub_ags = [a for a in pub_ags if a.deleted == deleted]
            if adgroups:
                if len(pub_ags) >= len(adgroups):
                    adgroups = [a for a in pub_ags if a in adgroups]
                elif len(pub_ags) < len(adgroups):
                    adgroups = [a for a in adgroups if a in pub_ags]
                else:
                    logging.error("That's Impossible")
            else:
                adgroups = pub_ags
        if adgroups:
            return reduce(lambda x, y: x+y, [[c for c in ag.creatives] for ag in adgroups])
        crtvs = Creative.all().filter('deleted =', deleted).filter('account =', account)
        return crtvs

        

    @classmethod
    @wraps_first_arg
    def put(cls, creatives):
        put_response = db.put(creatives)
    
        for creative in creatives:
            # update cache
            adunits = AdUnitQueryManager.get(creative.ad_group.site_keys)
            if adunits:
                AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
                
        return put_response
        
        
class TextCreativeQueryManager(CreativeQueryManager):
    Model = TextCreative
class TextAndTileCreativeQueryManager(CreativeQueryManager):
    Model = TextAndTileCreative
class HtmlCreativeQueryManager(CreativeQueryManager):
    Model = HtmlCreative
class ImageCreativeQueryManager(CreativeQueryManager):
    Model = ImageCreative
