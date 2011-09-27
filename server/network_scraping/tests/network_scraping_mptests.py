import os, sys
sys.path.append(os.environ['PWD'])

# magic test import
import common.utils.test.setup

import simplejson as json

from account.models import Account
from publisher.models import App

from network_scraping.adnetwork_update import *
from network_scraping.models import AdNetworkLoginInfo, AdNetwork, AdNetworkScrapeStats


def network_scraping_mptest():
    # Set up default models
    account = Account()
    account.put()
    
    nc = {}
    nc['username'] = 'njamal@stanford.edu'
    nc['password'] = 'xckjhfn3xprkxksm'
    nc['client_key'] = 'k907a03ee39cecb699b5ad45c5eded01'
    nc['app_name_dict'] = {}
    for i, site_id in enumerate(['a14a9ed9bf1fdcd', 'a14a7143850a745', 'a14a71435d8d5b3',
                                 'a14a7142ee96329', 'a14a7142acad145', 'a14a6e18d6610af', 
                                 'a14a6b5458b0447', 'a1497a459250ea5', 'a14970f6ad53c3c']):
        nc['app_name_dict'][site_id] = 'test%d' % i
    nc['network'] = 'admob'
    nc = json.dumps(nc)
    admob_login_info = AdNetworkLoginInfo(account=account, ad_network='admob', dictionary=nc)
    
    nc = {}
    nc['username'] = 'vrubba'
    nc['password'] = 'fluik123!'
    nc['network'] = 'jumptap'
    nc = json.dumps(nc)
    jumptap_login_info = AdNetworkLoginInfo(account=account, ad_network='jumptap', dictionary=nc)
    
    admob_login_info.put()
    jumptap_login_info.put()

    app = App(account=account, name="Test App")
    app.put()
    
    jumptap_network = AdNetwork(application=app, ad_network='admob')
    admob_network = AdNetwork(application=app, ad_network='jumptap')
    jumptap_network.put()
    admob_network.put()
    
    update_ad_networks()
