import os, sys
sys.path.append(os.environ['PWD'])

# magic test import
import common.utils.test.setup

from google.appengine.ext import db
# from google.appengine.ext import testbed

from datetime import date, timedelta
from sets import Set

from account.models import Account, NetworkConfig
from publisher.models import App

from network_scraping.adnetwork_update import *
from network_scraping.models import *

TEST_JUMPTAP_PUB_ID = '12345'
TEST_ADMOB_PUB_ID = 'a14a9ed9bf1fdcd'
TEST_IAD_PUB_ID = '362641118' # NOT IN NetworkConfig
TEST_INMOBI_PUB_ID ='4028cb962b75ff06012b792fc5fb0045'
TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

def network_scraping_mptest():
    # First, create # an instance of the Testbed class.
    #     tstbd = testbed.Testbed()
    #     # Then activate the testbed, which prepares the service stubs for use.
    #     tstbd.activate()
    #     # Next, declare which service stubs you want to use.
    #     tstbd.init_datastore_v3_stub()
    
    ''' Set up the default models '''
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
    admob_login_info.put()
    
    # JumpTap login info
    jumptap_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'jumptap', username = 'vrubba',
                                            password = 'fluik123!')
    jumptap_login_info.put()
    
    # iAd login info                                        
    iad_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'iad', username = 'rawrmaan@me.com',
                                           password = '606mCV&#dS')
    iad_login_info.put()
    
    # InMobi login info
    inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = '4028cb8b2b617f70012b792fe65e00a2',
                                        password = '84585161')
    inmobi_login_info.put()
    # MobFox login info
    mobfox_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'mobfox', publisher_ids = ['fb8b314d6e62912617e81e0f7078b47e'])
    mobfox_login_info.put()
    
    # Only needed for jumptap
    network_config = NetworkConfig(jumptap_pub_id = TEST_JUMPTAP_PUB_ID)
    network_config.put()
    
    # name corresponds to jumptap login info
    app = App(account = account, name = "Office Jerk", network_config = network_config)
    app.put()
    
    network_app_mappers = []
    network_app_mappers.append(AdNetworkAppMapper(application = app, ad_network_name = 'admob', publisher_id = TEST_ADMOB_PUB_ID, ad_network_login = admob_login_info,
                                         attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0))
    network_app_mappers.append(AdNetworkAppMapper(application = app, ad_network_name = 'jumptap', publisher_id = TEST_JUMPTAP_PUB_ID, ad_network_login = jumptap_login_info,
                                       attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0))
    network_app_mappers.append(AdNetworkAppMapper(application = app, ad_network_name = 'iad', publisher_id = TEST_IAD_PUB_ID, ad_network_login = iad_login_info,
                                       attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0))
    network_app_mappers.append(AdNetworkAppMapper(application = app, ad_network_name = 'inmobi', publisher_id = TEST_INMOBI_PUB_ID, ad_network_login = inmobi_login_info,
                                       attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0))
    network_app_mappers.append(AdNetworkAppMapper(application = app, ad_network_name = 'mobfox', publisher_id = TEST_MOBFOX_PUB_ID, ad_network_login = mobfox_login_info,
                                       attempts = 0, impressions = 0, fill_rate = 0.0, clicks = 0, ctr = 0.0, ecpm = 0.0))
    db.put(network_app_mappers)
    
    ''' Call the method we are testing '''
    update_ad_networks()
    
    ''' Verify results '''
    test_network_app_mappers = get_ad_network_totals(account)
    
    # Was a day created for each app for the account?
    yesterday = date.today() - timedelta(days = 1)
    for n in test_network_app_mappers:
        stats = get_ad_network_app_stats(n)
        assert stats[0].date == yesterday
