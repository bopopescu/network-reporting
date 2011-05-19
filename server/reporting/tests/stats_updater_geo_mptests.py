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


def offline_geo_rollup_mptest(): 
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
           
    # date_hours: first and last hours of pi day
    hour1 = datetime.datetime(2011, 03, 21, 01)
    hour2 = datetime.datetime(2011, 03, 21, 23)
    day = datetime.datetime(2011, 03, 21)

    # hour1
    us_hour1 = [48, 16, 0, 0]
    gb_hour1 = [61, 18, 12, 3]
    us_req_hour1 = [40, 0, 0, 0]
    gb_req_hour1 = [50, 0, 0, 0]
    
    # hour2
    us_hour2 = [52, 5, 2, 1]
    gb_hour2 = [63, 34, 10, 6]
    us_req_hour2 = [31, 0, 0, 0]
    gb_req_hour2 = [49, 0, 0, 0]
    
    # day 
    us_day = add_lists([us_hour1, us_hour2])
    gb_day = add_lists([gb_hour1, gb_hour2])
    us_req_day = add_lists([us_req_hour1, us_req_hour2])
    gb_req_day = add_lists([gb_req_hour1, gb_req_hour2])
    
    
    obj_dict = {
    ###########################
    #### DATE_HOUR ROLLUPS ####
    ###########################

    ### ADUNITS ###
    # Adunit-Creative-country-hour1
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),

    # Adunit-Creative-country-hour2
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # Adunit-AdGroup-country-hour1
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),

    # Adunit-AdGroup-country-hour2
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # Adunit-Campaign-country-hour1
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # Adunit-Campaign-country-hour2
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),

    # Adunit Totals for hour1
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'US', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0], us_hour1[1:]),
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'GB', hour1.strftime('%y%m%d%H')): prepend_list(gb_req_hour1[0], gb_hour1[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0]+gb_req_hour1[0], add_lists([us_hour1, gb_hour1])[1:]),
    
    # Adunit Totals for hour2
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'US', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0], us_hour2[1:]),
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'GB', hour2.strftime('%y%m%d%H')): prepend_list(gb_req_hour2[0], gb_hour2[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0]+gb_req_hour2[0], add_lists([us_hour2, gb_hour2])[1:]),
    
    #### Apps ####
    # App-Creative-country-hour1
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(app_id, creative_id1, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),    

    # App-Creative-country-hour2
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(app_id, creative_id1, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # App-AdGroup-country-hour1
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(app_id, adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # App-AdGroup-country-hour2
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(app_id, adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # App-Campaign-country-hour1
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%(app_id, campaign_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # App-Campaign-country-hour2
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%(app_id, campaign_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # App Total for hour1
    'k:%s:%s:%s:::::%s'%(app_id, '', 'US', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0], us_hour1[1:]),
    'k:%s:%s:%s:::::%s'%(app_id, '', 'GB', hour1.strftime('%y%m%d%H')): prepend_list(gb_req_hour1[0], gb_hour1[1:]),
    'k:%s:%s:%s'%(app_id, '', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0]+gb_req_hour1[0], add_lists([us_hour1, gb_hour1])[1:]),

    # App Totals for hour2
    'k:%s:%s:%s:::::%s'%(app_id, '', 'US', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0], us_hour2[1:]),
    'k:%s:%s:%s:::::%s'%(app_id, '', 'GB', hour2.strftime('%y%m%d%H')): prepend_list(gb_req_hour2[0], gb_hour2[1:]),
    'k:%s:%s:%s'%(app_id, '', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0]+gb_req_hour2[0], add_lists([us_hour2, gb_hour2])[1:]),
    
    ### * ###
    # *-Creative-country-hour1
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%('', creative_id1, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # *-Creative-country-hour2
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%('', creative_id1, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),
    
    # *-AdGroup-country_hour1
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%('', adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # *-AdGroup-country-hour2
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%('', adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),

    # *-Campaign-country_hour1
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'US', hour1.strftime('%y%m%d%H')): us_hour1,
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'GB', hour1.strftime('%y%m%d%H')): gb_hour1,
    'k:%s:%s:%s'%('', campaign_id, hour1.strftime('%y%m%d%H')): add_lists([us_hour1, gb_hour1]),
    
    # *-Campaign-country-hour2
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'US', hour2.strftime('%y%m%d%H')): us_hour2,
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'GB', hour2.strftime('%y%m%d%H')): gb_hour2,
    'k:%s:%s:%s'%('', campaign_id, hour2.strftime('%y%m%d%H')): add_lists([us_hour2, gb_hour2]),

    # *-*-country-hour1
    'k:%s:%s:%s:::::%s'%('', '', 'US', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0], us_hour1[1:]),
    'k:%s:%s:%s:::::%s'%('', '', 'GB', hour1.strftime('%y%m%d%H')): prepend_list(gb_req_hour1[0], gb_hour1[1:]),
    'k:%s:%s:%s'%('', '', hour1.strftime('%y%m%d%H')): prepend_list(us_req_hour1[0]+gb_req_hour1[0], add_lists([us_hour1, gb_hour1])[1:]),
    
    # *-*-country-hour2
    'k:%s:%s:%s:::::%s'%('', '', 'US', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0], us_hour2[1:]),
    'k:%s:%s:%s:::::%s'%('', '', 'GB', hour2.strftime('%y%m%d%H')): prepend_list(gb_req_hour2[0], gb_hour2[1:]),
    'k:%s:%s:%s'%('', '', hour2.strftime('%y%m%d%H')): prepend_list(us_req_hour2[0]+gb_req_hour2[0], add_lists([us_hour2, gb_hour2])[1:]),


    ####################
    ### Date Rollups ###
    ####################

    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(adunit_id1, creative_id1, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(adunit_id1, creative_id1, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # Adunit-AdGroup
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(adunit_id1, adgroup_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # Adunit-Campaign
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(adunit_id1, campaign_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(adunit_id1, campaign_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # Adunit Totals 
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'US', day.strftime('%y%m%d')): prepend_list(us_req_day[0], us_day[1:]),
    'k:%s:%s:%s:::::%s'%(adunit_id1, '', 'GB', day.strftime('%y%m%d')): prepend_list(gb_req_day[0], gb_day[1:]),
    'k:%s:%s:%s'%(adunit_id1, '', day.strftime('%y%m%d')): prepend_list(us_req_day[0]+gb_req_day[0], add_lists([us_day, gb_day])[1:]),
    
    #### Apps ####
    # App-Creative
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(app_id, creative_id1, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(app_id, creative_id1, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # App-AdGroup
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(app_id, adgroup_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(app_id, adgroup_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # App-Campaign
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'US', day.strftime('%y%m%d')): us_day,
    'k:%s:%s:%s:::::%s'%(app_id, campaign_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%(app_id, campaign_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # App Totals 
    'k:%s:%s:%s:::::%s'%(app_id, '', 'US', day.strftime('%y%m%d')): prepend_list(us_req_day[0], us_day[1:]),
    'k:%s:%s:%s:::::%s'%(app_id, '', 'GB', day.strftime('%y%m%d')): prepend_list(gb_req_day[0], gb_day[1:]),
    'k:%s:%s:%s'%(app_id, '', day.strftime('%y%m%d')): prepend_list(us_req_day[0]+gb_req_day[0], add_lists([us_day, gb_day])[1:]),

    ### * ###
    # *-Creative
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'US', day.strftime('%y%m%d')): us_day, 
    'k:%s:%s:%s:::::%s'%('', creative_id1, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%('', creative_id1, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),
    
    # *-AdGroup
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'US', day.strftime('%y%m%d')): us_day, 
    'k:%s:%s:%s:::::%s'%('', adgroup_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%('', adgroup_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # *-Campaign
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'US', day.strftime('%y%m%d')): us_day, 
    'k:%s:%s:%s:::::%s'%('', campaign_id, 'GB', day.strftime('%y%m%d')): gb_day,
    'k:%s:%s:%s'%('', campaign_id, day.strftime('%y%m%d')): add_lists([us_day, gb_day]),

    # *-*
    'k:%s:%s:%s:::::%s'%('', '', 'US', day.strftime('%y%m%d')): prepend_list(us_req_day[0], us_day[1:]),
    'k:%s:%s:%s:::::%s'%('', '', 'GB', day.strftime('%y%m%d')): prepend_list(gb_req_day[0], gb_day[1:]),
    'k:%s:%s:%s'%('', '', day.strftime('%y%m%d')): prepend_list(us_req_day[0]+gb_req_day[0], add_lists([us_day, gb_day])[1:]),
    }
    
    
    # verify there's no StatsModels in datastore yet
    assert_equals(StatsModel.all().count(), 0)
            
    # hour1             
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=us_hour1, date_hour=hour1, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=gb_hour1, date_hour=hour1, country_code='GB'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=us_req_hour1, date_hour=hour1, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=gb_req_hour1, date_hour=hour1, country_code='GB'))
       
    # hour2
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=us_hour2, date_hour=hour2, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=gb_hour2, date_hour=hour2, country_code='GB'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=us_req_hour2, date_hour=hour2, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=gb_req_hour2, date_hour=hour2, country_code='GB'))

    # day
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=us_day, date=day, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=gb_day, date=day, country_code='GB'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=us_req_day, date=day, country_code='US'))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=gb_req_day, date=day, country_code='GB'))

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

        