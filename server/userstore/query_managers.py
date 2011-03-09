import logging
from datetime import timedelta

from google.appengine.ext import db

from common.utils.cachedquerymanager import CachedQueryManager
from userstore.models import MobileUser, MobileApp, ClickEvent, AppOpenEvent, CLICK_EVENT_NO_APP_ID, DEFAULT_CONVERSION_WINDOW


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

    def get_mobile_apps(self, udid, mobile_appid=None, limit=50):
        mobile_apps = MobileApp.all()
        mobile_apps = mobile_apps.filter('udid = ', udid)
        if mobile_appid:
            mobile_apps = mobile_apps.filter('mobile_appid = ', mobile_appid)
        return mobile_apps.fetch(limit)

    def put_mobile_app(self, mobile_app):
        return db.run_in_transaction(MobileAppManager._insert_mobile_app_transaction, mobile_app.udid, mobile_app.mobile_appid)

    @staticmethod
    def get_or_insert(udid, mobile_appid):
        mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
        mobile_app = MobileApp.get(mobile_app_db_key)
        if not mobile_app:
            return db.run_in_transaction(MobileAppManager._insert_mobile_app_transaction, udid, mobile_appid)
        return mobile_app

    @staticmethod
    def _insert_mobile_app_transaction(udid, mobile_appid):
        mobile_user = MobileUserManager.get_or_insert(udid)
        mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
        mobile_app.put()
        return mobile_app
    
    
class ClickEventManager(CachedQueryManager):
    Model = ClickEvent

    def get_click_events(self, udid=None, mobile_appid=None, \
                             adunit=None, creative=None, \
                             limit=50):
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
                                limit=50):
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
        app_open_event = AppOpenEvent(udid=udid, mobile_appid=mobile_appid, time=time, conversion_window=conversion_window)
        
        # get mobile app that was opened
        mobile_app_db_key = MobileApp.get_db_key(udid, mobile_appid)
        mobile_app = MobileApp.get(mobile_app_db_key)
        if not mobile_app:
                mobile_user = MobileUserManager.get_or_insert(udid)
                mobile_app = MobileApp(udid=udid, mobile_appid=mobile_appid)
                mobile_app.put()
        elif mobile_app.latest_click_time:
            # associate conversion adunit and creative if within window
            if (time - mobile_app.latest_click_time) < timedelta(conversion_window):
                app_open_event.conversion_adunit = mobile_app.latest_click_adunit
                app_open_event.conversion_creative = mobile_app.latest_click_creative
                app_open_event.put()
                return app_open_event, True

        app_open_event.put()
        return app_open_event, False
        
            
    
    


