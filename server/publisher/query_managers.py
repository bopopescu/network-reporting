import logging

from common.utils.query_managers import QueryManager, CachedQueryManager

from common.utils.decorators import wraps_first_arg, deprecated

from google.appengine.ext import db

from publisher.models import App
from publisher.models import Site as AdUnit
from advertiser.models import Campaign, AdGroup, Creative
import datetime
from reporting.query_managers import StatsModelQueryManager
from google.appengine.api import memcache
from ad_server.debug_console import trace_logging
from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR

from common.constants import MAX_OBJECTS
CACHE_TIME = 5*60

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
            # put context in cache as long as it will fit
            # TODO: fix this so we don't need this hack
            try:
                memcache.set(str(adunit_context.key()), 
                             adunit_context, 
                             namespace="context", 
                             time=CACHE_TIME)
            except:
                pass    
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
    def get_apps(cls,account=None,deleted=False,limit=MAX_OBJECTS, alphabetize=False):
        apps = cls.Model.all().filter("deleted =",deleted)
        if account:
            apps = apps.filter("account =",account)
            if alphabetize:
                apps = apps.order("name")
        return apps.fetch(limit)    

    @classmethod
    def reports_get_apps(cls, account=None, publisher=None, advertiser=None, deleted=False, limit=MAX_OBJECTS):
        '''Given account or pub, or adv or some combination thereof return a list of apps that (correctly) 
        correspond to the inputs and things'''
        apps = App.all()
        if deleted is not None:
            apps = apps.filter("deleted =", deleted)
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
                apps.add(adunit.app.key())
            return list(App.get(apps))
            
        #if publisher has been set then everything makes no sense so just ignore it and pass it back or something
        # huh?
        if publisher:
            return [publisher]

        if account:
            apps = apps.filter('account =', account)
        return [app for app in apps]
        
    def put_apps(self,apps):
        return db.put(apps)    

    @classmethod
    @wraps_first_arg
    def put(cls, apps):
        put_response = db.put(apps)
    
        # Clear cache
        for app in apps:
            adunits = AdUnitQueryManager.get_adunits(app=app)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
    
        return put_response
        
    @classmethod
    def update_config_and_put(cls, app, network_config):
        """ Updates the network config and the associated app"""
        db.put(network_config)
        app.network_config = network_config
        cls.put(app)
        
class AdUnitQueryManager(QueryManager):
    Model = AdUnit
    
    @classmethod
    def get_adunits(cls,app=None,account=None,keys=None,deleted=False,limit=MAX_OBJECTS):
        if keys is not None:
            if type(keys) == list and len(keys) == 0:
                return []
            elif len(keys) > 0:
                objs = cls.Model.get(keys)
                return [obj for obj in objs if obj.deleted == deleted]
            else:
                logging.error('len is negative?')

        adunits = AdUnit.all().filter("deleted =",deleted)
        if app:
            adunits = adunits.filter("app_key =",app)
        if account:
            adunits = adunits.filter("account =",account)      
        return adunits.fetch(limit)

    @classmethod
    def reports_get_adunits(cls, account=None, publisher=None, advertiser=None, deleted=False):
        '''Given an account or publisher or advertiser return a list of adunits targeted by 
        the advertiser(s) and/or linked to the publisher(s)'''
        adunits = AdUnit.all().filter('deleted =', deleted)
        #do first
        if publisher:
            adunits = adunits.filter('app_key =', publisher)

        if advertiser:
            #we have advertisers, so don't target ALL adunits for a user, target only
            # those that are specified by advertisers

            #make advertiser a list (this has to do with how I plan on implementing network priority
            # and stuff) if it isn't already one
            temp_aus = []
            if not isinstance(advertiser, list):
                advertiser = [advertiser]
            for adv in advertiser:
                # this is how campaigns reference adgroups
                if hasattr(adv, 'adgroups'):
                    adgroups = adv.adgroups
                # this is how creatives reference adgroups
                elif hasattr(adv, 'adgroup'):
                    adgroups = [adv.adgroup]
                else:
                    #This doesn't make sense (but better safe than sorry!)
                    adgroups = advertiser
                # iterate over the adgroups (I think this is always just one though...?)
                # check if iterable
                try:
                    #this will throw a type error if not iterable
                    for a in adgroups:
                        #if it is iterable who cares, don't waste time iterating over it
                        break
                except TypeError:
                    #make it iterable
                    adgroups = [adgroups]
                for ag in adgroups:
                    #iterate over adgroup adunit targets
                    for key in ag.site_keys:
                        #if this isn't in the adunits list yet, put it there
                        if key not in temp_aus:
                            temp_aus.append(key)
            adunits = set([a.key() for a in adunits])
            #turn string refs into actual objects
            adunits = adunits.intersection(set(temp_aus))
            adunits = AdUnit.get(list(adunits))

        if account and not publisher and not advertiser:
            adunits = adunits.filter('account =', account)
        #publisher can only be an app or adunit, and two adunits is dumb
        # also do publisher after because we can filter much faster with advertiser data than the deleted stuff
        return [au for au in adunits]

    @classmethod 
    def put_adunits(cls,adunits):
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
    @classmethod
    @wraps_first_arg
    def put(cls, adunits):
        if not isinstance(adunits, (list, tuple)):
            adunits = [adunits]

        put_response = db.put(adunits)
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
        
        return put_response
        
    @classmethod
    def update_config_and_put(cls, adunit, network_config):
        """ Updates the network config and the associated app"""
        db.put(network_config)
        adunit.network_config = network_config
        cls.put(adunit)
        
    
