from django.conf import settings

import datetime
import logging
import time
import copy
import traceback
from urllib import urlopen
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        from django.utils import simplejson as json


from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.ext.db import InternalError, Timeout
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError

import reporting.models as reporting_models

from common.utils.query_managers import CachedQueryManager
from common.utils import date_magic
from common.utils.helpers import chunks
from reporting.models import SiteStats, StatsModel, BlobLog
from reporting import mongostats
from advertiser.models import Creative
from publisher.models import Site as AdUnit


# maximum number of objects per batch put
LIMIT = 200
# object cache miss sentinel for StatsModelQueryManager
SENTINEL = '!!!'
# max number of retries for offline batch put
MAX_RETRIES = 3

#blobkey:date:acct
BLOBLOG_KEY = 'blobkey:%s:%s'


class SiteStatsQueryManager(CachedQueryManager):
    def get_sitestats_for_days(self, site=None, owner=None, days=None):
        if isinstance(site,db.Model):
          site_key = site.key()
        else:
          site_key = site
        if isinstance(owner,db.Model):
          owner_key = owner.key()
        else:
          owner_key = owner

        days = days or None
        keys = (SiteStats.get_key(site_key, owner_key, d) for d in days)
        stats = SiteStats.get(keys) # db get
        stats = [s or SiteStats() for s in stats]
        return stats


class BlobLogQueryManager():

    def put_bloblog(self, date, blob_key, account=None):
        bloblog = BlobLog(date=date, blob_key=blob_key, account=account)
        return bloblog.put()

    @classmethod
    def get_blobkeys_for_days(cls, days, account_key):
        #for all the days, turn them into YYMMDD and then use that to construct the key, then with all those keys get all the BlobLogs, then with all those bloblogs, return only a list of the blob_keys associated with them
        keys = [BLOBLOG_KEY % (day.strftime('%y%m%d'), account_key) for day in days]
        # get_by_key_name returns None for every key that doesn't exist, get ride of these Nones
        return map(lambda bloblog: bloblog.blob_key, filter(lambda bl: bl is not None, BlobLog.get_by_key_name(keys)))
        # I guess we should also do something involving saying "Hey data you want doesn't exist.."but w/e

        #(for nafis)
        #return [blob.blob_key for blob in BlobLog.get([db.Key(BLOBLOG_KEY % day.strftime('%y%m%d')) for day in days])]


