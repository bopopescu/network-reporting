import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db

from common.utils.query_managers import QueryManager, CachedQueryManager
from common.utils.decorators import wraps_first_arg
from common.constants import CAMPAIGN_LEVELS

from advertiser.models import Campaign
from advertiser.models import AdGroup
from advertiser.models import Creative, TextCreative, \
                              TextAndTileCreative, \
                              HtmlCreative,\
                              ImageCreative

from publisher.models import App, AdUnit
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

import copy

from common.constants import MAX_OBJECTS

NAMESPACE = None

MAX_ALLOWABLE_QUERIES = 30

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

class CampaignQueryManager(QueryManager):
    Model = Campaign

    @classmethod
    def get_marketplace_campaign(cls, adunit=None):
        """ Returns a marketplace campaign for this adunit, 
            Creatives a new campaign if one doesn't exist already
            """
        if adunit is None:
            return None
        camps = cls.get_campaigns(account=adunit.account)
        mkcamp = filter(lambda camp: camp.campaign_type == 'marketplace', camps)
        if mkcamp:
            ag = camp.adgroups
            if adunit.key() not in ag.site_keys:
                ag.site_keys.append(adunit.key())
                ag.put()
            mkcamp.put()
            return mkcamp
        else:
            return cls.add_marketplace_campaign(cls, adunit=adunit)

    @classmethod
    def add_marketplace_campaign(cls, adunit=None):
            """ Adds a marketplace campagin for this adunit
                """
            acct = adunit.account
            camp = Campaign(name = 'Marketplace Campaign',
                                    campaign_type = 'marketplace',
                                    account = acct,
                                    )
            camp.put()
            ag = AdGroup(campaign = camp,
                                 account = acct,
                                 name = 'Marketplace adgroup',
                                 site_keys = [adunit.key()],
                                 )
            ag.put()
            creative = adgroup.default_creative()
            creative.account = acct
            creative.put()
            return camp
               
    @classmethod
    def get_campaigns(cls,account=None,adunit=None,deleted=False,limit=MAX_OBJECTS):
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
            if deleted is not None:
                adgroups = [a for a in adgroups if a.deleted == deleted]
            camps = [adgroup.campaign for adgroup in adgroups]
            if by_priority:
                temp = []
                for p in CAMPAIGN_LEVELS:
                    priority_camps = [c for c in camps if c.campaign_type == p]
                    if len(priority_camps) > 0:
                        temp.append(priority_camps)
                camps = temp
            return camps

        if deleted is not None:
            camps = Campaign.all().filter('deleted =', deleted)
        if account:
            camps = camps.filter('account = ', account)
        #turn a list of campaigns into a list of lists where each list is all
        #campagins at a given priority level
        if by_priority:
            temp = []
            for p in CAMPAIGN_LEVELS:
                priority_camps = [c for c in camps if c.campaign_type == p]
                if len(priority_camps) > 0:
                    temp.append(priority_camps)
            camps = temp
        return camps

class AdGroupQueryManager(QueryManager):
    Model = AdGroup   
        
    @classmethod
    def get_adgroups(cls, campaign=None, campaigns=None, adunit=None, app=None, account=None, deleted=False, limit=MAX_OBJECTS):
        adgroups = AdGroup.all()
        if not (deleted == None):
            adgroups = adgroups.filter("deleted =",deleted)
        if account:
            adgroups = adgroups.filter("account =",account)      
            
        if campaigns:
            # if the number of campaigns is greater than 30 we must "chunk" the query
            if len(campaigns) > MAX_ALLOWABLE_QUERIES:
                total_adgroups = []
                for sub_campaigns in chunks(campaigns,MAX_ALLOWABLE_QUERIES):
                    adgroups_current = copy.deepcopy(adgroups)
                    total_adgroups += adgroups_current.filter("campaign IN", sub_campaigns).\
                                        fetch(limit)
                return total_adgroups    
            else:    
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
    def get_creatives(cls,adgroup=None,ad_type=None,ad_types=None,account=None,deleted=False,limit=MAX_OBJECTS):
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
        #Advertiser will always be a campaign or a list of campaigns
        if advertiser:
            if not isinstance(advertiser, list):
                advertiser = [advertiser]
            for adv in advertiser:
                adgroups += adv.adgroups
        if publisher:
            adunits = [publisher]
            if hasattr(publisher, 'all_adunits'):
                adunits = [au for au in publisher.all_adunits]
            pub_ags = AdGroup.all().filter('site_keys IN', adunits)
            if deleted is not None:
                pub_ags = [a for a in pub_ags if a.deleted == deleted]
            #collect all the adgroups for the publisher and the advertiser
            #make sure to only take the intersection of the sets
            if adgroups:
                final = []
                for pub_ag in pub_ags:
                    for ag in adgroups:
                        if pub_ag.key() == ag.key():
                            final.append(pub_ag)
                adgroups = final
            else:
                adgroups = pub_ags
        if adgroups:
            return reduce(lambda x, y: x+y, [[c for c in ag.creatives] for ag in adgroups])
        crtvs = Creative.all().filter('account =', account)
        if deleted is not None:
            crtvs = crtvs.filter('deleted =', deleted)
        return [c for c in crtvs]

        

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
