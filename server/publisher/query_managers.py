import logging
import hashlib
import re

from hypercache import hypercache
import datetime
import urllib2
import time

from google.appengine.ext import db
from google.appengine.api import memcache, taskqueue

from ad_server.debug_console import trace_logging
import os

from ad_server.adunit_context.adunit_context import AdUnitContext

from advertiser.models import Campaign, AdGroup, Creative
from common.constants import MAX_OBJECTS
from common.utils.decorators import wraps_first_arg

from common.utils.query_managers import QueryManager, CachedQueryManager
from hypercache import hypercache
from publisher.models import App
from publisher.models import Site as AdUnit
from reporting.query_managers import StatsModelQueryManager

from adserver_constants import USER_PUSH_URL, ADSERVER_ADMIN_HOSTNAME


CACHE_TIME = 0 # turned off cache expiration

#TODO(tornado): This needs to be a url that we'll actually use
TEST_ADSERVER = 'localhost:8000'
AUC_CLEAR_URI = '/gae/adunit_context_clear'

IAD = 'iad'
APPLE_DEVICES = ('iphone', 'ipad')
IAD_URL = 'http://itunes.apple.com.*'
ALL_NETWORKS = 'default'

class AdUnitContextQueryManager(CachedQueryManager):
    """ Keeps an up-to-date version of the AdUnit Context in memcache.
    Deleted from memcache whenever its components are updated."""
    Model = AdUnitContext

    @classmethod
    def get_context(cls, adunit_key):
        adunit = AdUnit.get(adunit_key)
        adunit_context = AdUnitContext.wrap(adunit)
        return adunit_context

    @classmethod
    def cache_get_or_insert(cls, adunit_key):
        """ Takes an AdUnit key, tries both hypercache and memcache, if found
            neither, builds the context from the datastore.

            This assumes that any stale adunit_context objects have been removed
            from memcache using cache_delete_from_adunits.
            """
        # TODO(simon): This will eventually change to just get from the datastore, with no memcaching.
        # ...assuming that this will only be used for the AdUnitContext fetch service.

        adunit_key = str(adunit_key).replace("'","")
        adunit_context_key = AdUnitContext.key_from_adunit_key(adunit_key)

        memcache_ts = memcache.get("ts:%s" % adunit_context_key)
        hypercached_context = hypercache.get(adunit_context_key)

        # We can return our hypercached context if nothing in memcache changed yet
        if hypercached_context and (hypercached_context._hyper_ts == memcache_ts):
            return hypercached_context

        trace_logging.warning("hypercache miss: fetching adunit_context from memcache")

        # Something has changed, let's get the new memcached context
        adunit_context = memcache.get(adunit_context_key)

        if adunit_context is None:
            trace_logging.warning("memcache miss: fetching adunit_context from db")
            try:
                adunit_context = cls.get_context(adunit_key)
                memcache.set(adunit_context_key,
                             adunit_context,
                             time=CACHE_TIME)
                new_timestamp = datetime.datetime.now()
                memcache.set("ts:%s" % adunit_context_key, new_timestamp)
            except: # Datastore timeouts usually
                pass
        else:
            new_timestamp = memcache_ts

        # We got new information for the hypercache, give it a new timestamp


        if adunit_context:
            context_created_at = getattr(adunit_context, 'created_at', None)
            if context_created_at is None:
                now = int(time.mktime(datetime.datetime.utcnow().timetuple()))
                adunit_context.created_at = now
                memcache.set(adunit_context_key,
                             adunit_context,
                             time=CACHE_TIME)
                memcache.set("ts:%s" % adunit_context_key, new_timestamp)

            adunit_context._hyper_ts = new_timestamp
            hypercache.set(adunit_context_key, adunit_context)

        return adunit_context

    @classmethod
    def cache_delete_from_adunits(cls, adunits, testing=False, fetcher=None, port=None):
        """ This is called whenever something modifies an adunit_context.
            Removes both the context and its digest from memcache in
            order to maintain an up-to-date value in the cache. """
        # TODO(simon): We need to make this method make an API call to the AWS/Tornado servers
        #   to tell them to clear the AdUnitContext from their caches.
        if not isinstance(adunits, list):
          adunits = [adunits]

        if len(adunits) > 0 and isinstance(adunits[0], str):
            keys = ["context:"+adunit for adunit in adunits]
            adunit_keys = adunits
        else:
            keys = ["context:"+str(adunit.key()) for adunit in adunits]
            adunit_keys = [str(adunit.key()) for adunit in adunits]

        clear_keys = ["adunit_key=%s" % key for key in adunit_keys]
        clear_uri = AUC_CLEAR_URI + '?' + '&'.join(clear_keys)

        if testing and fetcher:
            clear_uri = clear_uri + '&testing=True&port=%s' % port
            fetcher.fetch(clear_uri)
        else:
            #TODO(tornado): THIS IS COMMENTED OUT, NEED TO IMPLEMENT
            # WHEN SHIT IS LIVE FOR REAL
            queue = taskqueue.Queue()
            task = taskqueue.Task(url='/fetch_api/adunit_update_fanout',
                                  method='POST',
                                  params={'adunit_keys': adunit_keys})
            queue.add(task)

        logging.info("Deleting from memcache: %s" % keys)
        success = memcache.delete_multi(keys)
        ts_success = memcache.delete_multi(["ts:%s" % k for k in keys])

        logging.info("Deleted from memcache: %s" % (success and ts_success))
        return success


