import logging
import os
import sys
import urllib

# Are we on EC2 (Note can't use django.settings_module since it's not defined)
# TODO: Add this stuff to my path on EC2
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
    sys.path.append('/home/ubuntu/google_appengine')
    sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
    sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
    sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
    sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
    sys.path.append('/home/ubuntu/google_appengine/lib/webob')
    sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')

    import common.utils.test.setup

from datetime import datetime, timedelta

from account.query_managers import AccountQueryManager
from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkStats, \
     AdNetworkScrapeStats, \
     AdNetworkNetworkStats, \
     AdNetworkAppStats, \
     AdNetworkManagementStats, \
     STAT_NAMES, \
     MANAGEMENT_STAT_NAMES, \
     FAILED_LOGINS
from common.utils.query_managers import CachedQueryManager
from google.appengine.ext import db
from publisher.query_managers import AppQueryManager, \
        ALL_NETWORKS

AD_NETWORK_NAMES = {'admob': 'AdMob',
                    'jumptap': 'JumpTap',
                    'iad': 'iAd',
                    'inmobi': 'InMobi',
                    'mobfox': 'MobFox'}

ADMOB = 'admob'
IAD = 'iad'
INMOBI = 'inmobi'
MOBFOX = 'mobfox'
MOBFOX_PRETTY = 'MobFox'

# TODO: Figure out where to put this. Basically ad_network_reports
# package helper functions.
class AdNetworkReportManager(CachedQueryManager):
    @classmethod
    def get_aggregate_stats_list(cls,
                                 account,
                                 days):
        """
        Take account and list of days, [datetime.date,...].

        Return aggregate stats for all the different ad network mappers for the
        account for the given days.
        """
        # Get all the mappers for this account.
        mappers = list(AdNetworkMapperManager.get_mappers(
            account))

        aggregates_with_dates = [AdNetworkStatsManager. \
                get_stats_for_mapper_and_days(n, days) for n in mappers]
        if aggregates_with_dates:
            aggregates_list, sync_dates = \
                    zip(*aggregates_with_dates)
        else:
            return []
        return zip(mappers, aggregates_list, sync_dates)

    @classmethod
    def get_app_publisher_ids(cls,
                              account,
                              ad_network_name,
                              include_apps=False):
        """Check apps to see if their pub_id for the given ad_network is
        defined

        Return generator of applications with publisher ids for the account on
        the ad_network.
        """
        if ad_network_name == IAD:
            for item in AppQueryManager.get_iad_pub_ids(account=account,
                    include_apps=include_apps):
                yield item

        for app in AppQueryManager.get_apps_with_network_configs(account):
            publisher_id = getattr(app.network_config, '%s_pub_id'
                    % ad_network_name, None)
            if publisher_id:
                if include_apps:
                    # example return (App, NetworkConfig.admob_pub_id)
                    yield (app, publisher_id.strip())
                else:
                    yield publisher_id

    @classmethod
    def create_login_credentials_and_mappers(cls,
                                             account,
                                             ad_network_name,
                                             username='',
                                             password='',
                                             client_key='',
                                             send_email=False):
        """Check login credentials by making a request to tornado on EC2. If
        they're valid create AdNetworkLoginCredentials and AdNetworkAppMapper
        entities and store them in the db.

        Return None if the login credentials are correct otherwise return an
        error message.
        """
        login_credentials = AdNetworkLoginCredentials(account=account,
                                        ad_network_name=ad_network_name,
                                        username=username,
                                        password=password,
                                        client_key=client_key,
                                        email=send_email)
        login_credentials.put()

        apps_with_publisher_ids = cls.get_app_publisher_ids(
                account, ad_network_name, include_apps=True)
        # Create all the different AdNetworkAppMappers for all the
        # applications on the ad network for the user and add them to the db
        db.put([AdNetworkAppMapper(ad_network_name=ad_network_name,
            publisher_id=publisher_id, ad_network_login=login_credentials,
            application=app) for app, publisher_id in
            apps_with_publisher_ids])

        return login_credentials

    @classmethod
    def get_adunit_publisher_ids(cls,
                                 account,
                                 ad_network_name):
        """Get the ad unit publisher ids with the ad network from the generator
        of apps.

        Return a generator of ad unit publisher ids.
        """
        for app in AppQueryManager.get_apps_with_network_configs(account):
            for adunit in app.all_adunits:
                if hasattr(adunit, 'network_config') and getattr(adunit.
                        network_config, '%s_pub_id' % ad_network_name, None):
                    yield getattr(adunit.network_config, '%s_pub_id' %
                            ad_network_name).strip()

    @classmethod
    def get_networks_without_credentials(cls,
                                         account):
        """
        Take account.

        Return list of networks that don't have credentials but would work if
        set up (ie. publisher ids have been entered for at least one app for the
        network).
        """
        creds = AdNetworkLoginCredentials.all().filter('account =', account)
        networks_with_creds = [cred.ad_network_name for cred in creds]
        potential_networks = list(set(AD_NETWORK_NAMES.keys()) -
                set(networks_with_creds))
        for network in potential_networks:
            try:
                cls.get_app_publisher_ids(network).next()
            except StopIteration:
                pass
            else:
                yield network

