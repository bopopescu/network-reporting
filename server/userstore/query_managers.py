import logging
from datetime import timedelta

from google.appengine.ext import db

from common.utils.query_managers import CachedQueryManager
from userstore.models import MobileUser, MobileApp, ClickEvent, AppOpenEvent, ImpressionEvent, \
                             InAppPurchaseEvent, HourlyImpressionEvent, DailyImpressionEvent, \
                             CLICK_EVENT_NO_APP_ID, DEFAULT_CONVERSION_WINDOW

from common.constants import MAX_OBJECTS

NAMESPACE = None


class MobileUserManager(CachedQueryManager):
    Model = MobileUser

    def get_mobile_user(self, udid):
        return MobileUser.get(MobileUser.get_db_key(udid))
    
    def put_mobile_user(self, mobile_user):
            return mobile_user.put()

    @staticmethod
    def get_or_insert(udid):
        mobile_user_key = MobileUser.get_db_key(udid)
        mobile_user = MobileUser.get(mobile_user_key)
        if not mobile_user:
            mobile_user = MobileUser(udid=udid)
            mobile_user.put()
        return mobile_user

class MobileAppManager(CachedQueryManager):
    Model = MobileApp

    def get_mobile_apps(self, udid, mobile_appid=None, limit=MAX_OBJECTS):
        if mobile_appid:
            mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
            return [MobileApp.get(mobile_app_db_key)]
        else:
            return MobileApp.all().ancestor(MobileUser.get_db_key(udid)).fetch(limit)

    def put_mobile_app(self, mobile_app):
        return db.run_in_transaction(MobileAppManager._insert_mobile_app_txn, mobile_app.udid, mobile_app.mobile_appid)

    @staticmethod
    def get_or_insert(udid, mobile_appid, transaction=True):
        if transaction:
            return db.run_in_transaction(MobileAppManager._get_or_insert_txn, udid, mobile_appid)
        else:
            return MobileAppManager._get_or_insert_txn(udid, mobile_appid)     
    
    @staticmethod
    def _get_or_insert_txn(udid, mobile_appid):
        mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
        mobile_app = MobileApp.get(mobile_app_db_key)
        if not mobile_app:
            return MobileAppManager._insert_mobile_app_txn(udid, mobile_appid)
        return mobile_app

    @staticmethod
    def _insert_mobile_app_txn(udid, mobile_appid):
        mobile_user = MobileUserManager.get_or_insert(udid)
        mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
        mobile_app.put()
        return mobile_app
    
    
class ClickEventManager(CachedQueryManager):
    Model = ClickEvent

    def get_click_events(self, udid=None, mobile_appid=None, \
                             adunit=None, creative=None, \
                             limit=MAX_OBJECTS):
        click_events = ClickEvent.all()
        if udid:
            click_events = click_events.filter('udid =', udid)
        if mobile_appid:
            click_events = click_events.filter('mobile_appid =', mobile_appid)
        if adunit:
            click_events = click_events.filter('adunit = ', adunit)
        if creative:
            click_events = click_events.filter('creative = ', creative)
        return click_events.fetch(limit)

    def log_click_event(self, udid, mobile_appid, time, adunit, creative):
        return db.run_in_transaction(self._log_click_event_transaction, udid, mobile_appid, time, adunit, creative)
        
    def _log_click_event_transaction(self, udid, mobile_appid, time, adunit, creative):
        # create click event
        click_event = ClickEvent(udid=udid, mobile_appid=mobile_appid, time=time, adunit=adunit, creative=creative)
        click_event.put()
        # update corresponding mobile app with latest click info
        if mobile_appid and mobile_appid != CLICK_EVENT_NO_APP_ID:
            mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
            mobile_app = MobileApp.get(mobile_app_db_key)
            if not mobile_app:
                mobile_user = MobileUserManager.get_or_insert(udid)
                mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
            mobile_app.latest_click_time = time
            mobile_app.latest_click_adunit = adunit
            mobile_app.latest_click_creative = creative
            mobile_app.put()
        return click_event
                               
        
