import sys
import os
import logging
import datetime

sys.path.append(os.environ['PWD'])

from google.appengine.ext import db
from google.appengine.api import users
from nose.tools import assert_equals, assert_not_equals, assert_true, assert_false

from advertiser.models import *
from publisher.models import *
from reporting.aws_logging import stats_updater
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from test_utils import add_lists, prepend_list, clear_datastore, debug_key_name

AdUnit = Site


def offline_os_rollup_mptest(): 
    # make sure we start unit test with clean slate
    clear_datastore()
    
    # create and put model objects 
    user = users.User(email="test@example.com")
    account = Account(key_name="account",user=user).put()

    app = App(key_name='app1', name='App',account=account).put()
    adunit1 = AdUnit(key_name='adunit1', app_key=app, account=account).put()

    campaign = Campaign(key_name='campaign', name='campaign',account=account, u=user).put()
    adgroup = AdGroup(key_name='adgroup', campaign=campaign,account=account).put()
    creative1 = Creative(key_name='creative1', ad_group=adgroup,account=account).put()
   
    # get encoded strings of keys
    adunit_id1 = str(adunit1)
    app_id = str(app)
    creative_id1 = str(creative1)
    adgroup_id = str(adgroup)
    campaign_id = str(campaign)

    # mapping from key to encoded strings; used for debugging messages
    id_dict = {adunit_id1: 'adunit_id1',
               app_id: 'app_id',
               creative_id1: 'creative_id1',
               adgroup_id: 'adgroup_id',
               campaign_id: 'campaign_id',
               '': '',
               'k': 'k'}
           
    hour = datetime.datetime(2011, 03, 21, 01)
    day = datetime.datetime(2011, 03, 21)

    # Android 1.6
    android_16_hour = [47, 16, 8, 1]
    android_16_req_hour = [40, 0, 0, 0]

    # Android 2.2
    android_22_hour = [58, 18, 12, 3]
    android_22_req_hour = [50, 0, 0, 0]
    
    # iPhone OS 4.3
    iphone_43_hour = [70, 30, 10, 3]
    iphone_43_req_hour = [30, 0, 0, 0]

    # day 
    android_16_day = android_16_hour
    android_16_req_day = android_16_req_hour
    android_22_day = android_22_hour
    android_22_req_day = android_22_req_hour
    iphone_43_day = iphone_43_hour
    iphone_43_req_day = iphone_43_req_hour
    
    
    obj_dict = {
    ###########################
    #### DATE_HOUR ROLLUPS ####
    ###########################

    ### ADUNITS ###
    # Adunit-Creative
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # Adunit-AdGroup
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # Adunit-Campaign
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # Adunit-*
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0], add_lists([android_16_hour, android_22_hour])[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'iPhone_OS', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0]+iphone_43_req_hour[0], add_lists([android_16_hour, android_22_hour, iphone_43_hour])[1:]),
                
    
    #### Apps ####
    # App-Creative
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(app_id, creative_id1, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # App-AdGroup
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(app_id, adgroup_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # App-Campaign
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%(app_id, campaign_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # App-*
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0], add_lists([android_16_hour, android_22_hour])[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'iPhone_OS', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s:%s'%(app_id, '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0]+iphone_43_req_hour[0], add_lists([android_16_hour, android_22_hour, iphone_43_hour])[1:]),
        
    ### * ###
    # *-Creative
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%('', creative_id1, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # *-AdGroup
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%('', adgroup_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # *-Campaign
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '', hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour]),
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '1.6', hour.strftime('%y%m%d%H')): android_16_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '2.2', hour.strftime('%y%m%d%H')): android_22_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '4.3', hour.strftime('%y%m%d%H')): iphone_43_hour,
    'k:%s:%s:%s'%('', campaign_id, hour.strftime('%y%m%d%H')): add_lists([android_16_hour, android_22_hour, iphone_43_hour]),
    
    # *-*
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0], add_lists([android_16_hour, android_22_hour])[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '1.6', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0], android_16_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '2.2', hour.strftime('%y%m%d%H')): prepend_list(android_22_req_hour[0], android_22_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'iPhone_OS', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '4.3', hour.strftime('%y%m%d%H')): prepend_list(iphone_43_req_hour[0], iphone_43_hour[1:]),
    'k:%s:%s:%s'%('', '', hour.strftime('%y%m%d%H')): prepend_list(android_16_req_hour[0]+android_22_req_hour[0]+iphone_43_req_hour[0], add_lists([android_16_hour, android_22_hour, iphone_43_hour])[1:]),


    ####################
    ### Date Rollups ###
    ####################

    ### ADUNITS ###
    # Adunit-Creative
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, creative_id1, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # Adunit-AdGroup
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, adgroup_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # Adunit-Campaign
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, campaign_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # Adunit-*
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'Android', '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0], add_lists([android_16_day, android_22_day])[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', 'iPhone_OS', '', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(adunit_id1, '', '', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0]+iphone_43_req_day[0], add_lists([android_16_day, android_22_day, iphone_43_day])[1:]),
                
    
    #### Apps ####
    # App-Creative
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_hour, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, creative_id1, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(app_id, creative_id1, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # App-AdGroup
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, adgroup_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(app_id, adgroup_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # App-Campaign
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%(app_id, campaign_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%(app_id, campaign_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # App-*
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'Android', '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0], add_lists([android_16_day, android_22_day])[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', 'iPhone_OS', '', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%(app_id, '', '', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s:%s'%(app_id, '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0]+iphone_43_req_day[0], add_lists([android_16_day, android_22_day, iphone_43_day])[1:]),
        
    ### * ###
    # *-Creative
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', creative_id1, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%('', creative_id1, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # *-AdGroup
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', adgroup_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%('', adgroup_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # *-Campaign
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'Android', '', hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day]),
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '1.6', hour.strftime('%y%m%d')): android_16_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '2.2', hour.strftime('%y%m%d')): android_22_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, 'iPhone_OS', '', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s::::%s:%s:%s'%('', campaign_id, '', '4.3', hour.strftime('%y%m%d')): iphone_43_day,
    'k:%s:%s:%s'%('', campaign_id, hour.strftime('%y%m%d')): add_lists([android_16_day, android_22_day, iphone_43_day]),
    
    # *-*
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'Android', '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0], add_lists([android_16_day, android_22_day])[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '1.6', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0], android_16_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '2.2', hour.strftime('%y%m%d')): prepend_list(android_22_req_day[0], android_22_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'iPhone_OS', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', 'iPhone_OS', '', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s::::%s:%s:%s'%('', '', '', '4.3', hour.strftime('%y%m%d')): prepend_list(iphone_43_req_day[0], iphone_43_day[1:]),
    'k:%s:%s:%s'%('', '', hour.strftime('%y%m%d')): prepend_list(android_16_req_day[0]+android_22_req_day[0]+iphone_43_req_day[0], add_lists([android_16_day, android_22_day, iphone_43_day])[1:]),
    }
    
    # verify there's no StatsModels in datastore yet
    assert_equals(StatsModel.all().count(), 0)
            
    # hour             
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=android_16_hour, date_hour=hour, device_os='Android', device_os_version='1.6'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=android_22_hour, date_hour=hour, device_os='Android', device_os_version='2.2'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=iphone_43_hour, date_hour=hour, device_os='iPhone_OS', device_os_version='4.3'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=android_16_req_hour, date_hour=hour, device_os='Android', device_os_version='1.6'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=android_22_req_hour, date_hour=hour, device_os='Android', device_os_version='2.2'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=iphone_43_req_hour, date_hour=hour, device_os='iPhone_OS', device_os_version='4.3'))
       
    # day
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=android_16_day, date=day, device_os='Android', device_os_version='1.6'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=android_22_day, date=day, device_os='Android', device_os_version='2.2'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=iphone_43_day, date=day, device_os='iPhone_OS', device_os_version='4.3'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=android_16_req_day, date=day, device_os='Android', device_os_version='1.6'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=android_22_req_day, date=day, device_os='Android', device_os_version='2.2'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=iphone_43_req_day, date=day, device_os='iPhone_OS', device_os_version='4.3'))

    stats_updater.put_models() 
                        
    assert_equals(App.all().count(), 1)
    assert_equals(Campaign.all().count(), 1)
    assert_equals(AdGroup.all().count(), 1)
    assert_equals(AdUnit.all().count(), 1)
    assert_equals(Creative.all().count(), 1)

    assert_equals(len(obj_dict)+1, StatsModel.all().count())            

    for stats in StatsModel.all():
        key_name = stats.key().name()
        if len(key_name.split(':')) == 2: continue # skip the account 
        assert_equals(obj_dict[key_name], [stats.request_count, stats.impression_count, stats.click_count, stats.conversion_count])

