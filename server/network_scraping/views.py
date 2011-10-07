import logging

from django.contrib.auth.decorators import login_required

from common.ragendja.template import render_to_response
from common.utils.request_handler import RequestHandler
from datetime import timedelta, date
from network_scraping.query_managers import AdNetworkReportQueryManager

from google.appengine.ext import db
from network_scraping.models import *

# from network_scraping import ad_networks

IS_PRODUCTION = False

class AdNetworkReportIndexHandler(RequestHandler):
    def get(self):
        if IS_PRODUCTION:
            manager = AdNetworkReportQueryManager(self.account)
            mappers = manager.get_ad_network_mappers()
        else:
            # from network_scraping.load_test_data import TestDataLoader
            # manager = AdNetworkReportQueryManager(TestDataLoader.ACCOUNT_KEY_NAME)
            manager = AdNetworkReportQueryManager('test')
            query = AdNetworkAppMapper.all()
            mappers = list(query)
        
        keys = [s.key() for s in mappers]
        # Get aggregate stats for all the different ad network mappers for the account between the selected date range
        aggregates = [manager.get_ad_network_aggregates(n, date.today() - timedelta(days = 8), date.today() - timedelta(days = 1)) for n in mappers]
        aggregate_stats = zip(keys, mappers, aggregates)
        
        # Sort alphabetically by application name then by ad network name
        aggregate_stats = sorted(aggregate_stats, key = lambda s: s[1].application.name + s[1].ad_network_name)
        
        return render_to_response(self.request, 'network_scraping/ad_network_index.html',
                dict(aggregate_stats = aggregate_stats))
                     
@login_required
def ad_network_report_index(request, *args, **kwargs):
    return AdNetworkReportIndexHandler()(request, *args, **kwargs)
     
class ViewAdNetworkReportHandler(RequestHandler):
    def get(self, ad_network_app_mapper_key, *args, **kwargs):
        manager = AdNetworkReportQueryManager(self.account)
        
        logging.warning("ad_network_app_mapper_key = %s" % ad_network_app_mapper_key)
        ad_network_app_mapper = manager.get_ad_network_app_mapper(ad_network_app_mapper_key = ad_network_app_mapper_key)
        dates = manager.get_ad_network_app_stats(ad_network_app_mapper)
        return render_to_response(self.request, 'network_scraping/view_app_ad_network_report.html',
                dict(ad_network_name = ad_network_app_mapper.ad_network_name,
                     dates = dates))

@login_required
def view_ad_network_app_report(request, *args, **kwargs):
    return ViewAdNetworkReportHandler()(request, *args, **kwargs)
    
class AddLoginInfoHandler(RequestHandler):
    def get(self): #Verfify that this is SSL
        """ Input login info and select what apps you want to use it for and store it in the db """

        return render_to_response(self.request, 'network_scraping/add_login_info.html',
                                  dict(ad_network_names = ['admob', 'jumptap', 'iad', 'inmobi', 'mobfox']))#ad_networks.ad_networks.keys()))
                                  
    def post(self, ad_network_name, username = None, password = None, client_key = None, send_email = False):
        """ Create AdNetworkLoginInfo and AdNetworkAppMappers for all apps that have pub ids for this network and account """
        
        manager = AdNetworkReportQueryManager(self.account)
        
        apps_with_publisher_ids = manager.get_apps_with_publisher_ids(ad_network_name)
        
        # get the apps in the ad network
        publisher_ids = [publisher_id for app, publisher_id in apps_with_publisher_ids]
        
        login_info = AdNetworkLoginInfo(account = self.account, ad_network_name = ad_network_name, username = username, client_key = client_key, publisher_ids = publisher_ids)
        login_info.put()
        
        # Create all the different AdNetworkAppMappers for all the applications on the ad network for the user and add them to the db
        db.put([AdNetworkAppMapper(ad_network_name = ad_network_name, publisher_id = publisher_id,
                ad_network_login = login_info, application = app, send_email = False) for 
                app, publisher_id in apps_with_publisher_ids])
        

@login_required
def add_login_info(request, *args, **kwargs):
    return AddLoginInfoHandler()(request, *args, **kwargs)