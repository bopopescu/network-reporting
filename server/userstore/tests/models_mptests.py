import sys
import os
import logging
from datetime import datetime

sys.path.append(os.environ['PWD'])

from google.appengine.ext import db
from nose.tools import assert_equals, assert_not_equals, assert_true, assert_raises

from userstore.models import MobileUser, MobileApp, ClickEvent, AppOpenEvent, CLICK_EVENT_NO_APP_ID, DEFAULT_CONVERSION_WINDOW


SAMPLE_UDID1 = 'udid1'
SAMPLE_UDID2 = 'udid2'
SAMPLE_MOBILE_APPID1 = 'mobile_appid1'
SAMPLE_MOBILE_APPID2 = 'mobile_appid2'
SAMPLE_ADUNIT1 = 'adunit1'
SAMPLE_CREATIVE1 = 'creative1'


def clear_datastore():
    db.delete(MobileUser.all())
    db.delete(MobileApp.all())
    db.delete(ClickEvent.all())
    db.delete(AppOpenEvent.all())

    
def mobile_user_model_mptests():
    # creation
    user = MobileUser(udid=SAMPLE_UDID1)
    user.put()

    # fetch count check
    assert_equals(MobileUser.all().count(), 1)
    fetched_user = MobileUser.all().fetch(1)[0]

    # udid and key check
    assert_equals(fetched_user.udid, SAMPLE_UDID1)
    assert_equals(fetched_user.udid, user.udid)
    assert_equals(fetched_user.key(), user.key())

    # parent key check
    assert_true(fetched_user.parent_key() is None)
    
    # deletion
    user.delete()

    # fetch count check again
    assert_equals(MobileUser.all().count(), 0)

    # cleanup
    clear_datastore()

    
def mobile_app_model_mptests():
    # required properties check
    assert_raises(NameError, MobileApp)
    assert_raises(NameError, MobileApp, udid=SAMPLE_UDID1)
    assert_raises(NameError, MobileApp, mobile_appid=SAMPLE_MOBILE_APPID1)

    # creation
    app = MobileApp(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1)
    app.put()

     # fetch count check
    assert_equals(MobileApp.all().count(), 1)
    fetched_app = MobileApp.all().fetch(1)[0]

    # udid and key check
    assert_equals(fetched_app.udid, SAMPLE_UDID1)
    assert_equals(fetched_app.mobile_appid, SAMPLE_MOBILE_APPID1)
    assert_equals(fetched_app.key(), app.key())
    
    # parent key check
    assert_true(fetched_app.parent_key() is not None)

    # cleanup
    clear_datastore()


def click_event_model_mptests():
    #initialization
    dt = datetime.now()
    
    # required properties check
    assert_raises(NameError, ClickEvent)
    assert_raises(NameError, ClickEvent,
                  udid=SAMPLE_UDID1, time=dt, adunit=SAMPLE_ADUNIT1) # missing creative
    assert_raises(NameError, ClickEvent,
                  udid=SAMPLE_UDID1, time=dt, creative=SAMPLE_CREATIVE1) # missing adunit
    assert_raises(NameError, ClickEvent,
                  udid=SAMPLE_UDID1, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1) # missing time
    assert_raises(NameError, ClickEvent,
                  time=dt, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1) # missing udid

    # creation, one with mobile_appid and one without
    ce1 = ClickEvent(udid=SAMPLE_UDID1, time=dt, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    ce2 = ClickEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=dt, adunit=SAMPLE_ADUNIT1, creative=SAMPLE_CREATIVE1)
    db.put([ce1, ce2])
    
     # fetch count check
    assert_equals(ClickEvent.all().count(), 2)
    fetched_ce1 = ClickEvent.all().fetch(2)[0]
    fetched_ce2 = ClickEvent.all().fetch(2)[1]
    
    # udid and key check
    assert_equals(fetched_ce1.udid, SAMPLE_UDID1)
    assert_equals(fetched_ce1.mobile_appid, CLICK_EVENT_NO_APP_ID)
    assert_equals(fetched_ce2.mobile_appid, SAMPLE_MOBILE_APPID1)
    assert_equals(fetched_ce1.time, dt)
    assert_equals(fetched_ce1.adunit, SAMPLE_ADUNIT1)
    assert_equals(fetched_ce1.creative, SAMPLE_CREATIVE1)
    assert_equals(fetched_ce1.key(), ce1.key())
    assert_equals(fetched_ce2.key(), ce2.key())
    assert_not_equals(ce1.key(), ce2.key())

    # parent key check
    assert_true(fetched_ce1.parent_key() is not None)
    assert_true(fetched_ce2.parent_key() is not None)
    assert_not_equals(fetched_ce1.parent_key(), fetched_ce2.parent_key())
    
    # cleanup
    clear_datastore()


def app_open_event_model_mptests():
    # initialization
    dt = datetime.now()

    # required properties check
    assert_raises(NameError, AppOpenEvent)
    assert_raises(NameError, AppOpenEvent,
                  udid=SAMPLE_UDID1, mobile_app=SAMPLE_MOBILE_APPID1) # missing time
    assert_raises(NameError, AppOpenEvent,
                  udid=SAMPLE_UDID1, time=dt) # missing mobile_appid
    assert_raises(NameError, AppOpenEvent,
                  mobile_app=SAMPLE_MOBILE_APPID1, time=dt) # missing udid

    # creation
    aoe1 = AppOpenEvent(udid=SAMPLE_UDID1, mobile_appid=SAMPLE_MOBILE_APPID1, time=dt)
    aoe2 = AppOpenEvent(udid=SAMPLE_UDID2, mobile_appid=SAMPLE_MOBILE_APPID2, time=dt, conversion_window=2)
    db.put([aoe1, aoe2])

    # fetch count check
    assert_equals(AppOpenEvent.all().count(), 2)
    fetched_aoe1 = AppOpenEvent.all().fetch(2)[0]
    fetched_aoe2 = AppOpenEvent.all().fetch(2)[1]
    
    # properties check
    assert_equals(fetched_aoe1.udid, SAMPLE_UDID1)
    assert_equals(fetched_aoe1.mobile_appid, SAMPLE_MOBILE_APPID1)
    assert_equals(fetched_aoe1.time, dt)
    assert_equals(fetched_aoe1.conversion_window, DEFAULT_CONVERSION_WINDOW)

    assert_equals(fetched_aoe2.udid, SAMPLE_UDID2)
    assert_equals(fetched_aoe2.mobile_appid, SAMPLE_MOBILE_APPID2)
    assert_equals(fetched_aoe2.time, dt)
    assert_equals(fetched_aoe2.conversion_window, 2)

    assert_equals(fetched_aoe1.key(), aoe1.key())
    assert_equals(fetched_aoe2.key(), aoe2.key())
    assert_not_equals(aoe1.key(), aoe2.key())

    # parent key check
    assert_true(fetched_aoe1.parent_key() is not None)
    assert_true(fetched_aoe2.parent_key() is not None)
    assert_not_equals(fetched_aoe1.parent_key(), fetched_aoe2.parent_key())

    # cleanup
    clear_datastore()


    
                  
    



    


