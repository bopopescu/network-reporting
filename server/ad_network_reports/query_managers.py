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
     STAT_NAMES
from common.utils.query_managers import CachedQueryManager
from google.appengine.ext import db
from publisher.query_managers import AppQueryManager, \
        ALL_NETWORKS

AD_NETWORK_NAMES = {'admob': 'AdMob',
                    'jumptap': 'JumpTap',
                    'iad': 'iAd',
                    'inmobi': 'InMobi',
                    'mobfox': 'MobFox'}

MOBFOX_PRETTY = 'MobFox'
MOBFOX = 'mobfox'
IAD_PRETTY = 'iAd'
IAD = 'iad'

#TODO: Figure out where to put this. Basically ad_network_reports
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
                  network_name=''):
        """
        Return AdNetworkLoginCredentials entities for the given account.
        """
        query = AdNetworkLoginCredentials.all().filter('account =', account)
        if network_name:
            return query.filter('ad_network_name =', network_name)
        return query

    @classmethod
    def get_all_login_credentials(cls):
        """
        Return all AdNetworkLoginCredentials entities ordered by account.
        """
        return AdNetworkLoginCredentials.all().order('account')

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
    def get_ad_network_mapper(cls,
                              ad_network_app_mapper_key=None,
                              publisher_id=None,
                              ad_network_name=None):
        """Keyword arguments: either an ad_network_app_mapper_key or a
        publisher_id and login_credentials.

        Return the corresponding AdNetworkAppMapper.
        """
        if ad_network_app_mapper_key:
            return AdNetworkAppMapper.get(ad_network_app_mapper_key)
        elif publisher_id and ad_network_name:
            return AdNetworkAppMapper.get_by_publisher_id(publisher_id, ad_network_name)
        return None

