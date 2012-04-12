import logging

from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginCredentialsForm
from ad_network_reports.models import LoginStates, \
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
        AdNetworkManagementStatsManager, \
        create_fake_data

from common.utils.decorators import staff_login_required
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from common.constants import REPORTING_NETWORKS

from publisher.query_managers import AppQueryManager, \
        ALL_NETWORKS

from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.shortcuts import redirect

from google.appengine.ext import db

DATE = 'date'
REVENUE = 'revenue'
ATTEMPTS = 'attempts'
IMPRESSIONS = 'impressions'
CPM = 'cpm'
FILL_RATE = 'fill_rate'
CLICKS = 'clicks'
CPC = 'cpc'
CTR = 'ctr'
SORT_BY_NETWORK = 'network'
FAILED = 'failed'
LOGINS = 'logins'
ACCOUNTS = 'accounts'

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        #create_fake_data(self.account)

        # If a custom daterange is not selected shift days back by one
        if len(self.request.GET) < 2:
            days = [day - timedelta(days=1) for day in self.days]
        else:
            days = self.days

        networks = []
        apps_with_data = {}
        apps_for_network = None
        for network in sorted(REPORTING_NETWORKS.keys()):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = AD_NETWORK_NAMES[network]
            login = AdNetworkLoginManager.get_logins(self.account,
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

            # Give the template enough information to make the appropriate
            # queries ajax queries to get all the models for each collection
            network_data['pub_ids'] = []
            for mapper in sorted(AdNetworkMapperManager.get_mappers(self.account,
                    network), key=lambda mapper: mapper.application.name.lower()):
                network_data['pub_ids'].append(mapper.publisher_id)
                app = mapper.application
                apps_with_data[(app.name, app.app_type)] = mapper.application

            # Create a form for each network and autopopulate fields.
            try:
                login = AdNetworkLoginCredentials. \
                        get_by_ad_network_name(self.account, network)
                form = LoginCredentialsForm(instance=login, prefix=network)
                # Encryption doesn't work on app engine...
                #form.initial['password'] = login.decoded_password
                #form.initial['username'] = login.decoded_password
            except Exception, error:
                form = LoginCredentialsForm(prefix=network)
            network_data['form'] = form
            networks.append(network_data)

        apps = [app for app in sorted(apps_with_data.itervalues(), key=lambda
            app: app.identifier)]

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
              'ad_network_reports/ad_network_reports_index.html',
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
              })

@login_required
def ad_network_reports_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)

class AdNetworkSettingsHandler(RequestHandler):
    def post(self):
        email = self.request.POST.get('email', False) and True
        recipients = [recipient.strip() for recipient in self.request.POST.get(
            'recipients').split(',')]

        # Don't send a put to the db unless something changed
        if email != self.account.ad_network_email or recipients != \
                self.account.ad_network_recipients:
            self.account.ad_network_email = email
            self.account.ad_network_recipients = recipients
            self.account.put()

        return TextResponse('done')

@login_required
def ad_network_settings(request, *args, **kwargs):
    return AdNetworkSettingsHandler()(request, *args, **kwargs)

class ExportFileHandler(RequestHandler):
    def get(self,
            f_type,
            sort_type):
        """
        Take a file type (xls or csv).

        Return a file with the aggregate stats data sorted by network or app.
        """
        # If a custom daterange is not selected shift days back by one
        if len(self.request.GET) < 2:
            days = [day - timedelta(days=1) for day in self.days]
        else:
            days = self.days

        aggregate_stats_list = AdNetworkReportManager. \
                get_aggregate_stats_list(self.account, days)

        if sort_type == SORT_BY_NETWORK:
            all_stats = AdNetworkStatsManager.roll_up_unique_stats( \
                    aggregate_stats_list, True)
        else:
            all_stats = AdNetworkStatsManager.roll_up_unique_stats( \
                    aggregate_stats_list, False)

        stat_names = {}
        stat_names[MOBFOX_PRETTY] = (REVENUE, IMPRESSIONS, CPM, CLICKS,
                CPC, CTR)
        stat_names[sswriter.DEFAULT] = (REVENUE, ATTEMPTS, IMPRESSIONS,
                CPM, FILL_RATE, CLICKS, CPC, CTR)
        return sswriter.write_ad_network_stats(f_type, stat_names, all_stats,
                days=days, networks=(sort_type == 'network'))

@login_required
def export_file(request, *args, **kwargs):
    return ExportFileHandler()( request, *args, **kwargs )