class AdNetworkLoginManager(CachedQueryManager):
    @classmethod
    def get_login(cls,
                  account,
                  network=''):
        """
        Return AdNetworkLoginCredentials entities for the given account.
        """
        query = AdNetworkLoginCredentials.all().filter('account =', account)
        if network:
            return query.filter('ad_network_name =', network)
        return query

    @classmethod
    def get_all_logins(cls,
                       order_by_account=False):
        """
        Return all AdNetworkLoginCredential entities (ordered by account if
        the order by account flag is set).
        """
        query = AdNetworkLoginCredentials.all()
        if order_by_account:
            return query.order('account')
        return query

    @classmethod
    def get_number_of_accounts(cls):
        """
        Return the total number of accounts using ad network revenue
        reporting.
        """
        accounts = set()
        for login in AdNetworkLoginCredentials.all():
            accounts.add(str(login.account.key()))
        return len(accounts)

class AdNetworkMapperManager(CachedQueryManager):
    @classmethod
    def create(cls,
               network,
               pub_id,
               login,
               app):
        """
        Create an AdNetworkAppMapper for the given input data
        """
        AdNetworkAppMapper(ad_network_name=network,
                           publisher_id=pub_id,
                           ad_network_login=login,
                           application=app).put()

    @classmethod
    def find_app_for_stats(cls,
                           publisher_id,
                           login_credentials):
        """Attempt to link the publisher id with an App stored in MoPub's db.

        Check if the publisher id is in MoPub. If it is create an
        AdNetworkAppMapper and update the AdNetworkLoginCredentials.

        Return the mapper or None.
        """
        # Sanity check
        if publisher_id:
            ad_network_name = login_credentials.ad_network_name
            for app, app_publisher_id in AdNetworkReportManager. \
                    get_app_publisher_ids(login_credentials.account, \
                            ad_network_name, include_apps=True):
                # Is the app in Mopub?
                if publisher_id == app_publisher_id:
                    mapper = AdNetworkAppMapper(ad_network_name=ad_network_name,
                                                publisher_id=publisher_id,
                                                ad_network_login=
                                                        login_credentials,
                                                application=app)
                    mapper.put()
                    return mapper

    @classmethod
    def get_mappers_by_login(cls,
                             login):
        """
        Return a generator of the AdNetworkAppMappers with this login.
        """
        return AdNetworkAppMapper.all().filter('ad_network_login =', login)

    @classmethod
    def get_mappers(cls,
                    account,
                    network_name=''):
        """
        Inner join AdNetworkLoginCredentials with AdNetworkAppMapper.

        Return a generator of the AdNetworkAppMappers with this account.
        """
        for login in AdNetworkLoginManager. \
                get_login(account):
            query = AdNetworkAppMapper.all().filter('ad_network_login =',
                    login)
            if network_name:
                query.filter('ad_network_name =', network_name)
            for mapper in query:
                yield mapper

    @classmethod
    def get_mappers_for_app(cls,
                            login=None,
                            app=None):
        return AdNetworkAppMapper.all().filter('ad_network_login =',
                login).filter('application =', app)

    @classmethod
    def get_mapper(cls,
                   mapper_key=None,
                   publisher_id=None,
                   ad_network_name=None):
        """Keyword arguments: either an ad_network_app_mapper_key or a
        publisher_id and login_credentials.

        Return the corresponding AdNetworkAppMapper.
        """
        if mapper_key:
            return AdNetworkAppMapper.get(mapper_key)
        elif publisher_id and ad_network_name:
            return AdNetworkAppMapper.get_by_publisher_id(publisher_id,
                    ad_network_name)
        return None

