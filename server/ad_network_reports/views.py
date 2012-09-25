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
from common.ragendja.template import render_to_response, \
        TextResponse, \
        JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from common.constants import NETWORKS, \
        REPORTING_NETWORKS

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


# TODO: the request handler needs an account_key property, since it won't have an account anymore
class LoginStateHandler(RequestHandler):
    def post(self):
        """Return the login state given the account key and network_type

        Args:
            account_key: an account key
            network_type: a string, the base name of the network being modified, must be in NETWORKS

        Return:
            an integer: AdNetworkLoginCredentials.state
	    
        Author:
            Tiago Bandeira (7/17/2012)
        """
        account_key = db.Key(self.request.POST.get('account_key'))
        network_type = self.request.POST.get('network_type')

        login_state = 0
        if network_type in REPORTING_NETWORKS:
            login = AdNetworkLoginManager.get_logins(self.account_key, network_type).get()
            if login:
                login_state = login.state

        return JSONResponse({'login_state': login_state})

def login_state(request, *args, **kwargs):
    return LoginStateHandler()(request, *args, **kwargs)


class CreateMapperHandler(RequestHandler):
    def post(self):
        """Create mapper for the given network_type, app, and pub_id. Delete existing mappers
        with the same network_type and app if they don't have stats.

        Args:
            network_type: a string, the base name of the network being modified, must be in NETWORKS
            app_key: an application key
            pub_id: a string, the value of the new publisher id

        Author:
            Tiago Bandeira (7/17/2012)
        """
        network_type = self.request.POST.get('network_type')
        app_key = db.Key(self.request.POST.get('app_key'))
        pub_id = self.request.POST.get('pub_id')

        if network_type in REPORTING_NETWORKS:
            # Create an AdNetworkAppMapper if there exists a
            # login for the network (safe to re-create if it
            # already exists)
            login = AdNetworkLoginManager.get_logins(
                    self.account_key, network_type).get()
            if login:
                mappers = AdNetworkMapperManager.get_mappers_for_app(login=login, app=app_key)
                # Delete the existing mappers if there are no scrape
                # stats for them.
                for mapper in mappers:
                    if mapper:
                        stats = mapper.ad_network_stats
                        if not stats.count(1):
                            mapper.delete()
                if pub_id:
                    AdNetworkMapperManager.create(network=network_type,
                            pub_id=pub_id, login=login, app=app_key)

        return TextResponse()

def create_mapper(request, *args, **kwargs):
    return CreateMapperHandler()(request, *args, **kwargs)


class AdNetworkSettingsHandler(RequestHandler):
    def post(self):
        account_settings = AdNetworkAccountSettingsManager.get_by_account_key(self.account_key)# TODO

        account_settings.email = self.request.POST.get('email', False) and True
        account_settings.recipients = [recipient.strip() for recipient in self.request.POST.get(
            'recipients').split(',')]

        AdNetworkAccountSettingsManager.put(account_settings)

        return TextResponse('done')

@login_required
def ad_network_settings(request, *args, **kwargs):
    return AdNetworkSettingsHandler()(request, *args, **kwargs)


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