class PublisherQueryManager(CachedQueryManager):
    @classmethod
    def get_objects_dict_for_account(cls, account):
        """
        Returns a dictionary mapping App keys to App entities carrying adunit data. Adunits for each
        app can be retrieved as a list by using app.adunits.
        """
        apps_dict = cls.get_apps_dict_for_account(account)
        adunits = cls.get_adunits_dict_for_account(account).values()

        for app in apps_dict.values():
            app.adunits = []

        # Associate each ad unit with its app. We could have done this by looping through the apps
        # and getting each app's ad units, but that has a lot of GET overhead.
        for adunit in adunits:
            # Looks weird, but we're just avoiding adunit.app_key.key() since it incurs a fetch.
            app_key = str(AdUnit.app_key.get_value_for_datastore(adunit))
            app_for_this_adunit = apps_dict[app_key]
            app_for_this_adunit.adunits += [adunit]

        return apps_dict

    @classmethod
    def get_apps_dict_for_account(cls, account, include_deleted=False):
        return cls.get_entities_for_account(account, App, include_deleted)

    @classmethod
    def get_adunits_dict_for_account(cls, account, include_deleted=False):
        return cls.get_entities_for_account(account, AdUnit, include_deleted)


class AppQueryManager(CachedQueryManager):
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
    def get_all_apps(cls, **kwargs):
        """
        kwargs: account=None, deleted=False, alphabetize=False
        """
        num_apps = 0
        apps = cls.get_apps(limit=1000, **kwargs)
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

        # Invalidate cache entries as necessary.
        affected_account_keys = set()
        for app in apps:
            adunits = AdUnitQueryManager.get_adunits(app=app)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
            affected_account_keys.add(App.account.get_value_for_datastore(app))

        # For each account, clear its apps and adunits from memcache.
        PublisherQueryManager.memcache_flush_entities_for_account_keys(affected_account_keys, App)
        PublisherQueryManager.memcache_flush_entities_for_account_keys(affected_account_keys, AdUnit)

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

    @classmethod
    def get_apps_without_pub_ids(cls, account, networks):
        """
        Take account and list of network names.

        Return dictionary where the keys are the network names and the values
        are lists of apps where the pub_ids for that network haven't been set.
        """
        apps = {ALL_NETWORKS: []}
        for network in networks:
            apps[network] = []

        for app in App.all().filter('account =', account):
            if hasattr(app, 'network_config'):
                network_config = app.network_config
                for network in networks:
                    # iAd only supports apple devices
                    if network == IAD:
                        if app.app_type in APPLE_DEVICES:
                            apps[network].append(app)
                    elif not hasattr(network_config, network + '_pub_id') or \
                            not getattr(network_config, network + '_pub_id',
                                    None):
                        apps[network].append(app)
            else:
                apps[ALL_NETWORKS].append(app)
        return apps

    @classmethod
    def get_iad_pub_id(self, account, app_name):
        for app in App.all().filter('account =', account).filter('name =',
                app_name):
            if getattr(app, 'url', None) and re.match(IAD_URL, app.url):
                ids = re.findall('/id[0-9]*\?', app.url)
                if ids:
                    pub_id = ids[0][len('/id'):-1]
                    return pub_id

    @classmethod
    def get_iad_pub_ids(cls, account, include_apps=False):
        """ Get the iAd pub id from the app's url field.

        Return the pub ids and potentialy apps as a generator.
        """
        for app in App.all().filter('account =', account):
            if getattr(app, 'url', None) and re.match(IAD_URL, app.url):
                logging.info(app.name)
                ids = re.findall('/id[0-9]*\?', app.url)
                if ids:
                    pub_id = ids[0][len('/id'):-1]
                    logging.info(pub_id)
                    if include_apps:
                        yield app, pub_id
                    else:
                        yield pub_id

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

        affected_account_keys = set()
        for adunit in adunits:
            affected_account_keys.add(AdUnit.account.get_value_for_datastore(adunit))

        PublisherQueryManager.memcache_flush_entities_for_account_keys(affected_account_keys, AdUnit)

        return put_response

    @classmethod
    def update_config_and_put(cls, adunit, network_config):
        """ Updates the network config and the associated app"""
        db.put(network_config)
        adunit.network_config = network_config
        cls.put(adunit)