class AdNetworkStatsManager(CachedQueryManager):
    @classmethod
    def roll_up_unique_stats(cls,
                             aggregate_stats_list,
                             networks=True):
        """
        Generate the stats roll ups required for the index page.

        Put the apps into an intuitive data structure
        Apps are mapped to their stats, as well as to a list of
        their individual network stats. E.g. :

        Network level roll up: (kwarg networks=True)
        {
            'network1' : {
                'sub_data': [ {app1_stats ... appN_stats],
                'revenue': 0,
                'attempts': 0,
                'impressions': 0,
                'fill_rate': 0,
                'clicks': 0,
                'ctr': 0,
                ...
            }
            ...
        }

        App level roll up (kwarg networks=False):
        {
            'app1' : {
                'sub_data': [ {network1_stats ... networkN_stats],
                'revenue': 0,
                'attempts': 0,
                'impressions': 0,
                'fill_rate': 0,
                'clicks': 0,
                'ctr': 0,
                ...
            }
            ...
        }

        Return the sorted list of lists which contain the rolled up stats for
        the account.
        """
        data_dict = {}
        for mapper, stats, sync_date in aggregate_stats_list:
            app = mapper.application
            if networks:
                attr = AD_NETWORK_NAMES[mapper.ad_network_name]
                name = app.full_name
            else:
                attr = app.full_name
                name = AD_NETWORK_NAMES[mapper.ad_network_name]
            sub_data = {
                'name': name,
                'revenue': stats.revenue,
                'attempts': stats.attempts,
                'impressions': stats.impressions,
                'cpm': stats.cpm,
                'fill_rate': stats.fill_rate,
                'clicks': stats.clicks,
                'ctr': stats.ctr,
                'cpc': stats.cpc,
            }
            if attr not in data_dict:
                data_dict[attr] = {
                    'sub_data_list': [],
                    'revenue': 0.0,
                    'attempts': 0,
                    'fill_rate_impressions': 0,
                    'impressions': 0,
                    'cpm': 0.0,
                    'fill_rate': 0.0,
                    'clicks': 0,
                    'ctr': 0.0,
                    'cpc': 0.0,
                }
            data_dict[attr]['sub_data_list'].append(sub_data)
            data_dict[attr]['revenue'] += sub_data['revenue']
            data_dict[attr]['attempts'] += sub_data['attempts']
            # Only include impressions in fill rate calculations when attempts
            # is != 0 (MobFox doesn't report attempts)
            if sub_data['attempts']:
                data_dict[attr]['fill_rate_impressions'] += \
                        sub_data['impressions']
            data_dict[attr]['impressions'] += sub_data['impressions']
            data_dict[attr]['clicks'] += sub_data['clicks']

        # Calculate stats for highest level roll up for networks or apps.
        for data in data_dict.values():
            # Sort sub_data list by app name or network name.
            data['sub_data_list'] = sorted(data['sub_data_list'], key=lambda \
                    sub_data: sub_data['name'].lower())
            if data['attempts']:
                data['fill_rate'] = data['fill_rate_impressions'] / float(
                        data['attempts'])
            if data['clicks']:
                data['cpc'] = data['revenue'] / data['clicks']
            if data['impressions']:
                data['cpm'] = data['revenue'] / data['impressions'] * 1000
                data['ctr'] = (data['clicks'] /
                        float(data['impressions']))

        # Sort alphabetically
        data_list = sorted(data_dict.items(), key=lambda data_tuple:
                data_tuple[0].lower())

        return data_list

    @classmethod
    def get_stats_for_mapper_and_days(cls,
                                      ad_network_app_mapper,
                                      days):
        """Calculate aggregate stats for an ad network and app
        for the given days.

        Return the aggregate stats.
        """
        stats_list, last_day = AdNetworkScrapeStats.get_by_app_mapper_and_days(
                ad_network_app_mapper.key(), days, include_last_day=True)
        if stats_list:
            return (cls.roll_up_stats(stats_list), last_day)

    @classmethod
    def roll_up_stats(cls,
                      stats_iterable):
        """Roll up (aggregate) stats in the stats iterable.

        Take a stats iterable (query or list).

        Return a stats object.
        """
        aggregate_stats = AdNetworkStats()

        aggregate_stats.fill_rate_impressions = 0
        for stats in stats_iterable:
            cls.combined_stats(aggregate_stats, stats)

            if stats.attempts:
                aggregate_stats.fill_rate_impressions += stats.impressions

        return aggregate_stats

    @classmethod
    def get_stats_list_for_mapper_and_days(cls,
                                           ad_network_app_mapper_key,
                                           days):
        """Filter AdNetworkScrapeStats for a given ad_network_app_mapper. Sort
        chronologically by day, newest first (decending order.)

        Return a list of stats sorted by date.
        """
        stats_list = AdNetworkScrapeStats.get_by_app_mapper_and_days(
                ad_network_app_mapper_key, days)
        return sorted(stats_list, key=lambda stats: stats.date, reverse=True)

    @classmethod
    def copy_stats(cls,
                   stats1,
                   stats2):
        for stat in STAT_NAMES:
            setattr(stats1, stat, getattr(stats2, stat))

    @classmethod
    def combined_stats(cls,
                       stats1,
                       stats2,
                       subtract=False):
        """
        stats1 = stats1 + stats2
        """
        for stat in STAT_NAMES:
            # example: stats1.revenue += stats2.revenue
            if subtract:
                setattr(stats1, stat, getattr(stats1, stat) - getattr(stats2,
                    stat))
            else:
                setattr(stats1, stat, getattr(stats1, stat) + getattr(stats2,
                    stat))


