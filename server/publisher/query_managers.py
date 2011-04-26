import logging

from common.utils.query_managers import QueryManager, CachedQueryManager
from advertiser.query_managers import CampaignStatsCounter

from google.appengine.ext import db

from publisher.models import App
from publisher.models import Site as AdUnit
from advertiser.models import Campaign, AdGroup, Creative
import datetime
from reporting.query_managers import StatsModelQueryManager
from google.appengine.api import memcache

from ad_server.debug_console import trace_logging

from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR
        
class AdUnitContextQueryManager(CachedQueryManager):
    """ Keeps an up-to-date version of the AdUnit Context in memcache.
    Deleted from memcache whenever its components are updated."""
    Model = AdUnitContext

    @classmethod
    def cache_get_or_insert(cls,adunit_key):
        """ Takes an AdUnit key, gets or builds the context """
        adunit_key = str(adunit_key).replace("'","")
        adunit_context_key = "context:"+str(adunit_key)
        adunit_context = memcache.get(adunit_context_key, namespace="context")
        if adunit_context is None:
            trace_logging.warning("fetching adunit from db")
            # get adunit from db
            adunit = AdUnit.get(adunit_key)
            # wrap context
            adunit_context = AdUnitContext.wrap(adunit)
            # put context in cache
            memcache.set(str(adunit_context.key()), adunit_context, namespace="context")
        else:
            trace_logging.warning("found adunit in cache")    
        return adunit_context
        
    @classmethod
    def cache_delete_from_adunits(cls, adunits):
        if not isinstance(adunits,list):
          adunits = [adunits]
        keys = ["context:"+str(adunit.key()) for adunit in adunits]  
        logging.info("deleting from cache: %s"%keys)
        success = memcache.delete_multi(keys,namespace="context")
        logging.info("deleted: %s"%success)
        return success

class AppQueryManager(QueryManager):
    Model = App
    
    @classmethod
    def get_apps(cls,account=None,deleted=False,limit=50, alphabetize=False):
        apps = cls.Model.all().filter("deleted =",deleted)
        if account:
            apps = apps.filter("account =",account)
            if alphabetize:
                apps = apps.order("name")
        return apps.fetch(limit)    

class AdUnitQueryManager(QueryManager):
    Model = AdUnit
    
    @classmethod
    def get_adunits(cls,app=None,account=None,keys=None,deleted=False,limit=50):
        if keys is not None:
            if type(keys) == list and len(keys) == 0:
                return []
            elif len(keys) > 0:
                return cls.Model.get(keys)
            else:
                logging.error('len is negative?')

        adunits = AdUnit.all().filter("deleted =",deleted)
        if app:
            adunits = adunits.filter("app_key =",app)
        if account:
            adunits = adunits.filter("account =",account)      
        return adunits.fetch(limit)

