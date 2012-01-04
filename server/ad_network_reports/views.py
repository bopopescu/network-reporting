import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AD_NETWORK_NAMES, \
        MOBFOX, \
        MOBFOX_PRETTY, \
        IAD_PRETTY, \
        AdNetworkReportManager, \
        AdNetworkLoginCredentialsManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkManagementStatsManager, \
        create_fake_data
from common.utils.decorators import staff_login_required
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
SORT_BY_NETWORK = 'network'
MANAGEMENT_STAT_NAMES = ('found', 'updated', 'mapped', 'attempted_logins')
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

        days = get_days(self.start_date, self.date_range)

        aggregate_stats_list = AdNetworkReportManager. \
                get_aggregate_stats_list(self.account, days)

        # Get aggregate_list from aggregate_stats_list and pass it to
        # roll_up_stats.
        if aggregate_stats_list:
            aggregates = AdNetworkStatsManager.roll_up_stats(
                    zip(*aggregate_stats_list)[1])
        else:
            aggregates = []

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
        for name in sorted(AD_NETWORK_NAMES.keys()):
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
    def get(self,
            f_type,
            sort_type):
        """
        Take a file type (xls or csv).

        Return a file with the aggregate stats data sorted by network or app.
        """
        days = get_days(self.start_date, self.date_range)

        aggregate_stats_list = AdNetworkReportManager. \
                get_aggregate_stats_list(self.account, days)

        if sort_type == SORT_BY_NETWORK:
            all_stats = AdNetworkStatsManager.roll_up_unique_stats(self.account,
                    aggregate_stats_list, True)
        else:
            all_stats = AdNetworkStatsManager.roll_up_unique_stats(self.account,
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
        days = get_days(self.start_date, self.date_range)

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
        app = ad_network_app_mapper.application
        return render_to_response(self.request,
                  'ad_network_reports/ad_network_base.html',
                  {
                      'start_date' : days[0],
                      'end_date' : days[-1],
                      'date_range' : self.date_range,
                      'ad_network_name' :
                        AD_NETWORK_NAMES[ad_network_app_mapper.ad_network_name],
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
        days = get_days(self.start_date, self.date_range)

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
                key_type=sswriter.AD_NETWORK_APP_KEY, app_detail_name=('%s_%s' %
                (mapper.application.name.encode('utf8'), AD_NETWORK_NAMES[
                    mapper.ad_network_name])))

@login_required
def export_app_detail_file(request, *args, **kwargs):
    return ExportAppDetailFileHandler()( request, *args, **kwargs )

# TODO: Move to admin views
class AdNetworkManagementHandler(RequestHandler):
    def get(self):
        """
        Create the ad network reports management page. Get the list of
        management stats and login credentials that resulted in error.
        Return a webpage with the list of management stats in a table.
        """
        days = get_days(self.start_date, self.date_range)

        management_stats = AdNetworkManagementStatsManager.get_stats(days)

        networks = {}
        for ad_network_name in management_stats.keys():
            networks[ad_network_name] = {}
        for name, stats_list in management_stats.iteritems():
            for stat in MANAGEMENT_STAT_NAMES:
                networks[name][stat] = sum([getattr(stats, stat) for stats in
                    stats_list])
            networks[name][FAILED] = sum([len(stats.failed_logins) for stats
                in stats_list])
            stats_list.reverse()
            networks[name]['sub_data_list'] = stats_list

        aggregates = {}
        for stat in MANAGEMENT_STAT_NAMES:
            aggregates[stat] = sum([stats[stat] for stats in networks.values()])
        aggregates[FAILED] = sum([stats['failed'] for stats in
            networks.values()])
        aggregates[ACCOUNTS] = AdNetworkLoginCredentialsManager.get_number_of_accounts()
        aggregates[LOGINS] = AdNetworkLoginCredentialsManager.get_all_login_credentials().count()

        stats_by_date = {}
        for stats_tuple in zip(*management_stats.values()):
            stats_by_date[stats_tuple[0].date] = stats_tuple

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

def get_days(start_date,
             date_range):
    """
    Take a start date and a date range.

    Return a list of days, [datetime.date,...], objects for the given range.
    """
    if start_date:
        days = StatsModel.get_days(start_date, date_range)
    else:
        days = StatsModel.lastdays(date_range, 1)
    return days