class AdNetworkAggregateManager(CachedQueryManager):
    @classmethod
    def create_stats(cls,
                     account,
                     day,
                     stats_list,
                     network=None,
                     app=None):
        if network:
            stats = AdNetworkNetworkStats(account=account,
                                          ad_network_name=network,
                                          date=day)
        elif app:
            stats = AdNetworkAppStats(account=account,
                                      application=app,
                                      date=day)
        else:
            raise LookupError("Method needs either an app or a network.")
        AdNetworkStatsManager.copy_stats(stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        return stats

    @classmethod
    def update_stats(cls,
                     account,
                     mapper,
                     day,
                     stats,
                     network=None,
                     app=None):
        old_stats = AdNetworkScrapeStats.get_by_app_mapper_and_day(mapper,
                day)
        aggregate_stats = cls.find_or_create(account, day, network, app)
        # Do AdNetworkScrapeStats already exist for the app, network and
        # day?
        if old_stats:
            AdNetworkStatsManager.combined_stats(aggregate_stats, old_stats,
                    subtract=True)
        AdNetworkStatsManager.combined_stats(aggregate_stats, stats)
        aggregate_stats.put()

    @classmethod
    def find_or_create(cls,
                       account,
                       day,
                       network=None,
                       app=None,
                       create=True):
        if network:
            stats = AdNetworkNetworkStats.get_by_network_and_day(account,
                                                                network,
                                                                day)
            if create and not stats:
                return AdNetworkNetworkStats(account=account,
                                             ad_network_name=network,
                                             date=day)
            return stats
        elif app:
            stats = AdNetworkAppStats.get_by_app_and_day(account,
                                                        app,
                                                        day)
            if create and not stats:
                return AdNetworkAppStats(account=account,
                                         application=app,
                                         date=day)
            return stats
        raise LookupError("Method needs either an app or a network.")

    @classmethod
    def get_stats_for_day(cls,
                          account,
                          day):
        """Get rolled up stats for the given date (include all ad networks).

        Return rolled up stats.
        """
        stats_list = []
        for network in AD_NETWORK_NAMES.keys():
            stats = AdNetworkNetworkStats.get_by_network_and_day(
                            account,
                            network,
                            day)
            if stats:
                stats_list.append(stats)
        return(AdNetworkStatsManager.roll_up_stats(stats_list))


class AdNetworkManagementStatsManager(CachedQueryManager):
    def __init__(self,
                 day,
                 assemble=False):
        self.day = day
        self.stats_dict = {}
        for network in AD_NETWORK_NAMES.keys():
            if assemble:
                self.stats_dict[network] = AdNetworkManagementStats. \
                        get_by_day(network, day)
            else:
                self.stats_dict[network] = AdNetworkManagementStats(
                        ad_network_name=network,
                        date=day)

    @property
    def failed_logins(self):
        failed_logins = []
        for stats in self.stats_dict.itervalues():
            failed_logins += stats.failed_logins
        return failed_logins

    def clear_failed_logins(self):
        """
        Clear failed logins from management stats.
        """
        for stats in self.stats_dict.itervalues():
            stats.failed_logins = []
            stats.put()

    def append_failed_login(self,
                            login_credentials):
        if isinstance(login_credentials, unicode):
            login_key = login_credentials
            login_credentials = AdNetworkLoginManager.get(login_key)
        else:
            login_key = str(login_credentials.key())
        self.stats_dict[login_credentials.ad_network_name].failed_logins.append(
                login_key)

    def get_failed_logins(self):
        for stats in self.stats_dict.values():
            if stats.failed_logins:
                for login in stats.failed_logins:
                    yield login

    def increment(self,
                  ad_network_name,
                  field):
        setattr(self.stats_dict[ad_network_name], field,
                getattr(self.stats_dict[ad_network_name], field) + 1)

    def combined(self,
                 stats_manager):
        for network in AD_NETWORK_NAMES.keys():
            for stat in (list(MANAGEMENT_STAT_NAMES) + [FAILED_LOGINS]):
                setattr(self.stats_dict[network], stat, getattr(
                    self.stats_dict[network], stat) + getattr(
                    stats_manager.stats_dict[network], stat))

    def put_stats(self):
        for stats in self.stats_dict.values():
            stats.put()

    @classmethod
    def get_stats(cls,
                  days):
        management_stats = {}
        for ad_network_name in AD_NETWORK_NAMES.keys():
            management_stats[ad_network_name] = AdNetworkManagementStats. \
                    get_by_days(ad_network_name, days)
        return management_stats


def create_fake_data(account=None):
    """
    For debugging purposes. Creates some fake data out of the models
    so we can debug the views and templates.
    """
    import random

    from common.utils import date_magic
    from account.models import NetworkConfig
    from publisher.models import App

    from django.conf import settings

    # Make sure this isn't used on production datastore.
    if settings.DEBUG:
        account.ad_network_email = True
        account.ad_network_recipients = ['magic_monkey@mopub.com']
        account.put()

        last_90_days = date_magic.gen_date_range(90)

        app1 = App(account=account,
                name='Hello Kitty Island Adventures')
        nc1 = NetworkConfig()
        nc1.put()
        app1.network_config = nc1
        app1.put()

        app2 = App(account=account,
                name='WoW')
        nc2 = NetworkConfig()
        nc2.put()
        app2.network_config = nc2
        app2.put()

        networks = AD_NETWORK_NAMES.keys()[1:-2]

        for network in networks:
            login = AdNetworkLoginCredentials(account=account,
                               ad_network_name=network,
                               username='bullshit',
                               password='bullshit',
                               client_key='asdfasf',
                               send_email=False,
                               debug=True)
            login.put()
            pub_id1 = str(random.random()*100)
            AdNetworkAppMapper(ad_network_name=network,
                    publisher_id=pub_id1,
                    ad_network_login=login,
                    application=app1).put()
            setattr(nc1, network + '_pub_id', pub_id1)
            pub_id2 = str(random.random()*100)
            AdNetworkAppMapper(ad_network_name=network,
                    publisher_id=pub_id2,
                    ad_network_login=login,
                    application=app2).put()
            setattr(nc2, network + '_pub_id', pub_id2)

        nc1.put()
        nc2.put()

        AdNetworkLoginCredentials(account=account,
                ad_network_name=AD_NETWORK_NAMES.keys()[0],
                app_pub_ids=['hfehafa','aihef;iawh']).put()
        login = AdNetworkLoginCredentials(account=account,
                ad_network_name=AD_NETWORK_NAMES.keys()[-1])
        login.put()

        for day in last_90_days:
            network_totals = {}
            app_totals = {}
            for mapper in AdNetworkMapperManager.get_mappers(
                    account):
                revenue = random.random() * 10000
                attempts = random.randint(1, 100000)
                impressions = random.randint(1, attempts)
                clicks = random.randint(1, impressions)
                stats = AdNetworkScrapeStats(revenue=revenue,
                                             attempts=attempts,
                                             impressions=impressions,
                                             clicks=clicks,
                                             date=day,
                                             ad_network_app_mapper=mapper)
                stats.put()
                if mapper.ad_network_name not in network_totals:
                    network_totals[mapper.ad_network_name] = \
                            AdNetworkNetworkStats(account=account,
                                                  ad_network_name=mapper.ad_network_name,
                                                  date=day)
                AdNetworkStatsManager.combined_stats(network_totals[mapper.ad_network_name], stats)
                if mapper.application.key_ not in app_totals:
                    app_totals[mapper.application.key_] = \
                            AdNetworkAppStats(account=account,
                                              application=mapper.application,
                                              date=day)
                AdNetworkStatsManager.combined_stats(app_totals[mapper.application.key_], stats)

            for stats in network_totals.itervalues():
                stats.put()

            for stats in app_totals.itervalues():
                stats.put()

            for network in networks:
                stats = AdNetworkManagementStats(ad_network_name=network,
                                        date=day,
                                        found=random.randint(1, 100000),
                                        updated=random.randint(1, 100000),
                                        attempted_logins=random.randint(1, 100))
                for count in range(random.randint(0, 10)):
                    stats.failed_logins.append(str(random.randint(1, 100000)))
                stats.put()