class StatsModelQueryManager(CachedQueryManager):
    Model = StatsModel

    def __init__(self, account, offline=False, include_geo=False):
        #Hack to keep account object for mongo stats
        self.account_obj = account
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        else:
            self.account = db.Key(account)

        self.offline = offline

        self.stats = []
        self.obj_cache = {}
        self.all_stats_deltas = [StatsModel()]
        self.include_geo = include_geo

    def get_stats_for_apps(self, apps, days=None, num_days=30):
        days = days or StatsModel.lastdays(num_days)
        account_app_dict = {}
        # we bucket the apps per account since we know
        # behind the scenes this is how our data is stored
        for app in apps:
            if not app.account.key() in account_app_dict:
                account_app_dict[app.account.key()] = []
            account_app_dict[app.account.key()].append(app)

        stats = []
        for account,apps in account_app_dict.iteritems():
            stats += self.get_stats_for_days(publishers=apps,account=account,days=days,use_mongo=False)

        return stats

    def get_stats_for_hours(self,
                            publisher=None,
                            advertiser=None,
                            date_hour=None,
                            date_hours=None,
                            account=None,
                            country=None,
                            offline=False):
        """
        date_hour is a datetime object
        date_hours are a list of datetime objects
        """
        offline = offline or self.offline
        account = account or self.account

        if isinstance(publisher,db.Model):
          publisher = publisher.key()

        if isinstance(advertiser,db.Model):
          advertiser = advertiser.key()

        if date_hour:
            multiple = False
            date_hours = [date_hour]
        else:
            multiple = True

        if account:
            parent = db.Key.from_path(StatsModel.kind(),StatsModel.get_key_name(account=account,offline=offline))
        else:
            parent = None

        keys = [db.Key.from_path(StatsModel.kind(),
                                 StatsModel.get_key_name(publisher=publisher,
                                                         advertiser=advertiser,
                                                         account=account,
                                                         date_hour=dt,
                                                         country=country,
                                                         offline=offline),
                                  parent=parent)
                    for dt in date_hours]

        stats = StatsModel.get(keys) # db get
        # all_keys = [s.key() for s in StatsModel.all().fetch(100)]
        # print all_keys
        # print keys
        # print keys[0] in all_keys
        stats = [s or StatsModel() for s in stats]

        if not multiple:
            return stats[0]
        else:
            return stats

    def get_stats_for_days(self,
                           publisher=None,
                           publishers=None,
                           advertiser=None,
                           days=None,
                           num_days=None,
                           account=None,
                           country=None,
                           offline=False,
                           date_fmt='date',
                           use_mongo=False if settings.DEBUG else True):
        """
        Gets the stats for a specific pairing. Definitions:
        advertiser_group: Either Campaign, AdGroup or Creative
        publisher_group: Either App, or Site(AdUnit)
        """
        offline = offline or self.offline

        if isinstance(publisher,db.Model):
          publisher = publisher.key()

        if isinstance(advertiser,db.Model):
          advertiser = advertiser.key()

        if num_days:
            days = StatsModel.lastdays(num_days)
        else:
            days = days or []

        account = account or self.account


        # in order to use the keys for a lookup we need the parent,
        # publisher or advertiser and days
        # NOTE: publisher=None and advertiser=None and day=Something is actually valid
        #       this is basically the rollup for the entire account, but just not supported
        #       in this QM
        if account:
            parent = db.Key.from_path(StatsModel.kind(),StatsModel.get_key_name(account=account,offline=offline))
        else:
            parent = None

        # if going to use mongo we want offline = False in case we need to pull the unique user counts info
        # Note: fixing uniq user stats updater bug moving forward starting 1/20/2012
        if not offline and self.account_obj and self.account_obj.display_mongo and use_mongo:
            parent = db.Key.from_path(StatsModel.kind(),StatsModel.get_key_name(account=account,offline=True))

        if publishers:
            keys = [db.Key.from_path(StatsModel.kind(),
                                     StatsModel.get_key_name(publisher=publisher,
                                                             advertiser=advertiser,
                                                             account=account,
                                                             date=d,    # date is overloaded; type defined by date_fmt
                                                             country=country,
                                                             brand_name=None,
                                                             marketing_name=None,
                                                             device_os=None,
                                                             device_os_version=None,
                                                             offline=offline,
                                                             date_fmt=date_fmt),
                                      parent=parent)
                        for d in days
                            for publisher in publishers]
        else:
            keys = [db.Key.from_path(StatsModel.kind(),
                                     StatsModel.get_key_name(publisher=publisher,
                                                             advertiser=advertiser,
                                                             account=account,
                                                             date=d,    # date is overloaded; type defined by date_fmt
                                                             country=country,
                                                             brand_name=None,
                                                             marketing_name=None,
                                                             device_os=None,
                                                             device_os_version=None,
                                                             offline=offline,
                                                             date_fmt=date_fmt),
                                      parent=parent)
                        for d in days]


        #### BEGIN USE MONGOSTATS API ####

        # we only want to get our data from mongostats API if we are not explicitly trying
        # to get offline data (from GAE, i.e. 'offline=True') or explicitly don't want
        # data from mongo
        # TODO: remove this conditional so that we always use mongo data in all of our UI
        #       including the admin page
        if not offline and self.account_obj and self.account_obj.display_mongo and use_mongo:
            realtime_stats = mongostats.api_fetch(start_date=days[0],
                                              end_date=days[-1],
                                              account_key=account,
                                              publisher_key=publisher,
                                              advertiser_key=advertiser,
                                              )

            # In order to get unique user counts we must also get the offline stats
            # from the GAE datastore:
            # Currently the UI only needs 'user_count' for the following types of queries
            # (Account-*-*) and (Account-<Any Pub>-*)
            # TODO: remove the if statement so that we always have this data available
            # TODO: monogstats should be able to provide this data as well so we don't have to
            #       do two queries (one to API one Datastore lookup)
            if (account and not publisher and not advertiser) or \
                (account and publisher and not advertiser):

                # db get
                offline_stats = StatsModel.get(keys)

                # we patch the user_count data from the offline stats if possible
                for rt_stat, offline_stat in zip(realtime_stats, offline_stats):
                    rt_stat.user_count = offline_stat.user_count if offline_stat else 0

            return realtime_stats

        #### END USE MONGOSTATS API ####

        days_len = len(days)

        stats = StatsModel.get(keys) # db get
        #since pubs iterates more than once around days, stats might be too long
        #but it should only iterate on MULTIPLES of days_len, so ct mod days_len

        final_stats = []
        for i,(key,stat) in enumerate(zip(keys,stats)):
            if not stat:
                pub_string = key.name().split(':')[1] # k:<publisher>:<advertiser>:<date>
                publisher = db.Key(pub_string) if pub_string else None
                stat = stat or StatsModel(date=datetime.datetime.combine(days[i%days_len],datetime.time()), account=account, publisher=publisher, advertiser=advertiser)
                # if not self.offline:
                #     self._patch_mongodb_stats(stat)
            stat.include_geo = self.include_geo
            final_stats.append(stat)

        return final_stats

    def accumulate_stats(self, stat):
        self.stats.append(stat)


    def put_stats(self, stats=None ,rollup=True, offline=False):
        offline = offline or self.offline

        stats = stats or self.stats

        if isinstance(stats,db.Model):
            stats = [stats]
        if rollup:
            all_stats_deltas = self._get_all_rollups(stats, offline)
        else:
            all_stats_deltas = stats

        all_stats_deltas = self._place_stats_under_account(all_stats_deltas, offline=offline)

        self.all_stats_deltas = all_stats_deltas

        # get or insert from db in order to update as transaction
        def _txn(stats, offline):
            return self._update_db(stats, offline)

        if offline:
            return self._update_db(all_stats_deltas, offline)
        else:
            return db.run_in_transaction(_txn, all_stats_deltas, offline)


    def _update_db(self, stats, offline):
        offline = offline or self.offline
        key_list = []

        if offline:
            all_stats = stats
            page_count = 0
            retries = 0

            account_name = self.account.name()

            while stats and retries <= MAX_RETRIES:
                try:
                    db.put(stats[:LIMIT])
                    # print "putting %i models..." %(len(stats[:LIMIT]))
                    print '%s: %i models' % ((account_name or 'None').rjust(25), len(stats[:LIMIT]))
                    stats = stats[LIMIT:]
                    page_count += 1
                    retries = 0
                except: # (InternalError, Timeout, CapabilityDisabledError):
                    traceback.print_exc()
                    retries += 1
            return [s.key() for s in all_stats[:LIMIT*page_count]] # only return the ones that were successully batch put

        for s in stats:
            stat = db.get(s.key())    # get datastore's stat using key of s
            if stat:    # if exists, update with delta s
                stat += s
            else:       # if doesn't exist, make it with delta s
                stat = s
            key_list.append(stat.put())
        return key_list


    def _get_all_rollups(self, stats, offline):
        offline = offline or self.offline

        # initialize the object dictionary
        stats_dict = {}
        for stat in stats:
            stats_dict[stat.key().name()] = stat


        def _get_refprop_from_cache(entity, prop):
            if prop:
                model = entity.__class__
                key = getattr(model,prop).get_value_for_datastore(entity)
                value = self.obj_cache.get(key,SENTINEL)
                if value == SENTINEL:
                    value = getattr(entity,prop)
                    self.obj_cache[key] = value
                return value
            return None


        def _get_stat(pub=None, adv=None, date_hour=None, date=None, month=None, country=None,
                      brand_name=None, marketing_name=None, device_os=None, device_os_version=None):
            """get or creates the stat from the local dictionary"""
            key = StatsModel.get_key_name(publisher=pub,
                                          advertiser=adv,
                                          date=date,
                                          date_hour=date_hour,
                                          month=month,
                                          country=country,
                                          brand_name=brand_name,
                                          marketing_name=marketing_name,
                                          device_os=device_os,
                                          device_os_version=device_os_version)

            if not key in stats_dict:
                stat =  StatsModel(publisher=pub,
                                   advertiser=adv,
                                   date=date,
                                   date_hour=date_hour,
                                   month=month,
                                   country=country,
                                   brand_name=brand_name,
                                   marketing_name=marketing_name,
                                   device_os=device_os,
                                   device_os_version=device_os_version)
                stats_dict[key] = stat
            else:
                stat = stats_dict[key]
            return stat


        # TODO: Clean this function up a bit
        def make_above_stat(stat,attribute='date'):
            stat.advertiser = _get_refprop_from_cache(stat, 'advertiser')
            stat.publisher = _get_refprop_from_cache(stat, 'publisher')

            if attribute == 'advertiser' and not stat.advertiser:
                return None
            elif attribute == 'publisher' and not stat.publisher:
                return None
            elif attribute == 'country' and not stat.country:
                return None
            elif attribute == 'date' and stat.month: # stops at the month rollup
                return None

            properties = stat.properties()
            attrs = dict([(k,getattr(stat,k)) for k in properties])

            dynamic_properties = stat.dynamic_properties()
            attrs.update(dict([(k,getattr(stat,k)) for k in dynamic_properties]))

            if attribute == 'publisher' and stat.publisher:
                # owner_name prop returns a string that's the owner, i.e. creative.owner_name = 'ad_group'
                stat.publisher.owner = _get_refprop_from_cache(stat.publisher, stat.publisher.owner_name)

                attrs.update(publisher=stat.publisher.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'publisher')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country,
                                      brand_name=new_stat.brand_name,
                                      marketing_name=new_stat.marketing_name,
                                      device_os=new_stat.device_os,
                                      device_os_version=new_stat.device_os_version)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat

            elif attribute == 'advertiser' and stat.advertiser:
                # owner_name prop returns a string that's the owner, i.e. creative.owner_name = 'ad_group'
                stat.advertiser.owner = _get_refprop_from_cache(stat.advertiser, stat.advertiser.owner_name)

                attrs.update(advertiser=stat.advertiser.owner)
                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'advertiser')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country,
                                      brand_name=new_stat.brand_name,
                                      marketing_name=new_stat.marketing_name,
                                      device_os=new_stat.device_os,
                                      device_os_version=new_stat.device_os_version)
                prev_stat += new_stat
                # if owner is None, undo the increment of request count
                # publisher-* is already accounted for
                if not new_stat.advertiser:
                    prev_stat.request_count -= new_stat.request_count
                stats_dict[prev_stat.key().name()] = prev_stat

            elif attribute == 'country' and stat.country:
                country = attrs.get('country')
                attrs.update(country=None)
                new_stat = StatsModel(**attrs)

                # updating the geo properties of the model
                new_stat.update_geo(country,
                                    reporting_models.GEO_REQUEST_COUNT,
                                    attrs['request_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_IMPRESSION_COUNT,
                                    attrs['impression_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_CLICK_COUNT,
                                    attrs['click_count'])
                new_stat.update_geo(country,
                                    reporting_models.GEO_CONVERSION_COUNT,
                                    attrs['conversion_count'])

                # we don't need to do a recursive call because
                # we only have 2 levels, if we want to add something
                # like regions we'd do it here
                # make_above_stat(new_stat,'country')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country,
                                      brand_name=new_stat.brand_name,
                                      marketing_name=new_stat.marketing_name,
                                      device_os=new_stat.device_os,
                                      device_os_version=new_stat.device_os_version)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat

            elif attribute == 'date':
                # NOTE: This is a Pacific TimeZone day
                if stat.date_hour:
                    day = stat.date_hour.date() # makes date object
                    date = datetime.datetime(day.year,day.month,day.day) # makes datetime obj
                    # add date and remove date_hour
                    attrs.update(date=date)
                    del attrs['date_hour']
                if stat.date:
                    date = stat.date
                    month = datetime.datetime(date.year,date.month,1) # makes a date obj for 1st of month
                    attrs.update(month=month)
                    del attrs['date']

                new_stat = StatsModel(**attrs)
                make_above_stat(new_stat,'date')
                prev_stat = _get_stat(pub=new_stat.publisher,
                                      adv=new_stat.advertiser,
                                      date=new_stat.date,
                                      date_hour=new_stat.date_hour,
                                      month=new_stat.month,
                                      country=new_stat.country,
                                      brand_name=new_stat.brand_name,
                                      marketing_name=new_stat.marketing_name,
                                      device_os=new_stat.device_os,
                                      device_os_version=new_stat.device_os_version)
                prev_stat += new_stat
                stats_dict[prev_stat.key().name()] = prev_stat


        # attributes to roll up
        attr_rollup_list = ['publisher', 'advertiser', 'country']

        # roll each attribute up
        for attr in attr_rollup_list:
            stats = stats_dict.values()
            for stat in stats:
                make_above_stat(stat, attr)

        # if not offline, remove all the country level stats
        # because we are storing this data in dynamic properties
        # if not offline:

        stats = stats_dict.values()
        for stat in stats:
            if stat.country:
                del stats_dict[stat.key().name()]

        # time rollups
        if not offline: # do not rollup on date if it's offline, since aws-logging data is already cumulative
            stats = stats_dict.values()
            for stat in stats:
                make_above_stat(stat,'date')

        return stats_dict.values()


    def _place_stats_under_account(self, stats, account=None, offline=False):
        """
        rewrites all the stats objects in order to place them
        under the StatsModel object for the account
        """
        offline = offline or self.offline

        account = account or self.account
        account_stats = StatsModel(account=account, offline=offline)
        properties = StatsModel.properties()
        properties = [k for k in properties]
        new_stats = [account_stats]

        for s in stats:
            # get all the properties of the object
            # StatsModel.prop.get_value_for_datastore(s) for each property of s
            props = {}

            for k in properties:
                props[k] = getattr(s,'_%s'%k) # gets underlying data w/ no derefernce

            for k in s.dynamic_properties():
                props[k] = getattr(s,k)

            props.update(account=account)
            new_stat = StatsModel(parent=account_stats.key(),
                                  key_name=s.key().name(),
                                  **props)
            new_stats.append(new_stat)
        return new_stats

    def _patch_mongodb_stats(self, stat):
        """"Patches a StatModel with MongoDB's latest data for stats in the last week
            Stat is the StatModel for a chosen day
        """
        acct_str = None
        if stat.account:
            if stat.account.use_mongodb_stats and stat.account.use_only_mongo:
                acct_str = str(stat.account.key())
            else:
                return

        date_str = stat.date.date().strftime("%y%m%d")
        url = "http://mongostats.mopub.com/stats?start_date=" + date_str
        url += "&end_date=" + date_str

        pub_str = adv_str = None
        if stat.publisher:
            pub_str = str(stat.publisher.key())
        if stat.advertiser:
            adv_str = str(stat.advertiser.key())
        url += "&acct=%s&pub=%s&adv=%s"%(acct_str or "", pub_str or "", adv_str or "")

        today_dict = {}
        try:
            response = urlopen(url).read()
            today_dict = json.loads(response)
            key = "%s||%s||%s"%(pub_str or "*", adv_str or "*", acct_str or "*")
            today_dict = today_dict['all_stats'][key]['daily_stats'][0]
        except Exception, ex:
            logging.error(ex)

        #Replace StatModel properties with today's stats
        if today_dict:
            stat.revenue = today_dict['revenue']
            stat.impression_count = today_dict['impression_count']
            stat.attemp_count = today_dict['attempt_count']
            stat.request_count = today_dict['request_count']
            stat.click_count = today_dict['click_count']
