import os, sys
sys.path.append(os.environ['PWD'])

# magic test import
import common.utils.test.setup

from account.models import Account, NetworkConfig
from publisher.models import App

from network_scraping.adnetwork_update import *
from network_scraping.models import *

TEST_JUMPTAP_PUB_ID = '12345'
TEST_ADMOB_PUB_ID = 'a14a9ed9bf1fdcd'

def network_scraping_mptest():
    # Set up default models
    account = Account()
    account.put()
    
    # AdMob login info
    # nc['app_name_dict'] = {}
    # for i, site_id in enumerate(['a14a9ed9bf1fdcd', 'a14a7143850a745', 'a14a71435d8d5b3',
    #                              'a14a7142ee96329', 'a14a7142acad145', 'a14a6e18d6610af', 
    #                              'a14a6b5458b0447', 'a1497a459250ea5', 'a14970f6ad53c3c']):
    #     nc['app_name_dict'][site_id] = 'test%d' % i
    admob_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'admob', username = 'njamal@stanford.edu',
                                          password = 'xckjhfn3xprkxksm', client_key = 'k907a03ee39cecb699b5ad45c5eded01')
    
    # JumpTap login info
    jumptap_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'jumptap', username = 'vrubba',
                                            password = 'fluik123!')
    
    admob_login_info.put()
    jumptap_login_info.put()

    network_config = NetworkConfig(jumptap_pub_id = TEST_JUMPTAP_PUB_ID, admob_pub_id = TEST_ADMOB_PUB_ID)
    network_config.put()
    
    # name corresponds to jumptap login info
    app = App(account = account, name = "Office Jerk", network_config = network_config)
    app.put()
    
    jumptap_network = AdNetworkAppMapper(application = app, ad_network_name = 'admob', publisher_id = TEST_ADMOB_PUB_ID, ad_network_login = admob_login_info,
                                         attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0)
    admob_network = AdNetworkAppMapper(application = app, ad_network_name = 'jumptap', publisher_id = TEST_JUMPTAP_PUB_ID, ad_network_login = jumptap_login_info,
                                       attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0)
    jumptap_network.put()
    admob_network.put()
    
    update_ad_networks()
