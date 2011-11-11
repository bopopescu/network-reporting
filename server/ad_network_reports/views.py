import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AD_NETWORK_NAMES, \
        AdNetworkReportQueryManager, get_management_stats, create_manager
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.shortcuts import redirect
from reporting.models import StatsModel

from account.models import Account

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self, account_key=None):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)

        manager = create_manager(account_key, self.account)
        aggregates, daily_stats, aggregate_stats_list = manager.get_index_data(days)

        if account_key:
            add_credentials_url = '/ad_network_reports/manage/' + \
                                  str(account_key) + '/add'
        else:
            add_credentials_url = '/ad_network_reports/add'



        # Put the apps into an intuitive data structure
        # Apps are mapped to their stats, as well as to a list of
        # their individual network stats. E.g. :
        # {
        #     'app1' : {
        #         'networks': [ {network1_stats ... networkn_stats],
        #         'revenue': 0,
        #         'attempts': 0,
        #         'impressions': 0,
        #         'fill_rate': 0,
        #         'clicks': 0,
        #         'ctr': 0,
        #     }
        # }
        #
        # lol so tarded, sry
        apps = {}
        for key, mapper, stats in aggregate_stats_list:
            network_data_for_app = {
                'name': mapper.ad_network_name,
                'revenue': stats.revenue,
                'attempts': stats.attempts,
                'impressions': stats.impressions,
                'fill_rate': stats.fill_rate,
                'clicks': stats.clicks,
                'ctr': stats.ctr,
            }
            if apps.has_key(mapper.application.name):
                apps[mapper.application.name]['networks'].append(network_data_for_app)
                apps[mapper.application.name]['revenue'] += network_data_for_app['revenue']
                apps[mapper.application.name]['attempts'] += network_data_for_app['attempts']
                apps[mapper.application.name]['impressions'] += network_data_for_app['impressions']
                apps[mapper.application.name]['fill_rate'] += network_data_for_app['fill_rate']
                apps[mapper.application.name]['clicks'] += network_data_for_app['clicks']
                apps[mapper.application.name]['ctr'] += network_data_for_app['ctr']
            else:
                apps[mapper.application.name] = {
                    'networks': [],
                    'revenue': 0,
                    'attempts': 0,
                    'impressions': 0,
                    'fill_rate': 0,
                    'clicks': 0,
                    'ctr': 0,
                }
                apps[mapper.application.name]['networks'].append(network_data_for_app)
                apps[mapper.application.name]['key'] = str(key)
                apps[mapper.application.name]['revenue'] += network_data_for_app['revenue']
                apps[mapper.application.name]['attempts'] += network_data_for_app['attempts']
                apps[mapper.application.name]['impressions'] += network_data_for_app['impressions']
                apps[mapper.application.name]['fill_rate'] += network_data_for_app['fill_rate']
                apps[mapper.application.name]['clicks'] += network_data_for_app['clicks']
                apps[mapper.application.name]['ctr'] += network_data_for_app['ctr']


        # Do the same for networks
        networks = {}
        for key, mapper, stats in aggregate_stats_list:
            app_data_for_network = {
                'name': mapper.application.name,
                'revenue': stats.revenue,
                'attempts': stats.attempts,
                'impressions': stats.impressions,
                'fill_rate': stats.fill_rate,
                'clicks': stats.clicks,
                'ctr': stats.ctr,
                'key': str(key)
            }
            if networks.has_key(mapper.ad_network_name):
                networks[mapper.ad_network_name]['apps'].append(app_data_for_network)
                networks[mapper.ad_network_name]['revenue'] += app_data_for_network['revenue']
                networks[mapper.ad_network_name]['attempts'] += app_data_for_network['attempts']
                networks[mapper.ad_network_name]['impressions'] += app_data_for_network['impressions']
                networks[mapper.ad_network_name]['fill_rate'] += app_data_for_network['fill_rate']
                networks[mapper.ad_network_name]['clicks'] += app_data_for_network['clicks']
                networks[mapper.ad_network_name]['ctr'] += app_data_for_network['ctr']
            else:
                networks[mapper.ad_network_name] = {
                    'apps': [],
                    'revenue': 0,
                    'attempts': 0,
                    'impressions': 0,
                    'fill_rate': 0,
                    'clicks': 0,
                    'ctr': 0,
                }
                networks[mapper.ad_network_name]['apps'].append(app_data_for_network)
                networks[mapper.ad_network_name]['key'] = str(key)
                networks[mapper.ad_network_name]['revenue'] += app_data_for_network['revenue']
                networks[mapper.ad_network_name]['attempts'] += app_data_for_network['attempts']
                networks[mapper.ad_network_name]['impressions'] += app_data_for_network['impressions']
                networks[mapper.ad_network_name]['fill_rate'] += app_data_for_network['fill_rate']
                networks[mapper.ad_network_name]['clicks'] += app_data_for_network['clicks']
                networks[mapper.ad_network_name]['ctr'] += app_data_for_network['ctr']


        # REFACTOR
        # Each view should return one template only.

        if aggregate_stats_list:
            return render_to_response(self.request,
                                      'ad_network_reports/ad_network_reports_index.html',
                                      {
                                          'start_date' : days[0],
                                          'end_date' : days[-1],
                                          'date_range' : self.date_range,
                                          'add_credentials_url' : add_credentials_url,
                                          'aggregates' : aggregates,
                                          'daily_stats' : simplejson.dumps(daily_stats),
                                          'aggregate_stats_list' : aggregate_stats_list,
                                          'apps': apps,
                                          'networks': networks
                                      })
        else:
            return render_to_response(self.request,
                                      'ad_network_reports/ad_network_setup.html',
                                      {
                                          'add_credentials_url': add_credentials_url,
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
        ad_network_app_mapper = manager.get_ad_network_mapper(ad_network_app_mapper_key=mapper_key)
        stats_list = manager.get_stats_list_for_mapper_and_days(ad_network_app_mapper_key, days)
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
def app_detail(request, *args, **kwargs):
    return AppDetailHandler()(request, *args, **kwargs)



class AddLoginCredentialsHandler(RequestHandler):
    #TODO: Make SSL iframe
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
        for name in AD_NETWORK_NAMES:
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
                                      'ad_network_names' : AD_NETWORK_NAMES,
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