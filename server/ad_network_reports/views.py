from ad_network_reports.query_managers import AdNetworkReportQueryManager
from common.ragendja.template import render_to_response
from common.utils.request_handler import RequestHandler
from datetime import timedelta, date
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

AD_NETWORK_NAMES = ['admob', 'jumptap', 'iad', 'inmobi', 'mobfox']

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        """Generate a list of aggregtate stats for the ad networks, apps and
        account.

        Return a webpage with the list of stats in a table.
        """
        manager = AdNetworkReportQueryManager(self.account)
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
                'ad_network_reports/ad_network_index.html', dict(aggregate_stats
                    = aggregate_stats))

@login_required
def ad_network_report_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)

class ViewAdNetworkReportHandler(RequestHandler):
    def get(self, ad_network_app_mapper_key, *args, **kwargs):
        """Generate a list of stats for the ad network, app and account.

        Return a webpage with the list of stats in a table.
        """
        manager = AdNetworkReportQueryManager(self.account)
        ad_network_app_mapper = manager.get_ad_network_app_mapper(
                ad_network_app_mapper_key = ad_network_app_mapper_key)
        dates = manager.get_ad_network_app_stats(ad_network_app_mapper)
        return render_to_response(self.request,
                'ad_network_reports/view_app_ad_network_report.html',
                dict(ad_network_name = ad_network_app_mapper.ad_network_name,
                     app_name = ad_network_app_mapper.application.name,
                     dates = dates))

@login_required
def view_ad_network_app_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)

class AddLoginInfoHandler(RequestHandler):
    def get(self): #Verfify that this is SSL
        """Return form with ad network login info."""
        return render_to_response(self.request,
                'ad_network_reports/add_login_info.html',
                dict(ad_network_names = AD_NETWORK_NAMES, error = ""))

    def post(self):
        """Create AdNetworkLoginInfo and AdNetworkAppMappers for all apps that
        have pub ids for this network and account.

        Return a redirect to the ad nework report index.
        """
        ad_network_name = self.request.POST['ad_network_name']
        username = self.request.POST['username']
        password = self.request.POST['password']
        client_key = self.request.POST['client_key']
        send_email = eval(self.request.POST.get('send_email', 'False'))

        manager = AdNetworkReportQueryManager(self.account)

        error = manager.create_login_info_and_mappers(ad_network_name, username,
                password, client_key, send_email)

        if error:
            return render_to_response(self.request,
                    'ad_network_reports/add_login_info.html',
                    dict(ad_network_names = AD_NETWORK_NAMES, error = error))
        else:
            return redirect('ad_network_reports_index')

@login_required
def add_login_info(request, *args, **kwargs):
    return AddLoginInfoHandler()(request, *args, **kwargs)
