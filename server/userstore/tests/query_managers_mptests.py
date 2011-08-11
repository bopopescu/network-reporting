import sys
import os
import logging
from time import sleep
from datetime import datetime, timedelta

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from google.appengine.ext import db
from nose.tools import assert_equals, assert_not_equals, assert_true, assert_false, assert_raises

from userstore.query_managers import MobileUserManager, MobileAppManager, ClickEventManager, AppOpenEventManager, InAppPurchaseEventManager
from userstore.models import MobileUser, MobileApp, ClickEvent, AppOpenEvent, InAppPurchaseEvent, CLICK_EVENT_NO_APP_ID


SAMPLE_UDID1 = 'udid1'
SAMPLE_UDID2 = 'udid2'
SAMPLE_UDID3 = 'udid3'
SAMPLE_MOBILE_APPID1 = 'mobile_appid1'
SAMPLE_MOBILE_APPID2 = 'mobile_appid2'
SAMPLE_MOBILE_APPID3 = 'mobile_appid3'
SAMPLE_ADUNIT1 = 'adunit1'
SAMPLE_ADUNIT2 = 'adunit2'
SAMPLE_ADUNIT3 = 'adunit3'
SAMPLE_CREATIVE1 = 'creative1'
SAMPLE_CREATIVE2 = 'creative2'


def clear_datastore():
    db.delete(MobileUser.all())
    db.delete(MobileApp.all())
    db.delete(ClickEvent.all())
    db.delete(AppOpenEvent.all())
    db.delete(InAppPurchaseEvent.all())

def mobile_user_manager_mptests():
    # initialize
    user = MobileUser(udid=SAMPLE_UDID1)
    manager = MobileUserManager()

    # get() and put()
    assert_true(manager.put_mobile_user(user) is not None)
    fetched_user = manager.get_mobile_user(SAMPLE_UDID1)
    assert_true(fetched_user is not None)
    assert_equals(fetched_user.key(), user.key())

    # get_or_insert()
    user.delete()
    fetched_user = manager.get_or_insert(SAMPLE_UDID1)
    assert_true(fetched_user is not None)
    assert_equals(fetched_user.udid, SAMPLE_UDID1)

    # cleanup
    clear_datastore()

    
def mobile_app_manager_mptests():
    # initialize 2 different apps under the same udid
    app1 = MobileApp(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1)
    app2 = MobileApp(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID2)
    manager = MobileAppManager()

    # put()
    assert_true(manager.put_mobile_app(app1) is not None)
    assert_true(manager.put_mobile_app(app2) is not None)
    
    # get()
    fetched_apps = manager.get_mobile_apps(udid=SAMPLE_UDID1)
    assert_equals(len(fetched_apps), 2)
    fetched_apps = manager.get_mobile_apps(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1)
    assert_equals(len(fetched_apps), 1)
    assert_equals(fetched_apps[0].key(), app1.key())

    # get_or_insert()
    fetched_app = MobileAppManager.get_or_insert(SAMPLE_UDID1, SAMPLE_MOBILE_APPID1) # get existing entry
    assert_true(fetched_app is not None)
    assert_equals(MobileApp.all().count(), 2) 
    assert_equals(MobileUser.all().count(), 1)

    fetched_app = MobileAppManager.get_or_insert(SAMPLE_UDID2, SAMPLE_MOBILE_APPID3) # insert new entry
    assert_true(fetched_app is not None)
    assert_equals(MobileApp.all().count(), 3) 
    assert_equals(MobileUser.all().count(), 2)
    
    # cleanup
    clear_datastore()