class AppDetailHandler(RequestHandler):
    def get(self,
            mapper_key):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        # If a custom daterange is not selected shift days back by one
        if len(self.request.GET) < 2:
            days = [day - timedelta(days=1) for day in self.days]
        else:
            days = self.days

        ad_network_app_mapper = AdNetworkMapperManager.get(mapper_key)
        stats_list = AdNetworkStatsManager.get_stats_for_days(
                mapper_key, days)
        daily_stats = []
        for stats in stats_list:
            stats_dict = stats.__dict__['_entity']
            if not stats_dict:
                stats_dict = stats.__dict__
                stats_dict = dict([(key.replace('_', '', 1), val) for key, val
                    in stats_dict.iteritems()])
            else:
                del(stats_dict['ad_network_app_mapper'])
            del(stats_dict['date'])
            daily_stats.append(stats_dict)
        daily_stats.reverse()
        aggregates = AdNetworkStatsManager.roll_up_stats(stats_list)
        app = ad_network_app_mapper.application
        return render_to_response(self.request,
                  'ad_network_reports/ad_network_base.html',
                  {
                      'start_date' : days[0],
                      'end_date' : days[-1],
                      'date_range' : self.date_range,
                      'ad_network_name' :
                        REPORTING_NETWORKS[ad_network_app_mapper.ad_network_name],
                      'app_name' : '%s (%s)' % (app.name, app.app_type_text()),
                      'aggregates' : aggregates,
                      'daily_stats' :
                        simplejson.dumps(daily_stats),
                      'stats_list' : stats_list,
                      'show_graph': True,
                      'mapper_key': mapper_key,
                      'MOBFOX': MOBFOX_PRETTY
                  })

@login_required
def app_detail(request, *args, **kwargs):
    return AppDetailHandler()(request, *args, **kwargs)

class ExportAppDetailFileHandler(RequestHandler):
    def get(self,
            f_type,
            mapper_key):
        """
        Export data in for the app on the network (what's in the table) to xls
        or csv.
        """
        # If a custom daterange is not selected shift days back by one
        if len(self.request.GET) < 2:
            days = [day - timedelta(days=1) for day in self.days]
        else:
            days = self.days

        stats_list = AdNetworkStatsManager.get_stats_for_days(
                mapper_key, days)
        mapper = db.get(mapper_key)
        if mapper.ad_network_name == MOBFOX:
            stat_names = (DATE, REVENUE, IMPRESSIONS, CPM,
                    CLICKS, CPC, CTR)
        else:
            stat_names = (DATE, REVENUE, ATTEMPTS, IMPRESSIONS,
                    CPM, FILL_RATE, CLICKS, CPC, CTR)
        return sswriter.write_stats(f_type, stat_names, stats_list, days=days,
                key_type=sswriter.AD_NETWORK_APP_KEY, app_detail_name=('%s_%s' %
                (mapper.application.name.encode('utf8'), REPORTING_NETWORKS[
                    mapper.ad_network_name])))

@login_required
def export_app_detail_file(request, *args, **kwargs):
    return ExportAppDetailFileHandler()( request, *args, **kwargs )

# TODO: Move to admin views
class AdNetworkManagementHandler(RequestHandler):
    def get(self):
        """
        Create the ad network reports management page.

        Return a webpage with the list of management stats in a table grouped
        by network.
        """
        # If a custom daterange is not selected shift days back by one
        if len(self.request.GET) < 2:
            days = [day - timedelta(days=1) for day in self.days]
        else:
            days = self.days

        # Get dict of management stats where keys are the network names and the
        # values are the list of management stats over the give days
        management_stats = AdNetworkManagementStatsManager.get_stats(days)

        # Initialize dict of dicts
        networks = {}
        for ad_network_name in management_stats.keys():
            networks[ad_network_name] = {}

        # Fill in management stats for each network
        for name, stats_list in management_stats.iteritems():
            for stat in MANAGEMENT_STAT_NAMES:
                networks[name][stat] = sum([getattr(stats, stat) for stats in
                    stats_list])
            networks[name][FAILED] = sum([len(stats.failed_logins) for stats
                in stats_list])
            stats_list.reverse()
            networks[name]['sub_data_list'] = stats_list

        # Calculate aggregate management stats
        aggregates = {}
        for stat in MANAGEMENT_STAT_NAMES:
            aggregates[stat] = sum([stats[stat] for stats in networks.values()])
        aggregates[FAILED] = sum([stats[FAILED] for stats in
            networks.values()])
        aggregates[ACCOUNTS] = AdNetworkLoginManager.get_number_of_accounts()
        aggregates[LOGINS] = AdNetworkLoginManager.get_all_logins().count()

        # Group management stats by day instead of by network
        stats_by_date = {}
        for stats_list in management_stats.itervalues():
            for stats in stats_list:
                if stats.date in stats_by_date:
                    stats_by_date[stats.date].append(stats)
                else:
                    stats_by_date[stats.date] = [stats]

        # Calculate daily stats for the graph
        daily_stats = []
        for day in days:
            stats_dict = {}
            if day in stats_by_date:
                stats_tuple = stats_by_date[day]
                for stat in MANAGEMENT_STAT_NAMES:
                    stats_dict[stat] = int(sum([getattr(stats, stat) for stats
                        in stats_tuple]))
                stats_dict[FAILED] = int(sum([len(stats.failed_logins) for
                    stats in stats_tuple]))
            else:
                for stat in MANAGEMENT_STAT_NAMES:
                    stats_dict[stat] = 0
                stats_dict[FAILED] = 0
            daily_stats.append(stats_dict)

        # Sort the networks by name
        networks = sorted(networks.iteritems(), key=lambda network: network[0])

        return render_to_response(self.request,
              'ad_network_reports/ad_network_management.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'networks': networks,
                  'aggregates': aggregates,
                  'daily_stats': daily_stats
              })

@staff_login_required
def ad_network_management(request, *args, **kwargs):
    return AdNetworkManagementHandler()(request, *args, **kwargs)

