import copy
import logging

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        create_manager
from common.ragendja.template import render_to_response
from common.utils.request_handler import RequestHandler
from datetime import timedelta, date
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from account.models import Account

AD_NETWORK_NAMES = ['admob', 'jumptap', 'iad', 'inmobi', 'mobfox']

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self, account_key=None):
        """Generate a list of aggregtate stats for the ad networks, apps and
        account.

        Return a webpage with the list of stats in a table.
        """
        manager = create_manager(account_key, self.account)
        mappers = list(manager.get_ad_network_mappers())

        keys = [s.key() for s in mappers]
        # Get aggregate stats for all the different ad network mappers for the
        # account between the selected date range
        aggregates = [manager.get_ad_network_aggregates(n, date.today() -
            timedelta(days = 8), date.today() - timedelta(days = 1)) for n in
            mappers]
        aggregate_stats = zip(keys, mappers, aggregates)

        # Sort alphabetically by application name then by ad network name
        aggregate_stats = sorted(aggregate_stats, key = lambda s:
                s[1].application.name + s[1].ad_network_name)

        return render_to_response(self.request,
                                  'ad_network_reports/ad_network_index.html',
                                  {
                                      "aggregate_stats" : aggregate_stats,
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
                ad_network_app_mapper_key = ad_network_app_mapper_key)
        dates = manager.get_ad_network_app_stats(ad_network_app_mapper)
        return render_to_response(self.request,
                                  'ad_network_reports/'
                                  'view_app_ad_network_report.html',
                                  {
                                      "ad_network_name" :
                                      ad_network_app_mapper.ad_network_name,
                                      "app_name" : ad_network_app_mapper.
                                      application.name,
                                       "dates" : dates
                                  })

@login_required
def view_ad_network_app_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)

class AddLoginInfoHandler(RequestHandler):
    #TODO: Make SSL iframe
    def get(self, account_key=None):
        """Return form with ad network login info."""
        # Add a bunch of test data to the db
#        from account.models import NetworkConfig
#        from publisher.models import App, Site
#        from google.appengine.ext import db
#        from account.models import Account, NetworkConfig
#        chess_network_config = NetworkConfig(jumptap_pub_id = 'jumptap_chess_com_test', iad_pub_id = '329218549')
#        chess_network_config.put()
#
#        chess_app = App(account = self.account, name = "Chess.com - Play & Learn Chess", network_config = chess_network_config)
#        chess_app.put()
#
#        bet_network_config = NetworkConfig(jumptap_pub_id = 'jumptap_bet_test', admob_pub_id = 'a14c7d7e56eaff8')
#        bet_network_config.put()
#
#        bet_iad_network_config = NetworkConfig(iad_pub_id = '418612824')
#        bet_iad_network_config.put()
#
#        bet_app = App(account = self.account, name = "BET WAP Site", network_config = bet_network_config) # Name must be the same as in Jumptap
#        bet_app.put()
#
#        adunit_network_config = NetworkConfig(jumptap_pub_id =
#        'bet_wap_site_106andpark_top').put()
#        Site(app_key = bet_app, network_config = adunit_network_config).put()
#
#        bet_iad_app = App(account = self.account, name = "106 & Park", network_config = bet_iad_network_config)
#        bet_iad_app.put()
#
#        officejerk_network_config = NetworkConfig(jumptap_pub_id = 'office_jerk_test')
#        officejerk_network_config.put()
#
#        officejerk_app = App(account = self.account, name = "Office Jerk", network_config = officejerk_network_config)
#        officejerk_app.put()
#        if account_key:
#            account = Account.get(account)
#        else:
#            account = self.account

        forms = []
        for name in AD_NETWORK_NAMES:
            try:
                instance = AdNetworkLoginInfo.get_by_network(account, name)
                form = LoginInfoForm(instance=instance, prefix=name)
            except Exception, error:
                instance = None
                form = LoginInfoForm(prefix=name)
            form.ad_network = name
            forms.append(form)

        return render_to_response(self.request,
                                  'ad_network_reports/add_login_info.html',
                                  {
                                      'account_key' : account_key,
                                      'ad_network_names' : AD_NETWORK_NAMES,
                                      'forms' : forms,
                                      'error' : "",
                                  })

    def post(self, account_key=None):
        """Create AdNetworkLoginInfo and AdNetworkAppMappers for all apps that
        have pub ids for this network and account.

        Return a redirect to the ad nework report index.
        """
        logging.warning("Trying to create login info")

        initial = {}
        for network in AD_NETWORK_NAMES:
            initial[network + '-ad_network_name'] = network

        ad_network = self.request.POST['ad_network_name']
        wants_email = self.request.POST.get('email', False) and True

        postcopy = copy.deepcopy(self.request.POST)
        postcopy.update(initial)

        form = LoginInfoForm(postcopy, prefix=ad_network)

        if form.is_valid():
            logging.warning("Creating SHit")
            logging.warning(form.cleaned_data)
            manager = create_manager(account_key, self.account)
            manager.create_login_info_and_mappers(ad_network,
                    form.cleaned_data['username'],
                    form.cleaned_data['password'],
                    form.cleaned_data['client_key'],
                    wants_email)

        logging.warn(form.errors)

@login_required
def add_login_info(request, *args, **kwargs):
    return AddLoginInfoHandler()(request, *args, **kwargs)
