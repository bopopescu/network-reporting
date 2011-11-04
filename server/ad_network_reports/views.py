import copy
import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        get_management_stats, create_manager
from common.ragendja.template import render_to_response, TextResponse
from common.utils.request_handler import RequestHandler
from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.shortcuts import redirect
from reporting.models import StatsModel

from account.models import Account

AD_NETWORK_NAMES = ['admob', 'jumptap', 'iad', 'inmobi', 'mobfox']

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self, account_key=None):
        """Create the index page for ad network reports for an account.

        Create a manager and get required stats for the webpage.

        Return a webpage with the list of stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)

        manager = create_manager(account_key, self.account)

        aggregates, daily_stats, aggregate_stats_list = manager. \
                get_index_stats(days)

        if account_key:
            add_credentials_url = '/ad_network_reports/manage/' + \
                    str(account_key) + '/add'
        else:
            add_credentials_url = '/ad_network_reports/add'

        if aggregate_stats_list:
            return render_to_response(self.request,
                                      'ad_network_reports/ad_network_index' \
                                              '.html',
                                      {
                                          'start_date' : days[0],
                                          'end_date' : days[-1],
                                          'date_range' : self.date_range,
                                          'add_credentials_url' :
                                          add_credentials_url,
                                          'aggregates' : aggregates,
                                          'daily_stats' : simplejson.dumps(
                                              daily_stats),
                                          'aggregate_stats_list' :
                                            aggregate_stats_list
                                      })
        else:
            return render_to_response(self.request,
                                      'ad_network_reports/ad_network_setup' \
                                              '.html',
                                      {
                                          'add_credentials_url' :
                                          add_credentials_url,
                                      })

@login_required
def ad_network_report_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)

class ViewAdNetworkReportHandler(RequestHandler):
    def get(self, ad_network_app_mapper_key, *args, **kwargs):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        manager = AdNetworkReportQueryManager()
        ad_network_app_mapper = manager.get_ad_network_app_mapper(
                ad_network_app_mapper_key=ad_network_app_mapper_key)
        stats_list = manager.get_ad_network_app_stats(ad_network_app_mapper)
        daily_stats = [stats.__dict__ for stats in stats_list]
        aggregates = manager.roll_up_stats(stats_list)
        return render_to_response(self.request,
                                  'ad_network_reports/'
                                  'ad_network_base.html',
                                  {
                                      'ad_network_name' :
                                      ad_network_app_mapper.ad_network_name,
                                      'app_name' : ad_network_app_mapper.
                                      application.name,
                                      'aggregates' : aggregates,
                                      'daily_stats' : simplejson.dumps(
                                          daily_stats),
                                       'stats' : stats_list
                                  })

@login_required
def view_ad_network_app_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)

class AddLoginInfoHandler(RequestHandler):
    #TODO: Make SSL iframe
    def get(self, account_key=None):
        """Return form with ad network login info."""
        # Add a bunch of test data to the db
        #load_test_data(self.account)

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
                instance = AdNetworkLoginCredentials.get_by_ad_network_name(
                        account, name)
                form = LoginInfoForm(instance=instance, prefix=name)
            except Exception, error:
                instance = None
                form = LoginInfoForm(prefix=name)
            form.ad_network = name
            forms.append(form)

        logging.warning('account_key')
        logging.warning(str(account_key))
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
    return AddLoginInfoHandler()(request, *args, **kwargs)

class AdNetworkReportManageHandler(RequestHandler):
    def get(self):
        """Create the ad network reports management page.

        Get the list of management stats and login credentials that resulted in
        error.

        Return a webpage with the list of management stats in a table.
        """
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range, 1)

        management_stats_list = [dict(management_stats).items() for
                management_stats in get_management_stats(days)] or [[("NO" \
                        " DATA", 0)]]
        logging.warning(management_stats_list)
        for key, value in management_stats_list[0]:
            logging.warning(key)

        return render_to_response(self.request,
                                  'ad_network_reports/manage_ad_network_' \
                                          'reports.html',
                                  {
                                      'start_date' : days[0],
                                      'end_date' : days[-1],
                                      'date_range' : self.date_range,
                                      'management_stats_list' :
                                      management_stats_list
                                  })

@login_required
def manage_ad_network_reports(request, *args, **kwargs):
    return AdNetworkReportManageHandler()(request, *args, **kwargs)

def load_test_data(account=None):
    from account.models import NetworkConfig
    from publisher.models import App, Site
    from google.appengine.ext import db
    from account.models import Account, NetworkConfig

    if account == None:
        account = Account()
        account.put()

    chess_network_config = NetworkConfig(jumptap_pub_id=
            'jumptap_chess_com_test', iad_pub_id='329218549')
    chess_network_config.put()

    chess_app = App(account=account, name="Chess.com - Play & Learn Chess",
            network_config = chess_network_config)
    chess_app.put()

    bet_network_config = NetworkConfig(jumptap_pub_id='jumptap_bet_test',
            admob_pub_id = 'a14c7d7e56eaff8')
    bet_network_config.put()

    bet_iad_network_config = NetworkConfig(iad_pub_id='418612824')
    bet_iad_network_config.put()

    bet_app = App(account=account, name="BET WAP Site", network_config=
            bet_network_config)
    bet_app.put()

    adunit_network_config = NetworkConfig(jumptap_pub_id=
    'bet_wap_site_106andpark_top').put()
    Site(app_key=bet_app, network_config=adunit_network_config).put()

    bet_iad_app = App(account=account, name="106 & Park", network_config=
            bet_iad_network_config)
    bet_iad_app.put()

    officejerk_network_config = NetworkConfig(jumptap_pub_id='office_jerk_test')
    officejerk_network_config.put()

    officejerk_app = App(account=account, name="Office Jerk", network_config=
            officejerk_network_config)
    officejerk_app.put()
