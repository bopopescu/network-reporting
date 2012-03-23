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

from common.utils.test.test_utils import add_lists, prepend_list, clear_datastore, debug_key_name, debug_helper

AdUnit = Site


def offline_rollup_mptest():
    # make sure we start unit test with clean slate
    clear_datastore()
    
    # create and put model objects 
    user = users.User(email="test@example.com")
    account = Account(key_name="account",user=user).put()

    app = App(key_name='app1', name='App',account=account).put()
    adunit1 = AdUnit(key_name='adunit1', app_key=app, account=account).put()
    adunit2 = AdUnit(key_name='adunit2', app_key=app, account=account).put()

    campaign = Campaign(key_name='campaign', name='campaign',account=account, u=user).put()
    adgroup = AdGroup(key_name='adgroup', campaign=campaign,account=account).put()
    creative1 = Creative(key_name='creative1', ad_group=adgroup,account=account).put()
    creative2 = Creative(key_name='creative2', ad_group=adgroup,account=account).put()
   
    # get encoded strings of keys
    adunit_id1 = str(adunit1)
    adunit_id2 = str(adunit2)
    app_id = str(app)
    creative_id1 = str(creative1)
    creative_id2 = str(creative2)
    adgroup_id = str(adgroup)
    campaign_id = str(campaign)

    # mapping from key to encoded strings; used for debugging messages
    id_dict = {adunit_id1: 'adunit_id1',
               adunit_id2: 'adunit_id2',
               app_id: 'app_id',
               creative_id1: 'creative_id1',
               creative_id2: 'creative_id2',
               adgroup_id: 'adgroup_id',
               campaign_id: 'campaign_id',
               '': '',
               'k': 'k'}
           

    # date_hours: first and last hours of pi day
    hour1 = datetime.datetime(2011, 03, 21, 01)
    hour2 = datetime.datetime(2011, 03, 21, 23)
    day = datetime.datetime(2011, 03, 21)

    # date_hour count lists
    a1_c1_hour1 = [28, 16, 0, 0]
    a1_c2_hour1 = [31, 18, 12, 3]
    a2_c1_hour1 = [16, 5, 2, 1]
    a2_c2_hour1 = [47, 34, 10, 6]
    a1_hour1 = [40, 0, 0, 0]
    a2_hour1 = [50, 0, 0, 0]

    a1_c1_hour2 = [26, 10, 0, 0]
    a1_c2_hour2 = [22, 12, 5, 0]
    a2_c1_hour2 = [0, 4, 1, 0]
    a2_c2_hour2 = [70, 30, 10, 3]
    a1_hour2 = [31, 0, 0, 0]
    a2_hour2 = [49, 0, 0, 0]

    # date count lists
    a1_c1_day = add_lists([a1_c1_hour1, a1_c1_hour2])
    a1_c2_day = add_lists([a1_c2_hour1, a1_c2_hour2])
    a2_c1_day = add_lists([a2_c1_hour1, a2_c1_hour2])
    a2_c2_day = add_lists([a2_c2_hour1, a2_c2_hour2])
    a1_day = add_lists([a1_hour1, a1_hour2])
    a2_day = add_lists([a2_hour1, a2_hour2])



    obj_dict = {
    ###########################
    #### DATE_HOUR ROLLUPS ####
    ###########################


    ### ADUNITS ###
    # Adunit-Creative-hour1
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour1.strftime('%y%m%d%H')): a1_c1_hour1,
    'k:%s:%s:%s'%(adunit_id1, creative_id2, hour1.strftime('%y%m%d%H')): a1_c2_hour1,
    'k:%s:%s:%s'%(adunit_id2, creative_id1, hour1.strftime('%y%m%d%H')): a2_c1_hour1,
    'k:%s:%s:%s'%(adunit_id2, creative_id2, hour1.strftime('%y%m%d%H')): a2_c2_hour1,

    # Adunit-Creative-hour2
    'k:%s:%s:%s'%(adunit_id1, creative_id1, hour2.strftime('%y%m%d%H')): a1_c1_hour2,
    'k:%s:%s:%s'%(adunit_id1, creative_id2, hour2.strftime('%y%m%d%H')): a1_c2_hour2,
    'k:%s:%s:%s'%(adunit_id2, creative_id1, hour2.strftime('%y%m%d%H')): a2_c1_hour2,
    'k:%s:%s:%s'%(adunit_id2, creative_id2, hour2.strftime('%y%m%d%H')): a2_c2_hour2,

    # Adunit-AdGroup-hour1
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1]),
    'k:%s:%s:%s'%(adunit_id2, adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([a2_c1_hour1, a2_c2_hour1]),

    # Adunit-AdGroup-hour2
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2]),
    'k:%s:%s:%s'%(adunit_id2, adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([a2_c1_hour2, a2_c2_hour2]),

    # Adunit-Campaign-hour1
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1]),
    'k:%s:%s:%s'%(adunit_id2, campaign_id, hour1.strftime('%y%m%d%H')): add_lists([a2_c1_hour1, a2_c2_hour1]),

    # Adunit-Campaign-hour2
    'k:%s:%s:%s'%(adunit_id1, campaign_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2]),
    'k:%s:%s:%s'%(adunit_id2, campaign_id, hour2.strftime('%y%m%d%H')): add_lists([a2_c1_hour2, a2_c2_hour2]),

    # Adunit Totals for hour1
    'k:%s:%s:%s'%(adunit_id1,'',hour1.strftime('%y%m%d%H')): prepend_list(a1_hour1[0], add_lists([a1_c1_hour1, a1_c2_hour1])[1:]),
    'k:%s:%s:%s'%(adunit_id2,'',hour1.strftime('%y%m%d%H')): prepend_list(a2_hour1[0], add_lists([a2_c1_hour1, a2_c2_hour1])[1:]),

    # Adunit Totals for hour2
    'k:%s:%s:%s'%(adunit_id1,'',hour2.strftime('%y%m%d%H')): prepend_list(a1_hour2[0], add_lists([a1_c1_hour2, a1_c2_hour2])[1:]),
    'k:%s:%s:%s'%(adunit_id2,'',hour2.strftime('%y%m%d%H')): prepend_list(a2_hour2[0], add_lists([a2_c1_hour2, a2_c2_hour2])[1:]),

    #### Apps ####
    # App-Creative-hour1
    'k:%s:%s:%s'%(app_id, creative_id1, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a2_c1_hour1]),
    'k:%s:%s:%s'%(app_id, creative_id2, hour1.strftime('%y%m%d%H')): add_lists([a1_c2_hour1, a2_c2_hour1]),

    # App-Creative-hour2
    'k:%s:%s:%s'%(app_id, creative_id1, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a2_c1_hour2]),
    'k:%s:%s:%s'%(app_id, creative_id2, hour2.strftime('%y%m%d%H')): add_lists([a1_c2_hour2, a2_c2_hour2]),

    # App-AdGroup-hour1
    'k:%s:%s:%s'%(app_id, adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1]),

    # App-AdGroup-hour2
    'k:%s:%s:%s'%(app_id, adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2]),

    # App-Campaign-hour1
    'k:%s:%s:%s'%(app_id, campaign_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1]),

    # App-Campaign-hour2
    'k:%s:%s:%s'%(app_id, campaign_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2]),

    # App-Total-hour1
    'k:%s:%s:%s'%(app_id, '', hour1.strftime('%y%m%d%H')): prepend_list(a1_hour1[0]+a2_hour1[0], add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1])[1:]),

    # App-Total-hour2
    'k:%s:%s:%s'%(app_id, '', hour2.strftime('%y%m%d%H')): prepend_list(a1_hour2[0]+a2_hour2[0], add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2])[1:]),

    ### * ###
    # *-Creative-hour1
    'k:%s:%s:%s'%('', creative_id1, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a2_c1_hour1]),
    'k:%s:%s:%s'%('', creative_id2, hour1.strftime('%y%m%d%H')): add_lists([a1_c2_hour1, a2_c2_hour1]),

    # *-Creative-hour2
    'k:%s:%s:%s'%('', creative_id1, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a2_c1_hour2]),
    'k:%s:%s:%s'%('', creative_id2, hour2.strftime('%y%m%d%H')): add_lists([a1_c2_hour2, a2_c2_hour2]),

    # *-AdGroup-hour1
    'k:%s:%s:%s'%('', adgroup_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1]),

    # *-AdGroup-hour2
    'k:%s:%s:%s'%('', adgroup_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2]),

    # *-Campaign-hour1
    'k:%s:%s:%s'%('', campaign_id, hour1.strftime('%y%m%d%H')): add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1]),

    # *-Campaign-hour2
    'k:%s:%s:%s'%('', campaign_id, hour2.strftime('%y%m%d%H')): add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2]),

    # *-*-hour1
    'k:%s:%s:%s'%('', '', hour1.strftime('%y%m%d%H')): prepend_list(a1_hour1[0]+a2_hour1[0], add_lists([a1_c1_hour1, a1_c2_hour1, a2_c1_hour1, a2_c2_hour1])[1:]),

    # *-*-hour2
    'k:%s:%s:%s'%('', '', hour2.strftime('%y%m%d%H')): prepend_list(a1_hour2[0]+a2_hour2[0], add_lists([a1_c1_hour2, a1_c2_hour2, a2_c1_hour2, a2_c2_hour2])[1:]),


    ####################
    ### Date Rollups ###
    ####################

    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s:%s'%(adunit_id1, creative_id1, day.strftime('%y%m%d')): a1_c1_day,
    'k:%s:%s:%s'%(adunit_id1, creative_id2, day.strftime('%y%m%d')): a1_c2_day,
    'k:%s:%s:%s'%(adunit_id2, creative_id1, day.strftime('%y%m%d')): a2_c1_day,
    'k:%s:%s:%s'%(adunit_id2, creative_id2, day.strftime('%y%m%d')): a2_c2_day,

    # Adunit-AdGroup
    'k:%s:%s:%s'%(adunit_id1, adgroup_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day]),
    'k:%s:%s:%s'%(adunit_id2, adgroup_id, day.strftime('%y%m%d')): add_lists([a2_c1_day, a2_c2_day]),

    # Adunit-Campaign
    'k:%s:%s:%s'%(adunit_id1, campaign_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day]),
    'k:%s:%s:%s'%(adunit_id2, campaign_id, day.strftime('%y%m%d')): add_lists([a2_c1_day, a2_c2_day]),

    # Adunit Totals 
    'k:%s:%s:%s'%(adunit_id1, '', day.strftime('%y%m%d')): prepend_list(a1_day[0], add_lists([a1_c1_day, a1_c2_day])[1:]),
    'k:%s:%s:%s'%(adunit_id2, '', day.strftime('%y%m%d')): prepend_list(a2_day[0], add_lists([a2_c1_day, a2_c2_day])[1:]),

    #### Apps ####
    # App-Creative
    'k:%s:%s:%s'%(app_id, creative_id1, day.strftime('%y%m%d')): add_lists([a1_c1_day, a2_c1_day]),
    'k:%s:%s:%s'%(app_id, creative_id2, day.strftime('%y%m%d')): add_lists([a1_c2_day, a2_c2_day]),

    # App-AdGroup
    'k:%s:%s:%s'%(app_id, adgroup_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day]),

    # App-Campaign
    'k:%s:%s:%s'%(app_id, campaign_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day]),

    # App-Total
    'k:%s:%s:%s'%(app_id, '', day.strftime('%y%m%d')): prepend_list(a1_day[0]+a2_day[0], add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day])[1:]),

    ### * ###
    # *-Creative
    'k:%s:%s:%s'%('', creative_id1, day.strftime('%y%m%d')): add_lists([a1_c1_day, a2_c1_day]),
    'k:%s:%s:%s'%('', creative_id2, day.strftime('%y%m%d')): add_lists([a1_c2_day, a2_c2_day]),

    # *-AdGroup
    'k:%s:%s:%s'%('', adgroup_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day]),

    # *-Campaign
    'k:%s:%s:%s'%('', campaign_id, day.strftime('%y%m%d')): add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day]),

    # *-*
    'k:%s:%s:%s'%('', '', day.strftime('%y%m%d')): prepend_list(a1_day[0]+a2_day[0], add_lists([a1_c1_day, a1_c2_day, a2_c1_day, a2_c2_day])[1:]),
    }


    # verify there's no StatsModels in datastore yet
    assert_equals(StatsModel.all().count(), 0)
    
    # hour1
    # the first 4 updates should get overriden 
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=[100, 90, 80, 70], date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id2, counts=[100, 90, 80, 70], date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id1, counts=[100, 90, 80, 70], date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id2, counts=[100, 90, 80, 70], date_hour=hour1))
       
    stats_updater.single_thread_put_models()
    
    # hour1             
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=a1_c1_hour1, date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id2, counts=a1_c2_hour1, date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id1, counts=a2_c1_hour1, date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id2, counts=a2_c2_hour1, date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=a1_hour1, date_hour=hour1))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, counts=a2_hour1, date_hour=hour1))
       
    # hour2
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=a1_c1_hour2, date_hour=hour2))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id2, counts=a1_c2_hour2, date_hour=hour2))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id1, counts=a2_c1_hour2, date_hour=hour2))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id2, counts=a2_c2_hour2, date_hour=hour2))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=a1_hour2, date_hour=hour2))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, counts=a2_hour2, date_hour=hour2))

    # day
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id1, counts=a1_c1_day, date=day))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, creative_key=creative_id2, counts=a1_c2_day, date=day))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id1, counts=a2_c1_day, date=day))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, creative_key=creative_id2, counts=a2_c2_day, date=day))
    assert_true(stats_updater.update_model(adunit_key=adunit_id1, counts=a1_day, date=day))
    assert_true(stats_updater.update_model(adunit_key=adunit_id2, counts=a2_day, date=day))
    
    stats_updater.single_thread_put_models() 
            
            
    assert_equals(App.all().count(), 1)
    assert_equals(Campaign.all().count(), 1)
    assert_equals(AdGroup.all().count(), 1)
    assert_equals(AdUnit.all().count(), 2)
    assert_equals(Creative.all().count(), 2)

    assert_equals(len(obj_dict)+1, StatsModel.all().count())            

    for stats in StatsModel.all():
        key_name = stats.key().name()
        if len(key_name.split(':')) == 2: continue # skip the account 
        
        # for debugging
        readable_key_name = debug_key_name(key_name, id_dict)
        debug_helper(readable_key_name, obj_dict[key_name], [stats.request_count, stats.impression_count, stats.click_count, stats.conversion_count])

        # assert equality check
        assert_equals(obj_dict[key_name], [stats.request_count, stats.impression_count, stats.click_count, stats.conversion_count])
    
    # assert False
    
    # invalid parameters should return False    
    assert_false(stats_updater.update_model('blah', 'blah', a1_c1_hour2, date_hour=hour1))
    # adunit_id cannot be None
    assert_false(stats_updater.update_model(None, creative_id1, a1_c1_hour2, date_hour=hour1))
    # counts cannot be None
    assert_false(stats_updater.update_model(adunit_id1, creative_id1, None, date_hour=hour1))
    
    