def click_event_manager_filtering_mptests():
    # initialize
    ce1 = ClickEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=datetime.now(), adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    ce2 = ClickEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID2, time=datetime.now(), adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    ce3 = ClickEvent(udid=SAMPLE_UDID2, mobile_appid=CLICK_EVENT_NO_APP_ID, time=datetime.now(), adunit=SAMPLE_ADUNIT2, creative=SAMPLE_CREATIVE2)
    ce4 = ClickEvent(udid=SAMPLE_UDID3, mobile_appid=SAMPLE_MOBILE_APPID1, time=datetime.now(), adunit=SAMPLE_ADUNIT2, creative=SAMPLE_CREATIVE2)
    ce5 = ClickEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=datetime.now(), adunit=SAMPLE_ADUNIT3, creative=SAMPLE_CREATIVE2)
    db.put([ce1, ce2, ce3, ce4, ce5])
    assert_equals(ClickEvent.all().count(), 5)
    manager = ClickEventManager()

    # test cases
    fetched_ce = manager.get_click_events(udid=SAMPLE_UDID1)
    assert_equals(len(fetched_ce), 3)

    fetched_ce = manager.get_click_events(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1)
    assert_equals(len(fetched_ce), 2)

    fetched_ce = manager.get_click_events(udid=SAMPLE_UDID1, mobile_appid=CLICK_EVENT_NO_APP_ID)
    assert_equals(len(fetched_ce), 0)

    fetched_ce = manager.get_click_events(udid=SAMPLE_UDID2, mobile_appid=CLICK_EVENT_NO_APP_ID)
    assert_equals(len(fetched_ce), 1)
    
    fetched_ce = manager.get_click_events(udid=SAMPLE_UDID1, adunit=SAMPLE_ADUNIT3)
    assert_equals(len(fetched_ce), 1)

    fetched_ce = manager.get_click_events(adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    assert_equals(len(fetched_ce), 2)

    # cleanup
    clear_datastore()
    
    
def click_event_manager_logging_mptests():
    dt = datetime.now()
    manager = ClickEventManager()
    
    # no mobile_appid provided; only one ClickEvent should be created
    manager.log_click_event(udid=SAMPLE_UDID1, mobile_appid=CLICK_EVENT_NO_APP_ID, time=dt, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    assert_equals(ClickEvent.all().count(), 1)
    assert_equals(MobileApp.all().count(), 0)
    assert_equals(MobileUser.all().count(), 0)

    # mobile_appid provided; new ClickEvent created, with additional associated MobileUser and MobileApp created
    manager.log_click_event(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=dt, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    assert_equals(ClickEvent.all().count(), 2)
    assert_equals(MobileApp.all().count(), 1)
    assert_equals(MobileUser.all().count(), 1)

    fetched_user = MobileUser.all().fetch(1)[0]
    assert_equals(fetched_user.udid, SAMPLE_UDID1)
    
    fetched_app = MobileApp.all().fetch(1)[0]
    assert_equals(fetched_app.udid, SAMPLE_UDID1)
    assert_equals(fetched_app.mobile_appid, SAMPLE_MOBILE_APPID1)
    assert_equals(fetched_app.latest_click_time, dt)
    assert_equals(fetched_app.latest_click_adunit, SAMPLE_ADUNIT1)
    assert_equals(fetched_app.latest_click_creative, SAMPLE_CREATIVE1)

    # clicked again
    manager.log_click_event(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=datetime.now(), adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    assert_equals(ClickEvent.all().count(), 3)
    assert_equals(MobileApp.all().count(), 1)
    assert_equals(MobileUser.all().count(), 1)
    
    # cleanup
    clear_datastore()

    
def app_open_event_manager_filtering_mptests():
    # initialize
    aoe1 = AppOpenEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=datetime.now(), conversion_adunit=SAMPLE_ADUNIT1, conversion_creative=SAMPLE_CREATIVE1)
    aoe2 = AppOpenEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID2, time=datetime.now(), conversion_adunit=SAMPLE_ADUNIT1, conversion_creative=SAMPLE_CREATIVE2)
    aoe3 = AppOpenEvent(udid=SAMPLE_UDID2, mobile_appid=SAMPLE_MOBILE_APPID2, time=datetime.now(), conversion_adunit=SAMPLE_ADUNIT2, conversion_creative=SAMPLE_CREATIVE2)
    aoe4 = AppOpenEvent(udid=SAMPLE_UDID3, mobile_appid=SAMPLE_MOBILE_APPID3, time=datetime.now(), conversion_adunit=SAMPLE_ADUNIT1, conversion_creative=SAMPLE_CREATIVE2)

    db.put([aoe1, aoe2, aoe3, aoe4])
    assert_equals(AppOpenEvent.all().count(), 4)
    manager = AppOpenEventManager()

    # test cases
    fetched_aoe = manager.get_app_open_events(udid=SAMPLE_UDID1)
    assert_equals(len(fetched_aoe), 2)

    fetched_aoe = manager.get_app_open_events(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1)
    assert_equals(len(fetched_aoe), 1)

    fetched_aoe = manager.get_app_open_events(udid=SAMPLE_UDID1, conversion_adunit=SAMPLE_ADUNIT1)
    assert_equals(len(fetched_aoe), 2)

    fetched_aoe = manager.get_app_open_events(udid=SAMPLE_UDID3, conversion_creative=SAMPLE_CREATIVE2)
    assert_equals(len(fetched_aoe), 1)
    
    fetched_aoe = manager.get_app_open_events(conversion_adunit=SAMPLE_ADUNIT1, conversion_creative=SAMPLE_CREATIVE2)
    assert_equals(len(fetched_aoe), 2)

    # cleanup
    clear_datastore()

    
def app_open_event_manager_conversion_logging_mptests():
    dt = datetime.now()
    manager = AppOpenEventManager()
  
    # app gets clicked on
    ce_manager = ClickEventManager()
    ce_manager.log_click_event(SAMPLE_UDID1, SAMPLE_MOBILE_APPID1, dt, SAMPLE_ADUNIT1, SAMPLE_CREATIVE1)
    fetched_app = MobileApp.all().fetch(1)[0]
    assert_equals(fetched_app.latest_click_adunit, SAMPLE_ADUNIT1)
    assert_equals(fetched_app.latest_click_creative, SAMPLE_CREATIVE1)
    assert_equals(fetched_app.latest_click_time, dt)
    
    # app_open_event happens again (hypothetically)
    aoe, conversion_logged = manager.log_conversion(SAMPLE_UDID1, SAMPLE_MOBILE_APPID1, dt)
    assert_equals(AppOpenEvent.all().count(), 1)
    assert_equals(MobileApp.all().count(), 1)
    assert_equals(MobileUser.all().count(), 1)
    assert_true(conversion_logged)
    assert_equals(fetched_app.latest_click_adunit, SAMPLE_ADUNIT1)
    assert_equals(fetched_app.latest_click_creative, SAMPLE_CREATIVE1)
    assert_true(fetched_app.latest_click_time is not None)

    # try open app again after 20 days, which is > default windows of 30 days 
    aoe, conversion_logged = manager.log_conversion(SAMPLE_UDID1, SAMPLE_MOBILE_APPID1, dt+timedelta(40))
    assert_equals(AppOpenEvent.all().count(), 1)
    assert_equals(MobileApp.all().count(), 1)
    assert_equals(MobileUser.all().count(), 1)
    assert_false(conversion_logged)
    assert_true(aoe is None)
    
    # cleanup
    clear_datastore()    

def inapp_purchase_event_manager_conversion_logging_mptests():
    # cleanup
    clear_datastore()
    
    
    dt = datetime.now()
    manager = InAppPurchaseEventManager()
    
    SAMPLE_RECEIPT1 = "{'receipt1':'i am'}"
    SAMPLE_RECEIPT2 = "{'receipt2':'i am'}"
    
    SAMPLE_TRANSACTION_ID1 = "TRANSACTION1"
    SAMPLE_TRANSACTION_ID2 = "TRANSACTION2"
    
    
    # log two inapp purchases one beloging to a user and app and one only to a user
    manager.log_inapp_purchase_event(SAMPLE_TRANSACTION_ID1, SAMPLE_UDID1, dt, SAMPLE_RECEIPT1, SAMPLE_MOBILE_APPID1)
    manager.log_inapp_purchase_event(SAMPLE_TRANSACTION_ID1, SAMPLE_UDID1, dt, SAMPLE_RECEIPT1, SAMPLE_MOBILE_APPID1)
    manager.log_inapp_purchase_event(SAMPLE_TRANSACTION_ID2, SAMPLE_UDID1, dt, SAMPLE_RECEIPT2)
    
    
    # confirms that the right objects are created
    temp = InAppPurchaseEvent.all().fetch(100)
    for t in temp:
        print repr(t)
    assert_equals(InAppPurchaseEvent.all().count(), 2)
    assert_equals(MobileApp.all().count(), 1)
    assert_equals(MobileUser.all().count(), 1)
    
    inapp_purchases = InAppPurchaseEvent.all()
    assert_equals(inapp_purchases[1].receipt, SAMPLE_RECEIPT1)
    assert_equals(inapp_purchases[0].receipt, SAMPLE_RECEIPT2)
    
    
    user = MobileUserManager().get_mobile_user(SAMPLE_UDID1)
    mobile_app = MobileAppManager().get_mobile_apps(SAMPLE_UDID1,SAMPLE_MOBILE_APPID1)[0]
    
    assert_equals(user.num_purchases,2)
    assert_equals(mobile_app.num_purchases,1)
    
    # cleanup
    clear_datastore()
    