class AppOpenEventManager(CachedQueryManager):
    Model = AppOpenEvent

    def get_app_open_events(self, udid=None, mobile_appid=None, \
                                conversion_adunit=None, conversion_creative=None, \
                                limit=MAX_OBJECTS):
        app_open_events = AppOpenEvent.all()
        if udid:
            app_open_events = app_open_events.filter('udid = ', udid)
        if mobile_appid:
            app_open_events = app_open_events.filter('mobile_appid = ', mobile_appid)
        if conversion_adunit:
            app_open_events = app_open_events.filter('conversion_adunit = ', conversion_adunit)
        if conversion_creative:
            app_open_events = app_open_events.filter('conversion_creative = ', conversion_creative)
        return app_open_events.fetch(limit)

    def log_conversion(self, udid, mobile_appid, time, conversion_window=DEFAULT_CONVERSION_WINDOW):
        return db.run_in_transaction(self._log_conversion_transaction, udid, mobile_appid, time, conversion_window)
    
    def _log_conversion_transaction(self, udid, mobile_appid, time, conversion_window):
        # create app open event
        app_open_event = AppOpenEvent(udid=udid, mobile_appid=mobile_appid, time=time)
        
        # try to get mobile app that was opened
        mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
        mobile_app = MobileApp.get(mobile_app_db_key)

        # if mobile_app doesn't exist, create it but don't log conversion event
        if not mobile_app:
            mobile_user = MobileUserManager.get_or_insert(udid)
            mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
            mobile_app.opened = True
            mobile_app.put()
            app_open_event.put()
            return app_open_event, False
        elif mobile_app.latest_click_time and not mobile_app.opened:  # mobile_app exists, i.e. the ad driving it's download was clicked on 
            # associate conversion adunit and creative if within window
            open_delay = time - mobile_app.latest_click_time
            if open_delay < timedelta(DEFAULT_CONVERSION_WINDOW):
                conversion = True
            else:
                conversion = False  

            app_open_event.conversion_adunit = mobile_app.latest_click_adunit
            app_open_event.conversion_creative = mobile_app.latest_click_creative
            app_open_event.conversion_delay = open_delay.seconds + open_delay.days * 86400
            app_open_event.put() 
            mobile_app.opened = True
            mobile_app.put()
            return app_open_event, conversion
               
        # mobile_app exists but either already opened OR
        # doesn't have latest_click_time (i.e. mobile_app not created as result of ClickEvent)
        return None, False    

        
class InAppPurchaseEventManager(CachedQueryManager):            
    def get_inapp_purchase_event(self, udid, mobile_appid=None, limit=MAX_OBJECTS):
        inapp_purchase_events = InAppPurchaseEvent.all()
        # the parent is either a mobile user
        # or mobile_appid depending on the query
        # NOTE: this query will return all the inapp events
        # for a given udid if mobile_appid is None no matter
        # if its directly placed under an mobileuser or mobileapp
        if mobile_appid:
            parent = MobileApp.get_db_key(udid, mobile_appid)
        else:
            parent = MobileUser.get_db_key(udid)
        inapp_purchase_events = inapp_purchase_events.ancestor(parent)
        return inapp_purchase_events.fetch(limit)
    
    def log_inapp_purchase_event(self, transaction_id, udid, time, receipt, mobile_appid=None):
        return db.run_in_transaction(self._log_inapp_purchase_event, transaction_id, udid, time, receipt, mobile_appid)
    
    def _log_inapp_purchase_event(self, transaction_id, udid, time, receipt, mobile_appid=None):
        # get or create this mobile user
        # then increment its in app purchase account
        mobile_user = MobileUserManager.get_or_insert(udid)

        # get or create this mobile app for this user
        # then increment its in app purchase account        
        if mobile_appid:
            # attempt to get mobile app from db
            mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
            mobile_app = MobileApp.get(mobile_app_db_key)
            # if not there, create it and update its num_purchases
            if not mobile_app:
                mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
                mobile_app.put()
                    
        # create and put an new inapp purchase event if its new
        # otherwise return the old one
        inapp_purchase_event = InAppPurchaseEvent.get(InAppPurchaseEvent.get_db_key(transaction_id, udid, mobile_appid))
        if not inapp_purchase_event:
            inapp_purchase_event = InAppPurchaseEvent(udid=udid,time=time,receipt=receipt,mobile_appid=mobile_appid, transaction_id=transaction_id)
            inapp_purchase_event.put()
            
            # update num_purchases
            mobile_user.num_purchases += 1
            mobile_user.put()
            
            if mobile_appid:
                mobile_app.num_purchases += 1
                mobile_app.put()
            
        return inapp_purchase_event
        
    
class ImpressionEventManager(CachedQueryManager):

    IMPRESSION_TYPES_TO_MODEL = {'hourly': HourlyImpressionEvent, 'daily': DailyImpressionEvent}
    HOURLY = 'hourly'
    DAILY = 'daily'

    def get_impression_events(self, udid, adgroup_ids, time):
        hourly_keys = []
        daily_keys = []
        for adgroup_id in adgroup_ids:
            hourly_keys += [HourlyImpressionEvent.get_db_key(udid, adgroup_id, time)]
            daily_keys += [DailyImpressionEvent.get_db_key(udid, adgroup_id, time)]
        return HourlyImpressionEvent.get(hourly_keys) + DailyImpressionEvent.get(daily_keys)

    def log_impression(self, udid, adgroup_id, time, impression_types):
        return db.run_in_transaction(self._log_impression_transaction, udid, str(adgroup_id), time, impression_types)

    def _log_impression_transaction(self, udid, adgroup_id, time, impression_types):
        for impression_type in impression_types:
            Model = self.IMPRESSION_TYPES_TO_MODEL[impression_type]
            imp_db_key = Model.get_db_key(udid, adgroup_id, time)
            imp = Model.get(imp_db_key)
            
            # ensures that user objects exist
            mobile_user = MobileUserManager.get_or_insert(udid)
            if not imp:
                imp = Model(udid=udid, adgroup_id=adgroup_id, time=time)

            imp.count += 1
            imp.put()
