from django.contrib.auth.decorators import login_required

from common.ragendja.template import render_to_response
from common.utils.request_handler import RequestHandler

from network_scraping.query_managers import AdNetworkReportQueryManager

IS_PRODUCTION = False

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        if IS_PRODUCTION:
            manager = AdNetworkReportQueryManager(self.account)
        else:
            from network_scraping.tests.load_test_data import TestDataLoader
            manager = AdNetworkReportQueryManager(Accounts.get_by_key_name(TestDataLoader.ACCOUNT_KEY_NAME)) 
        totals = manager.get_ad_network_totals()
                
        return render_to_response(self.request, 'network_scraping/ad_network_index.html',
                dict(totals = totals))
                     
@login_required
def adnetwork_report_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)
     
class ViewAdNetworkReportHandler(RequestHandler):
    def get(self, ad_network_app_mapper_key, *args, **kwargs):
        manager = AdNetworkReportQueryManager(self.account)
        dates = manager.get_ad_network_app_stats(ad_network_app_mapper)
        
        ad_network_name = manager.get_ad_network_app_mapper(ad_network_app_mapper_key = ad_network_app_mapper_key).ad_network_name
        return render_to_response(self.request, 'network_scraping/view_app_ad_network_report.html',
                dict(ad_network_name = ad_network_name,
                     dates = dates))

@login_required
def view_adnetwork_app_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)
    
class AddLoginInfoHandler(RequestHandler):
    def get(self):
        """ Input login info and select what apps you want to use it for and store it in the db """
        manager = AdNetworkReportQueryManager(self.account)
        totals = manager.get_ad_network_totals()

        return render_to_response(self.request, 'network_scraping/.html',
                dict(totals = totals))

@login_required
def add_login_info(request, *args, **kwargs):
    return AddLoginInfoHandler()(request, *args, **kwargs)