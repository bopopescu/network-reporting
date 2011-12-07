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
     AdNetworkScrapeStats, \
     AdNetworkManagementStats
from common.utils.query_managers import CachedQueryManager
from google.appengine.ext import db
from publisher.query_managers import AppQueryManager

AD_NETWORK_NAMES = {'admob': 'AdMob',
                    'jumptap': 'JumpTap',
                    'iad': 'iAd',
                    'inmobi': 'InMobi',
                    'mobfox': 'MobFox'}

# Don't touch or everything is fucked
KEY = 'V("9L^4z!*QCF\%"7-/j&W}BZmDd7o.<'

class Stats(object):
    pass

#TODO: Break up query manager into a query manager for each model
class AdNetworkReportQueryManager(CachedQueryManager):

    def __init__(self, account=None):
        self.account = account

    def get_ad_network_mappers(self):
        """
        Inner join AdNetworkLoginCredentials with AdNetworkAppMapper.
        Return a generator of the AdNetworkAppMappers with this account.
        """
        for credential in AdNetworkLoginCredentials.all().filter('account =',
                self.account):
            for mapper in AdNetworkAppMapper.all().filter('ad_network_login =',
                    credential):
                yield mapper

    def get_index_data(self, days):
        """
        Get required data for the index page of ad network reports.

        Generate a list of aggregate stats for the ad networks, apps and
        account fro a date range of the last 7 days. Roll up these aggregate
        stats.

        Return the rolled up aggregates and the aggregate stats list in a
        tuple.
        """
        mappers = list(self.get_ad_network_mappers())

        keys = [s.key() for s in mappers]
        # Get aggregate stats for all the different ad network mappers for the
        # account between the selected date range
        aggregates_with_dates = [self._get_stats_for_mapper_and_days(n, days)
                for n in mappers]
        if aggregates_with_dates:
            aggregates_list, sync_dates = zip(*aggregates_with_dates)
        else:
            aggregates_list = []
            sync_dates = []
        aggregate_stats_list = zip(keys, mappers, aggregates_list, sync_dates)
        aggregates = self.roll_up_stats(aggregates_list)

        # Get the daily stats list.
        daily_stats = [self._get_stats_for_day(date).__dict__ for
                date in days]


        networks = self._roll_up_unique_stats(aggregate_stats_list, True)
        apps = self._roll_up_unique_stats(aggregate_stats_list, False)

        return (aggregates, daily_stats, networks, apps)

    def _roll_up_unique_stats(self, aggregate_stats_list, networks=True):
        """
         Put the apps into an intuitive data structure
         Apps are mapped to their stats, as well as to a list of
         their individual network stats. E.g. :
         {
             'app1' : {
                 'networks': [ {network1_stats ... networkn_stats],
                 'revenue': 0,
                 'attempts': 0,
                 'impressions': 0,
                 'fill_rate': 0,
                 'clicks': 0,
                 'ctr': 0,
             }
             ...
         }
        """
        # Can't get timezone (pytz) on app engine without jumping through some
        # large hoops so we do a rough check.
        yesterday = (datetime.now() - timedelta(days=1)).date()

        data_dict = {}
        for key, mapper, stats, sync_date in aggregate_stats_list:
            if networks:
                attr = AD_NETWORK_NAMES[mapper.ad_network_name]
                name = mapper.application.name
            else:
                attr = mapper.application.name
                name = AD_NETWORK_NAMES[mapper.ad_network_name]
            sub_data = {
                'name': name,
                'key': mapper.key(),
                'revenue': stats.revenue,
                'attempts': stats.attempts,
                'impressions': stats.impressions,
                'fill_rate': stats.fill_rate,
                'clicks': stats.clicks,
                'ctr': stats.ctr,
            }
            if not data_dict.has_key(attr):
                data_dict[attr] = {
                    'sub_data_list': [],
                    'revenue': 0,
                    'attempts': 0,
                    'fill_rate_impressions': 0,
                    'impressions': 0,
                    'fill_rate': 0,
                    'clicks': 0,
                    'ctr': 0,
                    'key': str(key)
                }
                if networks:
                    login_credentials = AdNetworkLoginCredentials.all(). \
                            filter('ad_network_name =', mapper. \
                            ad_network_name).filter('account =',
                                    self.account).get()
                    data_dict[attr]['sync_date'] = sync_date
                    data_dict[attr]['sync_error'] = sync_date - yesterday >= \
                            timedelta(days=1)
                    data_dict[attr]['app_pub_ids'] = ', '.join(
                            login_credentials.app_pub_ids)
            data_dict[attr]['sub_data_list'].append(sub_data)
            data_dict[attr]['revenue'] += sub_data['revenue']
            data_dict[attr]['attempts'] += sub_data['attempts']
            if sub_data['attempts']:
                data_dict[attr]['fill_rate_impressions'] += \
                        sub_data['impressions']
            data_dict[attr]['impressions'] += sub_data['impressions']
            data_dict[attr]['fill_rate'] += sub_data['fill_rate']
            data_dict[attr]['clicks'] += sub_data['clicks']

        for data in data_dict.values():
            # Sort sub_data list.
            data['sub_data_list'] = sorted(data['sub_data_list'], key=lambda \
                    sub_data: sub_data['name'].lower())
            if data['attempts']:
                data['fill_rate'] = data[
                        'fill_rate_impressions'] / float(
                                data['attempts']) * 100
            if data['impressions']:
                data['ctr'] = (data['clicks'] /
                        float(data['impressions'])) * 100
                #network_data['ecpm'] /= float(network_data['impressions'])

        # Add networks that aren't included and set them their data to None.
        if networks:
            for network in AD_NETWORK_NAMES.values():
                if not data_dict.has_key(network):
                    data_dict[network] = None

        # Sort alphabetically
        data_list = sorted(data_dict.items(), key=lambda data_tuple:
                data_tuple[0].lower())

        return data_list

    def _get_stats_for_day(self, day):
        """Get rolled up stats for the given date (include all ad networks).

        Return rolled up stats.
        """
        login_credentials_list = list(AdNetworkLoginCredentials.all().filter(
                'account =', self.account))
        mappers = list(AdNetworkAppMapper.all().filter('application !=', None).
                filter('ad_network_login IN', login_credentials_list))
        return(self.roll_up_stats(AdNetworkScrapeStats.all().filter('date =',
            day).filter('ad_network_app_mapper IN', mappers)))

    def get_chart_stats_for_all_networks(self, days):
        daily_stats = []
        for ad_network_name in AD_NETWORK_NAMES.keys():
            login = AdNetworkLoginCredentials.get_by_ad_network_name(
                    self.account, ad_network_name)
            mappers = list(AdNetworkAppMapper.all().filter('ad_network_login =',
                    login))

            network_stats_dict = {}
            network_stats_dict['name'] = ad_network_name
            network_stats_dict['stats'] = [self._get_stats_for_network_and_day(
                mappers, day) for day in days]
            daily_stats.append(network_stats_dict)
        return daily_stats

    def _get_stats_for_network_and_day(self, mappers, day):
        """Get rolled up stats for the given date and ad network name.

        Return rolled up stats.
        """
        return(self.roll_up_stats(AdNetworkScrapeStats.all().filter('date =',
            day).filter('ad_network_app_mapper IN', mappers)))

    def _get_stats_for_mapper_and_days(self, ad_network_app_mapper,
            days):
        """Calculate aggregate stats for an ad network and app
        for the given days.

        Return the aggregate stats.
        """
        stats_list = AdNetworkScrapeStats.get_by_app_mapper_and_days(
                ad_network_app_mapper.key(), days)
        return (self.roll_up_stats(stats_list), stats_list[-1].date if
                stats_list else None)

    def roll_up_stats(self, stats_iterable):
        """Roll up (aggregate) stats in the stats iterable.

        Take a stats iterable (query or list).

        Return a stats object.
        """
        aggregate_stats = Stats()
        aggregate_stats.revenue = 0
        aggregate_stats.attempts = 0
        aggregate_stats.impressions = 0
        aggregate_stats.clicks = 0
        aggregate_stats.ecpm = 1

        aggregate_stats.fill_rate_impressions = 0
        for stats in stats_iterable:
            old_impressions_total = stats.impressions

            aggregate_stats.revenue += stats.revenue
            aggregate_stats.attempts += stats.attempts
            aggregate_stats.impressions += stats.impressions
            aggregate_stats.clicks += stats.clicks

            if stats.attempts:
                aggregate_stats.fill_rate_impressions += stats.impressions

            if aggregate_stats.impressions:
                aggregate_stats.ecpm += stats.ecpm * stats.impressions

        if aggregate_stats.attempts:
            aggregate_stats.fill_rate = (aggregate_stats.fill_rate_impressions /
                    float(aggregate_stats.attempts)) * 100
        else:
            aggregate_stats.fill_rate = 0
        if aggregate_stats.impressions:
            aggregate_stats.ctr = (aggregate_stats.clicks /
                    float(aggregate_stats.impressions)) * 100
            aggregate_stats.ecpm /= float(aggregate_stats.impressions)
        else:
            aggregate_stats.ctr = 0

        return aggregate_stats

    def get_stats_list_for_mapper_and_days(self, ad_network_app_mapper_key,
            days):
        """Filter AdNetworkScrapeStats for a given ad_network_app_mapper. Sort
        chronologically by day, newest first (decending order.)

        Return a list of stats sorted by date.
        """
        stats_list = AdNetworkScrapeStats.get_by_app_mapper_and_days(
                ad_network_app_mapper_key, days)
        return sorted(stats_list, key=lambda stats: stats.date, reverse=True)

    def get_ad_network_mapper(self,
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
            return AdNetworkAppMapper.get_by_publisher_id(publisher_id,
                    ad_network_name)
        return None

    def _get_apps_with_publisher_ids(self, ad_network_name):
        """Check apps to see if their pub_id for the given ad_network is
        defined

        Return generator of applications with publisher ids for the account on
        the ad_network.
        """
        for app in AppQueryManager.get_apps_with_network_configs(self.account):
            publisher_id = getattr(app.network_config, '%s_pub_id'
                    % ad_network_name, None)
            if publisher_id != None:
                # example return (App, NetworkConfig.admob_pub_id)
                yield (app, publisher_id)

    def create_login_credentials_and_mappers(self,
                                             ad_network_name,
                                             username='',
                                             password='',
                                             client_key='',
                                             send_email=False,
                                             use_crypto=True):
        """Check login credentials by making a request to tornado on EC2. If
        they're valid create AdNetworkLoginCredentials and AdNetworkAppMapper
        entities and store them in the db.

        Return None if the login credentials are correct otherwise return an
        error message.
        """
        if use_crypto:
            from Crypto.Cipher import AES
            from Crypto.Util import randpool
            password_iv = ''
            username_iv = ''
            if password:
                rp = randpool.RandomPool()

                username_iv = rp.get_bytes(16)
                username_aes_cfb = AES.new(KEY, AES.MODE_CFB, username_iv)
                username = username_aes_cfb.encrypt(username)

                password_iv = rp.get_bytes(16)
                password_aes_cfb = AES.new(KEY, AES.MODE_CFB, password_iv)
                password = password_aes_cfb.encrypt(password)

        else:
            username_iv = username
            password_iv = password

        login_credentials = AdNetworkLoginCredentials(account=self.account,
                                        ad_network_name=ad_network_name,
                                        username=username,
                                        username_iv=username_iv,
                                        password=password,
                                        password_iv=password_iv,
                                        client_key=client_key,
                                        email=send_email)
        login_credentials.put()

        apps_with_publisher_ids = self._get_apps_with_publisher_ids(
                ad_network_name)
        # Create all the different AdNetworkAppMappers for all the
        # applications on the ad network for the user and add them to the db
        db.put([AdNetworkAppMapper(ad_network_name=ad_network_name,
            publisher_id=publisher_id, ad_network_login=login_credentials,
            application=app) for app, publisher_id in
            apps_with_publisher_ids])

        return login_credentials



    def find_app_for_stats(self, publisher_id, login_credentials):
        """Attempt to link the publisher id with an App stored in MoPub's db.

        Check if the publisher id is in MoPub. If it is create an
        AdNetworkAppMapper and update the AdNetworkLoginCredentials.

        Return the mapper or None.
        """
        # Sanity check
        if publisher_id:
            ad_network_name = login_credentials.ad_network_name
            for app, app_publisher_id in self._get_apps_with_publisher_ids(
                    ad_network_name):
                # Is the app in Mopub?
                if publisher_id == app_publisher_id:
                    mapper = AdNetworkAppMapper(ad_network_name=ad_network_name,
                                                publisher_id=publisher_id,
                                                ad_network_login=
                                                        login_credentials,
                                                application=app)
                    mapper.put()
                    return mapper

    def get_app_publisher_ids(self, ad_network_name):
        """Check apps to see if their pub_id for the given ad_network is
        defined

        Return generator of publisher ids at the application level for the
        account on the ad_network.
        """
        for app in AppQueryManager.get_apps_with_network_configs(self.account):
            pub_id = getattr(app.network_config, '%s_pub_id' % ad_network_name, None)
            if pub_id != None:
                yield pub_id


    def get_adunit_publisher_ids(self, ad_network_name):
        """Get the ad unit publisher ids with the ad network from the generator
        of apps.

        Return a generator of ad unit publisher ids.
        """
        for app in AppQueryManager.get_apps_with_network_configs(self.account):
            for adunit in app.all_adunits:
                if hasattr(adunit, 'network_config') and getattr(adunit.
                        network_config, '%s_pub_id' % ad_network_name, None):
                    yield getattr(adunit.network_config, '%s_pub_id' %
                            ad_network_name)


    def get_networks_without_credentials(self):
        creds = AdNetworkLoginCredentials.all().filter('account =',
                self.account)
        networks_with_creds = [cred.ad_network_name for cred in creds]
        potential_networks = list(set(AD_NETWORK_NAMES.keys()) -
                set(networks_with_creds))
        for network in potential_networks:
            pub_ids = list(self.get_app_publisher_ids(network))
            if pub_ids:
                yield network

    def get_login_credentials(self):
        """Return AdNetworkLoginCredentials entities for the given account."""
        return AdNetworkLoginCredentials.all().filter('account =', self.account)

def get_all_login_credentials():
    """Return all AdNetworkLoginCredentials entities ordered by account."""
    return AdNetworkLoginCredentials.all().order('account')

def get_management_stats(days):
    return AdNetworkManagementStats.get_by_days(days)

def create_manager(account_key, my_account):
    if account_key:
        return AdNetworkReportQueryManager(AccountQueryManager.get_account_by_key(account_key))
    return AdNetworkReportQueryManager(my_account)

def load_test_data(account=None):
    from account.models import NetworkConfig
    from publisher.models import App, Site
    from google.appengine.ext import db
    from account.models import Account, NetworkConfig

    if account == None:
        account = Account()
        account.put()

    chess_network_config = NetworkConfig(jumptap_pub_id='jumptap_chess_com_test',
                                         iad_pub_id='329218549')
    chess_network_config.put()

    chess_app = App(account=account,
                    name="Chess.com - Play & Learn Chess",
                    network_config=chess_network_config)
    chess_app.put()

    bet_network_config = NetworkConfig(jumptap_pub_id='jumptap_bet_test',
                                       admob_pub_id = 'a14c7d7e56eaff8')
    bet_network_config.put()

    bet_iad_network_config = NetworkConfig(iad_pub_id='418612824')
    bet_iad_network_config.put()

    bet_app = App(account=account,
                  name="BET WAP Site",
                  network_config=bet_network_config)
    bet_app.put()

    adunit_network_config = NetworkConfig(jumptap_pub_id='bet_wap_site_106andpark_top').put()
    Site(app_key=bet_app, network_config=adunit_network_config).put()

    bet_iad_app = App(account=account,
                      name="106 & Park",
                      network_config=bet_iad_network_config)
    bet_iad_app.put()

    officejerk_network_config = NetworkConfig(jumptap_pub_id='office_jerk_test')
    officejerk_network_config.put()

    officejerk_app = App(account=account,
                         name="Office Jerk",
                         network_config=officejerk_network_config)
    officejerk_app.put()


def clear_data():
    db.delete(AdNetworkScrapeStats.all())
    db.delete(AdNetworkAppMapper.all())
    db.delete(AdNetworkLoginCredentials.all())
    db.delete(Accounts.all())

def create_fake_data(account=None):
    """
    For debugging purposes. Creates some fake data out of the models
    so we can debug the views and templates.
    """
    import random
    from common.utils import date_magic

    load_test_data(account)

    a = AdNetworkReportQueryManager(account)

    last_90_days = date_magic.gen_date_range(90)

    for network in AD_NETWORK_NAMES.keys():
        a.create_login_credentials_and_mappers(network,
                                               username='bullshit',
                                               password='bullshit',
                                               client_key='asdfasf',
                                               send_email=False,
                                               use_crypto=False)


    for day in last_90_days:

        for mapper in a.get_ad_network_mappers():
            stats = AdNetworkScrapeStats(revenue = random.random()*100000,
                                         attempts = random.randint(1, 100000),
                                         impressions = random.randint(1, 100000),
                                         fill_rate = random.random()*100,
                                         clicks = random.randint(1, 1000),
                                         ctr = random.random()*100,
                                         ecpm = random.random()*100,
                                         date = day,
                                         ad_network_app_mapper=mapper)
            stats.put()

