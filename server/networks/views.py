import logging

from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.models import LoginStates, \
        MANAGEMENT_STAT_NAMES
from ad_network_reports.query_managers import AD_NETWORK_NAMES, \
        ADMOB, \
        IAD, \
        INMOBI, \
        MOBFOX, \
        MOBFOX_PRETTY, \
        AdNetworkReportManager, \
        AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkManagementStatsManager, \
        create_fake_data

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
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        #create_fake_data(self.account)

        days = gen_days_for_range(self.start_date, self.date_range)

        networks = []
        apps_with_data = {}
        apps_for_network = None
        for network in sorted(AD_NETWORK_NAMES.keys()):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = AD_NETWORK_NAMES[network]
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
                            AD_NETWORK_NAMES.keys())
                apps_list = apps_for_network[network] + \
                        apps_for_network[ALL_NETWORKS]

                network_data['apps_without_pub_ids'] = apps_list

            # Give the template enough information to make the appropriate
            # queries ajax queries to get all the models for each collection
            network_data['mopub_app_stats'] = []
            for mapper in sorted(AdNetworkMapperManager.get_mappers(self.account,
                    network), key=lambda mapper: mapper.application.name.lower()):
                app = mapper.application
                apps_with_data[(app.name, app.app_type)] = mapper.application


                # get adgroups targeting this app
                adgroups = AdGroupQueryManager.get_adgroups(app=app)

                app_stats = StatsModel()
                for ag in adgroups:
                    logging.warning("Checking Adgroup")
                    logging.warning(getattr(ag, 'network_type', ''))
                    logging.warning(network)
                    if getattr(ag, 'network_type', '') == network or \
                            getattr(ag, 'network_type', '') == AD_NETWORK_NAMES[network]:
                        stats_manager = StatsModelQueryManager(self.account,offline=self.offline)
                        all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                                        advertiser=ag,
                                                                        days=days)
                        logging.warning(all_stats)
                        stats = reduce(lambda x, y: x+y, all_stats, StatsModel())
                        logging.warning(stats)
                        app_stats += stats
                network_data['mopub_app_stats'].append((app,
                    mapper.publisher_id, app_stats))

            network_data['mopub_stats'] = reduce(lambda x, y: x+y,
                    [app_stats for app, pub_id, app_stats in
                        network_data['mopub_app_stats']], StatsModel())
            network_data['mopub_app_stats'] = sorted(
                    network_data['mopub_app_stats'], key=lambda app_data:
                    app_data[0].identifier)


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
            networks.append(network_data)

        apps = [app for app in sorted(apps_with_data.itervalues(), key=lambda
            app: app.identifier)]


#        mopub_app_stats = {}
#        mopub_network_stats = {}
#        # For all apps for this account get the network stats
#        for app in get_all_apps()
#                for ag in app.adgroups:
#                    if ag.campaign.campaign_type == 'network':
#                        stats_manager = StatsModelQueryManager(self.account,offline=self.offline)
#                        all_stats = stats_manager.get_stats_for_days(publisher=app,
#                                                                        advertiser=ag,
#                                                                        days=days)
#                        stats = reduce(lambda x, y: x+y, all_stats, StatsModel())
#
#                        if ag.network_type in mopub_network_stats:
#                            network_data = mopub_network_stats[ag.network_type]
#                            network_data['stats'] += stats
#                            app_data = network_data['app_stats']
#                            if app.key() in app_data:
#                                app_data[app.key()] += stats
#                            else:
#                                app_data[app.key()] = stats
#                        else:
#                            mopub_network_stats[ag.network_type] = \
#                                    {'stats': stats,
#                                     'app_stats': {}}
#
#                        if app.key() in mopub_app_stats:
#                            app_data = mopub_app_stats[app.key()]
#                            app_data['stats'] += stats
#                            network_data = network_data['network_stats']
#                            if ag.network_type in network_data:
#                                network_data[ag.network_type] += stats
#                            else:
#                                network_data[ag.network_type] = stats
#                        else:
#                            mopub_app_stats[app.key()] = \
#                                    {'stats': stats,
#                                     'network_stats': {}}


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
                  'show_graph' : (apps and True) or False,
                  # Account key needed for form submission to EC2.
                  'settings': settings,
                  'account_key' : str(self.account.key()),
                  'networks': networks,
                  'apps': apps,
                  'LoginStates': LoginStates,
                  'ADMOB': ADMOB,
                  'IAD': IAD,
                  'INMOBI': INMOBI,
                  'MOBFOX': MOBFOX,
#                  'mopub_app_stats': mopub_app_stats,
#                  'mopub_network_stats': mopub_app_stats,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

