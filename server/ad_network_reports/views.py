import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AD_NETWORK_NAMES, \
        MOBFOX, MOBFOX_PRETTY, IAD_PRETTY, AdNetworkReportQueryManager, \
        AdNetworkMapperManager, AdNetworkStatsManager, \
        AdNetworkManagementStatsManager, create_fake_data
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.shortcuts import redirect
from reporting.models import StatsModel

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

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        #create_fake_data(self.account)

        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)


        mappers = list(AdNetworkMapperManager.get_ad_network_mappers(
            self.account))

        # Get aggregate stats for all the different ad network mappers for the
        # account between the selected date range
        aggregates_with_dates = [AdNetworkStatsManager. \
                get_stats_for_mapper_and_days(n, days) for n in mappers]
        if aggregates_with_dates:
            aggregates_list, applications, sync_dates = \
                    zip(*aggregates_with_dates)
        else:
            aggregates_list = []
            sync_dates = []
            applications = []
        aggregate_stats_list = zip(mappers, aggregates_list, applications,
                sync_dates)
        aggregates = AdNetworkStatsManager.roll_up_stats(aggregates_list)

        # Get the daily stats list.
        daily_stats = []
        for date in days:
            stats_dict = AdNetworkStatsManager.get_stats_for_day(self.account,
                    date).__dict__
            stats_dict = dict([(key.replace('_', '', 1), val) for key, val
                    in stats_dict.iteritems()])
            daily_stats.append(stats_dict)

        networks = AdNetworkStatsManager.roll_up_unique_stats(self.account,
                aggregate_stats_list, True)
        apps = AdNetworkStatsManager.roll_up_unique_stats(self.account,
                aggregate_stats_list, False)
        if networks:
            network_names, networks = zip(*networks)
        else:
            network_names = []
            networks = []

        forms = []
        from ad_network_reports.models import AdNetworkLoginCredentials
        for name in AD_NETWORK_NAMES.keys():
            try:
                instance = AdNetworkLoginCredentials. \
                        get_by_ad_network_name(self.account, name)
                form = LoginInfoForm(instance=instance, prefix=name)
                # Encryption doesn't work on app engine...
                #form.initial['password'] = instance.decoded_password
                #form.initial['username'] = instance.decoded_password
            except Exception, error:
                instance = None
                form = LoginInfoForm(prefix=name)
            form.ad_network = name
            forms.append(form)

        return render_to_response(self.request,
              'ad_network_reports/ad_network_reports_index.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'account_key' : str(self.account.key()),
                  'aggregates' : aggregates,
                  'daily_stats' : simplejson.dumps(
                      daily_stats),
                  'apps': apps,
                  'show_graph': apps != [],
                  'networks': zip(network_names, networks, forms),
                  'forms': forms,
                  'MOBFOX': MOBFOX_PRETTY,
                  'IAD': IAD_PRETTY
              })

@login_required
def ad_network_reports_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)

class ExportFileHandler(RequestHandler):
    def get(self, f_type):
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range)

        mappers = list(AdNetworkMapperManager.get_ad_network_mappers(
            self.account))

        # Get aggregate stats for all the different ad network mappers for the
        # account between the selected date range
        aggregates_with_dates = [AdNetworkStatsManager. \
                get_stats_for_mapper_and_days(n, days) for n in mappers]
        if aggregates_with_dates:
            aggregates_list, applications, sync_dates = \
                    zip(*aggregates_with_dates)
        else:
            aggregates_list = []
            sync_dates = []
            applications = []
        aggregate_stats_list = zip(mappers, aggregates_list, applications,
                sync_dates)

        networks = AdNetworkStatsManager.roll_up_unique_stats(self.account,
                aggregate_stats_list, True)

        stat_names = {}
        stat_names[MOBFOX_PRETTY] = (REVENUE, IMPRESSIONS, CPM, CLICKS,
                CPC, CTR)
        stat_names[sswriter.DEFAULT] = (REVENUE, ATTEMPTS, IMPRESSIONS,
                CPM, FILL_RATE, CLICKS, CPC, CTR)
        return sswriter.write_ad_network_stats(f_type, stat_names, networks,
                days=days)

@login_required
def export_file(request, *args, **kwargs):
    return ExportFileHandler()( request, *args, **kwargs )

class AppDetailHandler(RequestHandler):
    def get(self, mapper_key, *args, **kwargs):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)



        ad_network_app_mapper = AdNetworkMapperManager.get_ad_network_mapper(
                ad_network_app_mapper_key=mapper_key)
        stats_list = AdNetworkStatsManager.get_stats_list_for_mapper_and_days(
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
        return render_to_response(self.request,
                  'ad_network_reports/ad_network_base.html',
                  {
                      'start_date' : days[0],
                      'end_date' : days[-1],
                      'date_range' : self.date_range,
                      'ad_network_name' :
                        AD_NETWORK_NAMES[ad_network_app_mapper.ad_network_name],
                      'app_name' :
                        ad_network_app_mapper.application.name,
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
    def get(self, f_type, mapper_key):
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range)

        stats_list = AdNetworkStatsManager.get_stats_list_for_mapper_and_days(
                mapper_key, days)
        mapper = db.get(mapper_key)
        if mapper.ad_network_name == MOBFOX:
            stat_names = (DATE, REVENUE, IMPRESSIONS, CPM,
                    CLICKS, CPC, CTR)
        else:
            stat_names = (DATE, REVENUE, ATTEMPTS, IMPRESSIONS,
                    CPM, FILL_RATE, CLICKS, CPC, CTR)
        return sswriter.write_stats(f_type, stat_names, stats_list, days=days,
                key_type='ad_network')

@login_required
def export_app_detail_file(request, *args, **kwargs):
    return ExportAppDetailFileHandler()( request, *args, **kwargs )

class AdNetworkManagementHandler(RequestHandler):
    def get(self):
        """
        Create the ad network reports management page. Get the list of
        management stats and login credentials that resulted in error.
        Return a webpage with the list of management stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)

        management_stats = AdNetworkManagementStatsManager.get_stats(days)
        management_stats = sorted(management_sats.values(), key=lambda stats
                : stats.ad_network_name)

        return render_to_response(self.request,
              'ad_network_reports/ad_network_management.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'management_stats': management_stats
              })

@login_required
def ad_network_management(request, *args, **kwargs):
    return AdNetworkManagementHandler()(request, *args, **kwargs)

