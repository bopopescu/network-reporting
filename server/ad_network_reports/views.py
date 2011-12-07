import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AD_NETWORK_NAMES, \
        AdNetworkReportQueryManager, get_management_stats, create_fake_data
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.shortcuts import redirect
from reporting.models import StatsModel

from account.models import Account

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

        manager = AdNetworkReportQueryManager(self.account)
        aggregates, daily_stats, networks, apps = manager. \
                get_index_data(days)


        forms = []
        for name in sorted(AD_NETWORK_NAMES.keys()):
            try:
                instance = AdNetworkLoginCredentials. \
                        get_by_ad_network_name(self.account, name)
                form = LoginInfoForm(instance=instance, prefix=name)
            except Exception, error:
                instance = None
                form = LoginInfoForm(prefix=name)
            form.ad_network = name
            forms.append(form)



        # Get networks for which they've entered publisher information but
        # havent given us login credentials so we can bug them about giving us
        # their creds
        networks_without_creds = \
                list(manager.get_networks_without_credentials())

        network_names, networks = zip(*networks)
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
                              'forms': forms
                          })

@login_required
def ad_network_reports_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)


class AppDetailHandler(RequestHandler):
    def get(self, mapper_key, *args, **kwargs):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)

        manager = AdNetworkReportQueryManager()
        ad_network_app_mapper = manager.get_ad_network_mapper(
                ad_network_app_mapper_key=mapper_key)
        stats_list = manager.get_stats_list_for_mapper_and_days(mapper_key,
                days)
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
        aggregates = manager.roll_up_stats(stats_list)
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
                                      'show_graph': True
                                  })

@login_required
def app_detail(request, *args, **kwargs):
    return AppDetailHandler()(request, *args, **kwargs)



class NetworkDetailHandler(RequestHandler):
    def get(self, network_name, *args, **kwargs):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)


        manager = AdNetworkReportQueryManager(self.account)
        networks = manager._




        ad_network_app_mapper = manager.get_ad_network_mapper(ad_network_app_mapper_key=mapper_key)
        stats_list = manager.get_stats_list_for_mapper_and_days(mapper_key, days)
        daily_stats = []
        for stats in stats_list:
            stats_dict = stats.__dict__['_entity']
            del(stats_dict['ad_network_app_mapper'])
            del(stats_dict['date'])
            daily_stats.append(stats_dict)
        aggregates = manager.roll_up_stats(stats_list)
        return render_to_response(self.request,
                                  'ad_network_reports/ad_network_base.html',
                                  {
                                      'start_date' : days[0],
                                      'end_date' : days[-1],
                                      'date_range' : self.date_range,
                                      'ad_network_name' : ad_network_app_mapper.ad_network_name,
                                      'app_name' : ad_network_app_mapper.application.name,
                                      'aggregates' : aggregates,
                                      'daily_stats' : simplejson.dumps(daily_stats),
                                      'stats_list' : stats_list
                                  })


@login_required
def network_detail(request, *args, **kwargs):
    return NetworkDetailHandler()(request, *args, **kwargs)



class AddLoginCredentialsHandler(RequestHandler):
    def get(self, account_key=None):
        """
        Return form with ad network login info.
        """

        if account_key:
            account = Account.get(account_key)
            management_mode = True
        else:
            account = self.account
            account_key = self.account.key()
            management_mode = False

        forms = []
        for name in AD_NETWORK_NAMES.keys():
            try:
                instance = AdNetworkLoginCredentials.get_by_ad_network_name(account, name)
                form = LoginInfoForm(instance=instance, prefix=name)
            except Exception, error:
                instance = None
                form = LoginInfoForm(prefix=name)
            form.ad_network = name
            forms.append(form)

        return render_to_response(self.request,
                                  'ad_network_reports/add_login_credentials.html',
                                  {
                                      'management_mode' : management_mode,
                                      'account_key' : str(account_key),
                                      'ad_network_names' :
                                        AD_NETWORK_NAMES.keys(),
                                      'forms' : forms,
                                      'error' : "",
                                  })

@login_required
def add_login_credentials(request, *args, **kwargs):
    return AddLoginCredentialsHandler()(request, *args, **kwargs)


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

        management_stats_list = get_management_stats(days)

        return render_to_response(self.request,
                                  'ad_network_reports/ad_network_management.html',
                                  {
                                      'start_date' : days[0],
                                      'end_date' : days[-1],
                                      'date_range' : self.date_range,
                                      'management_stats_list': management_stats_list
                                  })

@login_required
def ad_network_management(request, *args, **kwargs):
    return AdNetworkManagementHandler()(request, *args, **kwargs)
