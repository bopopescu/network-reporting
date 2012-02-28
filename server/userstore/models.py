# Google AppEngine Datastore Hierarchy:
#
# MobileUser
#     MobileApp
#         ClickEvent (mobile_appid specified)
#         AppOpenEvent
#     ClickEvent (mobile_appid not specified, i.e. mobile_appid=CLICK_EVENT_NO_APP_ID)

import datetime
import logging

from google.appengine.ext import db
from google.appengine.ext.db import Key

from userstore.helper import get_key_name, get_required_param, check_required_param


CLICK_EVENT_NO_APP_ID = 'NOT_PROVIDED'
DEFAULT_CONVERSION_WINDOW = 30 # days


class MobileUser(db.Model):
    udid = db.StringProperty(required=True)
    num_purchases = db.IntegerProperty(default=0)

    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key', None):
            udid = get_required_param('udid', kwargs)
            key_name = get_key_name(udid)
        super(MobileUser, self).__init__(parent=parent, key_name=key_name, **kwargs)
        
    @classmethod
    def get_db_key(cls, udid):
        return Key.from_path(cls.kind(), get_key_name(udid))


class MobileApp(db.Model):
    udid = db.StringProperty(required=True)
    mobile_appid = db.StringProperty(required=True)
    latest_click_time = db.DateTimeProperty()
    latest_click_adunit = db.StringProperty()
    latest_click_creative = db.StringProperty()
    opened = db.BooleanProperty(default=False)
    num_purchases = db.IntegerProperty(default=0)

    def __init__(self, parent=None, key_name=None, **kwargs):
        udid = get_required_param('udid', kwargs)
        mobile_appid = get_required_param('mobile_appid', kwargs)

        if not kwargs.get('key', None):
            if not parent:
                parent = MobileUser.get_db_key(udid)
            if not key_name:
                key_name = get_key_name(mobile_appid)
        super(MobileApp, self).__init__(parent=parent, key_name=key_name, **kwargs)
        
    @classmethod
    def get_db_key(cls, udid, mobile_appid):
        return Key.from_path(MobileUser.kind(), get_key_name(udid),
                             cls.kind(), get_key_name(mobile_appid))


class ClickEvent(db.Model):
    udid = db.StringProperty(required=True)
    mobile_appid = db.StringProperty()
    time = db.DateTimeProperty(required=True)
    adunit = db.StringProperty(required=True)
    creative = db.StringProperty(required=True)
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        udid = get_required_param('udid', kwargs)
        mobile_appid = kwargs.get('mobile_appid', None)
        check_required_param('time', kwargs)
        check_required_param('adunit', kwargs)
        check_required_param('creative', kwargs)

        if not kwargs.get('key', None):
            if not parent:
                if mobile_appid:
                    parent = MobileApp.get_db_key(udid, mobile_appid)
                else:
                    kwargs['mobile_appid'] = CLICK_EVENT_NO_APP_ID
                    parent = MobileUser.get_db_key(udid)
        super(ClickEvent, self).__init__(parent=parent, key_name=key_name, **kwargs)
        
        
class AppOpenEvent(db.Model):
    udid = db.StringProperty(required=True)
    mobile_appid = db.StringProperty(required=True)
    time = db.DateTimeProperty(required=True)
    conversion_delay = db.IntegerProperty() # number of secs between click time and open time
    conversion_adunit = db.StringProperty()
    conversion_creative = db.StringProperty()

    def __init__(self, parent=None, key_name=None, **kwargs):
        udid = get_required_param('udid', kwargs)
        mobile_appid = get_required_param('mobile_appid', kwargs)
        check_required_param('time', kwargs)
            
        if not kwargs.get('key', None):
            if not parent:
                parent = MobileApp.get_db_key(udid, mobile_appid)
        super(AppOpenEvent, self).__init__(parent=parent, key_name=key_name, **kwargs)
  

class InAppPurchaseEvent(db.Model):
    udid = db.StringProperty(required=True)
    mobile_appid = db.StringProperty()
    receipt = db.TextProperty()
    time = db.DateTimeProperty(required=True,auto_now_add=True)
    transaction_id = db.StringProperty(required=True)
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        udid = get_required_param('udid', kwargs)
        mobile_appid = kwargs.get('mobile_appid', None)
        transaction_id = get_required_param('transaction_id',kwargs)
        check_required_param('time', kwargs)
        check_required_param('receipt', kwargs)
    
        if not kwargs.get('key', None):
            if not parent:
                if mobile_appid:
                    parent = MobileApp.get_db_key(udid, mobile_appid)
                else:
                    kwargs['mobile_appid'] = CLICK_EVENT_NO_APP_ID
                    parent = MobileUser.get_db_key(udid)
                if not key_name:
                    key_name = get_key_name(transaction_id)
                    
        super(InAppPurchaseEvent, self).__init__(parent=parent, key_name=key_name, **kwargs)    
        
    @classmethod
    def get_db_key(cls, transaction_id, udid, mobile_appid=None):
        if mobile_appid:
            parent = MobileApp.get_db_key(udid, mobile_appid)
        else:
            parent = MobileUser.get_db_key(udid)
        
        return Key.from_path(cls.kind(), get_key_name(transaction_id),parent=parent)
        
    
    
    def __repr__(self):
        return 'InAppPurchaseEvent(udid=%s, mobile_appid=%s, reciept=%s, time=%s)'%(self.udid,
                                                                                    self.mobile_appid,
                                                                                    self.receipt,
                                                                                    self.time)


class ImpressionEvent(db.Model):
    """
    Abstract class
    """
    udid = db.StringProperty(required=True)
    adgroup_id = db.StringProperty(required=True)
    time = db.DateTimeProperty(required=True)
    count = db.IntegerProperty(default=0)

    def __init__(self, parent=None, key_name=None, **kwargs):
        udid = get_required_param('udid', kwargs)
        adgroup_id = get_required_param('adgroup_id', kwargs)
        time = get_required_param('time', kwargs)

        if not kwargs.get('key', None):
            if not parent:
                parent = MobileUser.get_db_key(udid)
                if not key_name:
                    key_name = self.get_key_name(adgroup_id, time)
                    
            time = self.set_time_precision(time)
            kwargs.update(time=time)

        super(ImpressionEvent, self).__init__(parent=parent, key_name=key_name, **kwargs)

    @classmethod
    def get_key_name(cls, adgroup_id, time):
        return get_key_name([adgroup_id, cls.format_time(time)])

    @classmethod
    def set_time_precision(cls, time):
        raise NotImplementedError

    @classmethod
    def format_time(cls, time):
        raise NotImplementedError

    @classmethod
    def get_db_key(cls, udid, adgroup_id, time):
        parent = MobileUser.get_db_key(udid)
        return Key.from_path(cls.kind(), cls.get_key_name(adgroup_id, time), parent=parent)

class HourlyImpressionEvent(ImpressionEvent):
    
    @classmethod
    def set_time_precision(cls, time):
        return datetime.datetime(time.year, time.month, time.day, time.hour)
    
    @classmethod
    def format_time(cls, time):
        return time.strftime('%y%m%d%H')

class DailyImpressionEvent(ImpressionEvent):
    
    @classmethod
    def set_time_precision(cls, time):
        return datetime.datetime(time.year, time.month, time.day)
    
    @classmethod
    def format_time(cls, time):
        return time.strftime('%y%m%d')
    