class AdNetworkStatsManager(CachedQueryManager):
    @classmethod
    def roll_up_unique_stats(cls,
                             account,
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

        Make these generated data dict's lists then insert missing networks (if
        kwarg networks=True) and sort them alphabetically.

        Return the sorted list of lists which contain the rolled up stats for
        the account.
        """
        # Can't get timezone (pytz) on app engine without jumping through some
        # large hoops so we do a rough check.
        yesterday = (datetime.now() - timedelta(days=1)).date()

        data_dict = {}
        for mapper, stats, sync_date in aggregate_stats_list:
            application = mapper.application
            if networks:
                attr = AD_NETWORK_NAMES[mapper.ad_network_name]
                name = '%s (%s)' % (application.name, application. \
                        app_type_text())
                key = str(mapper.key())
            else:
                attr = (application.name, application.app_type_text())
                name = AD_NETWORK_NAMES[mapper.ad_network_name]
                key = application.key()
            sub_data = {
                'name': name,
                'key': mapper.key(),
                'revenue': stats.revenue,
                'attempts': stats.attempts,
                'impressions': stats.impressions,
                'cpm': stats.cpm,
                'fill_rate': stats.fill_rate,
                'clicks': stats.clicks,
                'ctr': stats.ctr,
                'cpc': stats.cpc,
            }
            if networks:
                sub_data['id'] = mapper.publisher_id
            if not data_dict.has_key(attr):
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
                    'key': key,
                }
                if networks:
                    data_dict[attr]['state'] = 2
                    data_dict[attr]['sync_date'] = sync_date
                    data_dict[attr]['sync_error'] = not sync_date or yesterday \
                            - sync_date >= timedelta(days=2)
                    login_credentials = AdNetworkLoginManager. \
                            get_login(account).filter(
                                    'ad_network_name =',
                                    mapper.ad_network_name).get()
                    data_dict[attr]['app_pub_ids'] = ', '.join(
                            login_credentials.app_pub_ids)
                else:
                    data_dict[attr]['icon_url'] = application.icon_url
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

        # Add all ad networks. If there are apps without pub ids set for the
        # network this list in the data_dict for the network.
        if networks:
            apps_without_pub_ids = AppQueryManager.get_apps_without_pub_ids(
                    account, AD_NETWORK_NAMES.keys())

            for network in AD_NETWORK_NAMES.keys():
                if AD_NETWORK_NAMES[network] not in data_dict:
                    login_credentials =  AdNetworkLoginManager. \
                            get_login(account).filter(
                                    'ad_network_name =', network).get()
                    apps_without_pub_ids_for_network = apps_without_pub_ids[
                            network] + apps_without_pub_ids[ALL_NETWORKS]

                    # iAd displays a link to each app in the front-end message
                    # so in this case the front-end requires more information
                    # than simply the app's name.
                    if network == IAD:
                        apps_for_network = apps_without_pub_ids_for_network
                    else:
                        apps_for_network = ', '.join([app.name for app in
                            apps_without_pub_ids_for_network])

                    if login_credentials:
                        app_pub_ids = ', '.join(login_credentials.app_pub_ids)
                        if app_pub_ids:
                            data_dict[AD_NETWORK_NAMES[network]] = {'state': 1,
                                    'app_pub_ids': app_pub_ids}
                        else:
                            data_dict[AD_NETWORK_NAMES[network]] = {'state': 0,
                                    'apps_without_pub_ids': apps_for_network}
                    else:
                        data_dict[AD_NETWORK_NAMES[network]] = {'state': 0,
                                'apps_without_pub_ids': apps_for_network}

            # Sort alphabetically
            data_list = sorted(data_dict.items(), key=lambda data_tuple:
                    data_tuple[0].lower())
        else:
            # Sort alphabetically
            data_list = sorted(data_dict.items(), key=lambda data_tuple:
                    data_tuple[0][0].lower() + data_tuple[0][1].lower())

        return data_list

    @classmethod
    def get_stats_for_day(cls,
                          account,
                          day):
        """Get rolled up stats for the given date (include all ad networks).

        Return rolled up stats.
        """
        stats_list = []
        for login_credentials in AdNetworkLoginCredentials.all().filter(
                'account =', account):
            for mapper in AdNetworkAppMapper.all().filter('application !=',
                    None).filter('ad_network_login =',
                            login_credentials):
                for stats in AdNetworkScrapeStats.all().filter('date =',
                        day).filter('ad_network_app_mapper =', mapper):
                    stats_list.append(stats)
        return(AdNetworkStatsManager.roll_up_stats(stats_list))

    #TODO: Delete unused method
    @classmethod
    def _get_stats_for_network_and_day(cls,
                                       mappers,
                                       day):
        """Get rolled up stats for the given date and ad network name.

        Return rolled up stats.
        """
        stats_list = []
        for mapper in mappers:
            for stats in AdNetworkScrapeStats.all().filter('date =',
                    day).filter('ad_network_app_mapper =', mapper):
                stats_list.append(stats)
        return(cls.roll_up_stats(stats_list))

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
    def put_stats(cls,
                  account,
                  day,
                  stats_list,
                  network=None,
                  app=None):
        stats = cls.find_or_create(account, day, network, app)
        AdNetworkStatsManager.combined_stats(stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        stats.put()

    @classmethod
    def update_stats(cls,
                     account,
                     mapper,
                     day,
                     stats,
                     network=None,
                     app=None):
        old_stats = AdNetworkScrapeStats.get_by_app_mapper_and_day(mapper, day)
        aggregate_stats = cls.find_or_create(account, day, network, app)
        # Do AdNetworkScrapeStats already exist for the app, network and day?
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
                    AdNetworkAppStats(account=account,
                                      application=app,
                                      date=day)
            return stats
        raise LookupError("Method needs either an app or a network.")


class AdNetworkManagementStatsManager(CachedQueryManager):
    def __init__(self,
                 day):
        self.stats_dict = {}
        for network in AD_NETWORK_NAMES.keys():
            self.stats_dict[network] = AdNetworkManagementStats(
                    ad_network_name=network,
                    date=day)

    def append_failed_login(self,
                            login_credentials):
        self.stats_dict[login_credentials.ad_network_name].failed_logins.append(
                str(login_credentials.key()))

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
    from publisher.models import App

    from django.conf import settings

    # Make sure this isn't used on production datastore.
    if settings.DEBUG:
        last_90_days = date_magic.gen_date_range(90)

        app = App(account=account,
                name='My little pony island adventures')
        app.put()

        for network in AD_NETWORK_NAMES.keys()[1:-2]:
            login = AdNetworkLoginCredentials(account=account,
                               ad_network_name=network,
                               username='bullshit',
                               password='bullshit',
                               client_key='asdfasf',
                               send_email=False)
            login.put()
            AdNetworkAppMapper(ad_network_name=network,
                    publisher_id=str(random.random()*100),
                    ad_network_login=login,
                    application=app).put()
        AdNetworkLoginCredentials(account=account,
                ad_network_name=AD_NETWORK_NAMES.keys()[0],
                app_pub_ids=['hfehafa','aihef;iawh']).put()
        login = AdNetworkLoginCredentials(account=account,
                ad_network_name=AD_NETWORK_NAMES.keys()[-1])
        login.put()

        for day in last_90_days:
            for mapper in AdNetworkMapperManager.get_mappers(
                    account):
                attempts = random.randint(1, 100000)
                impressions = random.randint(1, attempts)
                clicks = random.randint(1, impressions)
                stats = AdNetworkScrapeStats(revenue=random.random()*10000,
                                             attempts=attempts,
                                             impressions=impressions,
                                             clicks=clicks,
                                             date=day,
                                             ad_network_app_mapper=mapper)
                stats.put()

            for network in AD_NETWORK_NAMES.keys():
                stats = AdNetworkManagementStats(ad_network_name=network,
                                        date=day,
                                        found=random.randint(1, 100000),
                                        updated=random.randint(1, 100000),
                                        mapped=random.randint(1, 100000),
                                        attempted_logins=random.randint(1, 100))

                if network == login.ad_network_name:
                    stats.failed_logins = [str(login.key())]
                stats.put()

