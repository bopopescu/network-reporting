import logging
import random

from google.appengine.api import memcache
from google.appengine.ext import db

from common.utils.query_managers import QueryManager, CachedQueryManager

from advertiser.models import Campaign
from advertiser.models import AdGroup
from advertiser.models import Creative, TextCreative, \
                              TextAndTileCreative, \
                              HtmlCreative,\
                              ImageCreative

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
      
class CampaignStatsCounter(object):
  def __init__(self,campaign):
    self.campaign = campaign
    self.number_of_shards = campaign.counter_shards
  
  @property  
  def count(self):
    keys = [str(e) for e in range(self.number_of_shards)]
    key_prefix = "cnt_%s_"%self.campaign.key()
    cnt_dict = memcache.get_multi(keys,key_prefix,namespace=None)
    logging.info("using: %s shards"%len(cnt_dict))
    return float(sum([long(e) for e in cnt_dict.values()]))/100000
    
  def increment(self,dollars):
    delta = int(dollars*100000)
    
    key = self._get_random_key()
    logging.info("random_key: %s"%key)
    new_value = memcache.incr(key,delta=delta,namespace=NAMESPACE,initial_value=0)
    if not new_value:
      raise Exception("Memcache error")
    return new_value  
  
  def _get_random_key(self):
      salt = random.randint(0,self.number_of_shards-1)
      key = "cnt_%s_%s"%(str(self.campaign.key()),salt)
      return key
      
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
    def delete(cls,creatives):
        """ Instead of deleting the entire object, we set a property to deleted """
        if isinstance(creatives, cls.Model):
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
