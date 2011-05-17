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


def offline_device_rollup_mptest(): 
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

    # Apple iPhone
    iphone_hour = [51, 16, 0, 0]
    iphone_req_hour = [40, 0, 0, 0]

    # Apple iPad
    ipad_hour = [65, 18, 12, 3]
    ipad_req_hour = [50, 0, 0, 0]
    
    # day 
    iphone_day = iphone_hour
    iphone_req_day = iphone_req_hour
    ipad_day = ipad_hour
    ipad_req_day = ipad_req_hour
    
    
    obj_dict = {
    ###########################
    #### DATE_HOUR ROLLUPS ####
    ###########################

    ### ADUNITS ###
    # Adunit-Creative
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
        
    # Adunit-AdGroup
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # Adunit-Campaign
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # Adunit-*
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', '', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', '', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),
            
    
    #### Apps ####
    # App-Creative
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(app_id, creative_id1, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
        
    # App-AdGroup
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(app_id, adgroup_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # App-Campaign
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%(app_id, campaign_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # App-*
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', '', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', '', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s:%s'%(app_id, '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),
        
    ### * ###
    # *-Creative
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%('', creative_id1, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # *-AdGroup
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%('', adgroup_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # *-Campaign
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', '', hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, '', 'iPhone', hour.strftime('%y%m%d%H')): iphone_hour,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, '', 'iPad', hour.strftime('%y%m%d%H')): ipad_hour,
    'k:%s:%s:%s'%('', campaign_id, hour.strftime('%y%m%d%H')): add_lists([iphone_hour, ipad_hour]),
    
    # *-*
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', '', 'iPhone', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0], iphone_hour[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', '', 'iPad', hour.strftime('%y%m%d%H')): prepend_list(ipad_req_hour[0], ipad_hour[1:]),
    'k:%s:%s:%s'%('', '', hour.strftime('%y%m%d%H')): prepend_list(iphone_req_hour[0]+ipad_req_hour[0], add_lists([iphone_hour, ipad_hour])[1:]),


    ####################
    ### Date Rollups ###
    ####################

    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, creative_id1, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
        
    # Adunit-AdGroup
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, adgroup_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # Adunit-Campaign
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, campaign_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # Adunit-*
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', 'Apple', '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', '', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(adunit_id1, '', '', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),
    
    
    #### Apps ####
    # App-Creative
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, creative_id1, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(app_id, creative_id1, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
        
    # App-AdGroup
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, adgroup_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(app_id, adgroup_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # App-Campaign
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%(app_id, campaign_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%(app_id, campaign_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # App-*
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', 'Apple', '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', '', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%(app_id, '', '', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s:%s'%(app_id, '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),

    ### * ###
    # *-Creative
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', creative_id1, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%('', creative_id1, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # *-AdGroup
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', adgroup_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%('', adgroup_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # *-Campaign
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, 'Apple', '', day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, '', 'iPhone', day.strftime('%y%m%d')): iphone_day,
    'k:%s:%s::%s:%s:::%s'%('', campaign_id, '', 'iPad', day.strftime('%y%m%d')): ipad_day,
    'k:%s:%s:%s'%('', campaign_id, day.strftime('%y%m%d')): add_lists([iphone_day, ipad_day]),
    
    # *-*
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', 'Apple', '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', '', 'iPhone', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0], iphone_day[1:]),
    'k:%s:%s::%s:%s:::%s'%('', '', '', 'iPad', day.strftime('%y%m%d')): prepend_list(ipad_req_day[0], ipad_day[1:]),
    'k:%s:%s:%s'%('', '', day.strftime('%y%m%d')): prepend_list(iphone_req_day[0]+ipad_req_day[0], add_lists([iphone_day, ipad_day])[1:]),
    }
    
    # verify there's no StatsModels in datastore yet
    assert_equals(StatsModel.all().count(), 0)
            
    # hour             
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=iphone_hour, date_hour=hour, brand_name='Apple', marketing_name='iPhone'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=ipad_hour, date_hour=hour, brand_name='Apple', marketing_name='iPad'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=iphone_req_hour, date_hour=hour, brand_name='Apple', marketing_name='iPhone'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=ipad_req_hour, date_hour=hour, brand_name='Apple', marketing_name='iPad'))
       
    # day
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=iphone_day, date=day, brand_name='Apple', marketing_name='iPhone'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=ipad_day, date=day, brand_name='Apple', marketing_name='iPad'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=iphone_req_day, date=day, brand_name='Apple', marketing_name='iPhone'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=ipad_req_day, date=day, brand_name='Apple', marketing_name='iPad'))

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

