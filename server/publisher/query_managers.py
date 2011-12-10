import logging
import hashlib

from hypercache import hypercache
import datetime

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
from ad_server.adunit_context.adunit_context import AdUnitContext, CreativeCTR
from common.constants import MAX_OBJECTS
CACHE_TIME = 0 # turned off caching

class AdUnitContextQueryManager(CachedQueryManager):
    """ Keeps an up-to-date version of the AdUnit Context in memcache.
    Deleted from memcache whenever its components are updated."""
    Model = AdUnitContext

    @classmethod
    def cache_get_or_insert(cls, adunit_key):
        """ Takes an AdUnit key, tries both hypercache and memcache, if found
            neither, builds the context from the datastore.

            This assumes that any stale adunit_context objects have been removed
            from memcache using cache_delete_from_adunits.
            """
        adunit_key = str(adunit_key).replace("'","")
        adunit_context_key = AdUnitContext.key_from_adunit_key(adunit_key)

        memcache_ts = memcache.get(adunit_context_key, namespace="context-timestamp")
        hypercached_context = hypercache.get(adunit_context_key)

        # We can return our hypercached context if nothing in memcache changed yet
        if hypercached_context and (hypercached_context._hyper_ts == memcache_ts):
            return hypercached_context

        trace_logging.warning("hypercache miss: fetching adunit_context from memcache")

        # Something has changed, let's get the new memcached context
        adunit_context = memcache.get(adunit_context_key, namespace="context")

        if adunit_context is None:
            trace_logging.warning("memcache miss: fetching adunit_context from db")
            # get adunit from db
            adunit = AdUnit.get(adunit_key)
            # wrap context
            adunit_context = AdUnitContext.wrap(adunit)
            memcache.set(adunit_context_key,
                         adunit_context,
                         namespace="context",
                         time=CACHE_TIME)
            new_timestamp = datetime.datetime.now()
            memcache.set(adunit_context_key, new_timestamp, namespace="context-timestamp")
        else:
            new_timestamp = memcache_ts

        # We got new information for the hypercache, give it a new timestamp
        adunit_context._hyper_ts = new_timestamp
        hypercache.set(adunit_context_key, adunit_context)

        return adunit_context




    @classmethod
    def cache_delete_from_adunits(cls, adunits):
        """ This is called whenever something modifies an adunit_context.
            Removes both the context and its digest from memcache in
            order to maintain an up-to-date value in the cache. """
        if not isinstance(adunits, list):
          adunits = [adunits]
        keys = ["context:"+str(adunit.key()) for adunit in adunits]
        logging.info("deleting from cache: %s"%keys)
        success = memcache.delete_multi(keys, namespace="context")
        ts_success = memcache.delete_multi(keys, namespace="context-timestamp")

        logging.info("deleted: %s" % success and ts_success)
        return success

class AppQueryManager(QueryManager):
    Model = App

    @classmethod
    def get_app_by_key(cls, key):
        app = cls.Model.get(key)
        return app

    @classmethod
    def get_apps(cls, account=None, deleted=False, limit=MAX_OBJECTS, alphabetize=False, offset=None, keys_only = False):
        apps = cls.Model.all(keys_only = keys_only).filter("deleted =", deleted)
        if account:
            apps = apps.filter("account =", account)
            if alphabetize:
                apps = apps.order("name")
        if offset:
            apps = apps.filter("__key__ >", offset)
        return apps.fetch(limit)

    @classmethod
    def get_app_keys(cls, account=None, deleted=False, limit=MAX_OBJECTS, alphabetize=False, offset=None):
        return cls.get_apps(account, deleted, limit, alphabetize, offset, keys_only = True)

    @classmethod
    def get_all_apps(cls, account=None, deleted=False, alphabetize=False):
        num_apps = 0
        apps = cls.get_apps(limit=1000)
        while len(apps) > num_apps:
            num_apps = len(apps)
            apps.extend(cls.get_apps(limit=1000, offset=apps[-1].key()))
        return apps

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
        return apps

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

    @classmethod
    def get_apps_with_network_configs(cls, account):
        return App.all().filter('account =', account).filter(
                'network_config !=', None)

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
        return adunits

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

