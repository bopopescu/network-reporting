import logging

from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.models import AdNetworkAppMapper, \
        LoginStates, \
        MANAGEMENT_STAT_NAMES
from ad_network_reports.query_managers import ADMOB, \
        IAD, \
        INMOBI, \
        MOBFOX, \
        MOBFOX_PRETTY, \
        AdNetworkReportManager, \
        AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkManagementStatsManager
from ad_network_reports.query_managers import AD_NETWORK_NAMES as \
        REPORTING_NETWORKS

from common.utils.date_magic import gen_days_for_range
from common.utils.decorators import staff_login_required
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter

from publisher.query_managers import AppQueryManager, \
        ALL_NETWORKS

from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.shortcuts import redirect

from google.appengine.ext import db

# Imports for getting mongo stats
from advertiser.query_managers import AdGroupQueryManager
from advertiser.models import NetworkStates
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

OTHER_NETWORKS = {'millennial': 'Millennial',
                  'ejam': 'eJam',
                  'chartboost': 'ChartBoost',
                  'appnexus': 'AppNexus',
                  'brightroll': 'BrightRoll',
                  'greystripe': 'Greystripe'}

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        def create_and_set(networks, network, app):
            if network not in networks:
                networks[network] = {}
            if 'mopub_app_stats' not in networks[network]:
                networks[network]['mopub_app_stats'] = {}
            if 'mopub_stats' not in networks[network]:
                networks[network]['mopub_stats'] = StatsModel()
            if app.key() not in networks[network]['mopub_app_stats']:
                networks[network]['mopub_app_stats'][app.key()] = \
                        {'stats': StatsModel(),
                         'app': app,
                         'adunits': []}

        days = gen_days_for_range(self.start_date, self.date_range)

        reporting_networks = {}
        other_networks = {}

        # Iterate through all networks that allow reporting
        apps_for_network = None
        for network in REPORTING_NETWORKS.keys():
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = REPORTING_NETWORKS[network]
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()
            if login:
                network_data['pub_ids_without_data'] = login.app_pub_ids
                network_data['state'] = login.state
            else:
                network_data['state'] = LoginStates.NOT_SETUP

            # Get list of apps that need pub ids if they want to be included
            if not login or not login.app_pub_ids:
                if not apps_for_network:
                    apps_for_network = AppQueryManager.get_apps_without_pub_ids(
                            self.account,
                            REPORTING_NETWORKS.keys())
                apps_list = apps_for_network[network] + \
                        apps_for_network[ALL_NETWORKS]

                network_data['apps_without_pub_ids'] = apps_list

            # Create a form for each network and autopopulate fields.
            try:
                login = AdNetworkLoginCredentials. \
                        get_by_ad_network_name(self.account, network)
                form = LoginInfoForm(instance=login, prefix=network)
                # Encryption doesn't work on app engine...
                #form.initial['password'] = login.decoded_password
                #form.initial['username'] = login.decoded_password
            except Exception, error:
                form = LoginInfoForm(prefix=network)
            network_data['form'] = form
            reporting_networks[network] = network_data

        # Iterate through all networks that don't have reporting
        for network in sorted(OTHER_NETWORKS.keys()):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = OTHER_NETWORKS[network]

            other_networks[network] = network_data

        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate the stats for reporting_networks
        # and other_networks
        for app in AppQueryManager.get_apps(self.account):
            network_config = app.network_config
            # Get data from the ad networks
            for network in REPORTING_NETWORKS.keys():
                pub_id = getattr(network_config, network + '_pub_id', '')
                logging.info('pub_id')
                logging.info(pub_id)
                if pub_id:
                    mapper = AdNetworkAppMapper.get_by_publisher_id(pub_id,
                            network)
                    logging.info('mapper')
                    logging.info(mapper)
                    if mapper:
                        create_and_set(reporting_networks, network, app)
                        reporting_networks[network] \
                                ['mopub_app_stats'][app.key()]['pub_id'] = \
                                pub_id

            # Get data collected by MoPub
            adunits = []
            for adgroup in AdGroupQueryManager.get_adgroups(app=app):
                if adgroup.network_state == NetworkStates.NETWORK_ADGROUP:
                    all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                                 advertiser=adgroup,
                                                                 days=days)
                    stats = reduce(lambda x, y: x+y, all_stats, StatsModel())
                    adunit = db.get(adgroup.site_keys[0])
                    adunit.stats = stats
                    if adgroup.network_type in REPORTING_NETWORKS.keys():
                        create_and_set(reporting_networks, adgroup.network_type, app)
                        reporting_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        reporting_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        reporting_networks[adgroup.network_type]['mopub_stats'] += stats
                    elif adgroup.network_type in OTHER_NETWORKS.keys():
                        create_and_set(other_networks, adgroup.network_type, app)
                        other_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        other_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        other_networks[adgroup.network_type]['mopub_stats'] += stats

        reporting_networks = sorted(reporting_networks.values(), key=lambda
                network_data: network_data['name'])
        for network_data in reporting_networks:
            if 'mopub_app_stats' in network_data:
                network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                        app_data: app_data['app'].identifier)
        logging.info('reporting_networks')
        logging.info(reporting_networks)

        # TODO: Generalize
        other_networks = sorted(other_networks.values(), key=lambda
                network_data: network_data['name'])
        for network_data in other_networks:
            if 'mopub_app_stats' in network_data:
                network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                        app_data: app_data['app'].identifier)
        logging.info('other_networks')
        logging.info(other_networks)

        # self.account can't access ad_network_* data
        account = AccountQueryManager.get_account_by_key(self.account.key())
        # Settings
        settings = {}
        settings['email'] = account.ad_network_email
        if account.ad_network_recipients:
            settings['recipients'] = ', '.join(account.ad_network_recipients)
        else:
            settings['recipients'] = ', '.join(account.emails)

        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/ad_network_reports_index.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'show_graph' : True,
                  # Account key needed for form submission to EC2.
                  'settings': settings,
                  'account_key' : str(self.account.key()),
                  'reporting_networks': reporting_networks,
                  'other_networks': other_networks,
                  'LoginStates': LoginStates,
                  'ADMOB': ADMOB,
                  'IAD': IAD,
                  'INMOBI': INMOBI,
                  'MOBFOX': MOBFOX,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

