import logging
import urllib

from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
from google.appengine.ext import db

from account.models import NetworkConfig
from common.utils import date_magic
from common.utils.query_managers import CachedQueryManager
from ad_network_reports.models import AdNetworkLoginInfo, AdNetworkAppMapper, \
        AdNetworkScrapeStats
from publisher.models import App

class Stats(object):
    pass

class AdNetworkReportQueryManager(CachedQueryManager):
    TEST_LOGIN_CREDENTIALS_URL = ("http://checklogincredentials.mopub.com:8888")

    def __init__(self, account=None):
        self.account = account

    def get_ad_network_mappers(self):
        """Inner join AdNetworkLoginInfo with AdNetworkAppMapper.

        Return a generator of the AdNetworkAppMappers with this account.
        """
        for credential in AdNetworkLoginInfo.all().filter('account =',
                self.account):
            for mapper in AdNetworkAppMapper.all().filter('ad_network_login =',
                    credential):
                yield mapper

    def get_ad_network_aggregates(self, ad_network_app_mapper,
            start_date, end_date):
        """Calculate aggregate stats for an ad network and app
        between the given start date and end date.

        Return the aggregate stats.
        """
        query = AdNetworkScrapeStats.all()
        query.filter('ad_network_app_mapper =', ad_network_app_mapper)
        query.filter('date IN', date_magic.gen_days(start_date, end_date))

        aggregate_stats = Stats()
        aggregate_stats.revenue = 0
        aggregate_stats.attempts = 0
        aggregate_stats.impressions = 0
        aggregate_stats.clicks = 0
        aggregate_stats.ecpm = 1
        for stats in query:
            old_impressions_total = stats.impressions

            aggregate_stats.revenue += stats.revenue
            aggregate_stats.attempts += stats.attempts
            aggregate_stats.impressions += stats.impressions
            aggregate_stats.clicks += stats.clicks

            if aggregate_stats.impressions != 0:
                aggregate_stats.ecpm = ((aggregate_stats.ecpm *
                    old_impressions_total + stats.ecpm * stats.impressions) /
                    float(aggregate_stats.impressions))
            else:
                aggregate_stats.ecpm = float('NaN')

        if aggregate_stats.attempts != 0:
            aggregate_stats.fill_rate = (aggregate_stats.impressions /
                    float(aggregate_stats.attempts))
        else:
            aggregate_stats.fill_rate = float('NaN')
        if aggregate_stats.impressions != 0:
            aggregate_stats.ctr = (aggregate_stats.clicks /
                    float(aggregate_stats.impressions))
        else:
            aggregate_stats.ctr = float('NaN')

        return aggregate_stats

    def get_ad_network_app_stats(self, ad_network_app_mapper):
        """Filter AdNetworkStats for a given ad_network_app_mapper. Sort
        chronologically by day, newest first (decending order.)

        Return the query (a generator.)
        """
        query = AdNetworkScrapeStats.all()
        query.filter('ad_network_app_mapper =', ad_network_app_mapper)
        query.order('-date')
        return query

    def get_ad_network_app_mapper(self, ad_network_app_mapper_key = None,
            publisher_id = None, login_info = None):
        """Keyword arguments: either an ad_network_app_mapper_key or a
        publisher_id and login_info.

        Return the corresponding AdNetworkAppMapper.
        """
        if ad_network_app_mapper_key:
            return db.get(ad_network_app_mapper_key)
        elif publisher_id and login_info:
            query = AdNetworkAppMapper.all()
            query.filter('publisher_id =', publisher_id)
            query.filter('ad_network_login =', login_info)
            return query.get()
        return None

    def get_apps_with_publisher_ids(self, ad_network_name):
        """Inner join of NetworkConfig and App.

        Return generator of applications with publisher ids for the account on
        the ad_network.
        """
        for config in NetworkConfig.all().filter('%s_pub_id !=' %
                ad_network_name, None):
            for app in (App.all().filter('account =',
                self.account).filter('network_config =', config)):
                # example return (App, NetworkConfig.admob_pub_id)
                yield (app, getattr(config, '%s_pub_id' % ad_network_name))

    def create_login_info_and_mappers(self, ad_network_name, username, password,
            client_key, send_email):
        """Check login credentials by making a request to tornado on EC2. If
        they're valid create AdNetworkLoginInfo and AdNetworkAppMapper entities
        and store them in the db.

        Return None if the login credentials are correct otherwise return an
        error message.
        """
        logging.warning('Creating shit')
        apps_with_publisher_ids = list(self.get_apps_with_publisher_ids(
            ad_network_name))
        publisher_ids = [publisher_id for app, publisher_id in
                apps_with_publisher_ids]

        adunits = [adunit.name for app, publisher_id in apps_with_publisher_ids
                for adunit in app.all_adunits]

        login_info = AdNetworkLoginInfo(account = self.account,
                                        ad_network_name = ad_network_name,
                                        username = username,
                                        password = password,
                                        client_key = client_key,
                                        publisher_ids = publisher_ids,
                                        adunits = adunits)
        
        
        logging.warning('attempting to connect to tornado')
        result = None
        try:
            result = urlfetch.fetch(url = self.TEST_LOGIN_CREDENTIALS_URL,
                    payload = urllib.urlencode(login_info.__dict__), method =
                    urlfetch.POST, deadline = 10)
        except DownloadError:
            logging.error("Server timeout occured when attempting to check ad "
                          "network login info")
        if result and result.status_code == 200:
            login_info.put()

            # Create all the different AdNetworkAppMappers for all the
            # applications on the ad network for the user and add them to the db
            db.put([AdNetworkAppMapper(ad_network_name = ad_network_name,
                publisher_id = publisher_id, ad_network_login = login_info,
                application = app, send_email = send_email) for app,
                publisher_id in apps_with_publisher_ids])
        else:
            return "Incorrect login information"

def get_login_credentials():
    """Return all AdNetworkLoginInfo entities ordered by account."""
    return AdNetworkLoginInfo.all().order('account')

def get_pub_id(pub_id, login_info):
    return pub_id

def get_pub_id_from_name(app_name, login_info):
    query = App.all()
    query.filter('name =', app_name)
    query.filter('account =', login_info.account)
    app = query.get()

    if app and login_info.ad_network_name == 'jumptap':
        return app.network_config.jumptap_pub_id
    return None
