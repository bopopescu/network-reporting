# !/usr/bin/env python

""" Provides handlers for all the ad server functions. For the handler for m/ad
    look at ad_server/handlers/adhandler.py."""

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import os
import hashlib

import urllib
import datetime

urllib.getproxies_macosx_sysconf = lambda: {}

from common.utils.db_deep_get import CONFIG

from google.appengine.api import users, urlfetch, memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images
from ad_server import frequency_capping
from publisher.models import *
from advertiser.models import *

from ad_server import mp_webapp

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from userstore.query_managers import ClickEventManager, AppOpenEventManager

from urllib import unquote

from stats import stats_accumulator
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging
from ad_server import memcache_mangler

###################
# Import Handlers #
###################
from ad_server.handlers import TestHandler, UDIDHandler, MPXUDIDHandler
from ad_server.handlers import adhandler
from ad_server.handlers import budget_handlers

TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"
from userstore.models import CLICK_EVENT_NO_APP_ID


# Figure out if we're on a production server
from google.appengine.api import apiproxy_stub_map
have_appserver = bool(apiproxy_stub_map.apiproxy.GetStub('datastore_v3'))
on_production_server = have_appserver and \
    not os.environ.get('SERVER_SOFTWARE', '').lower().startswith('devel')
DEBUG = not on_production_server


# Only exists in order to have data show up in apache logs
# Currently, this is called only by a taskqueue
# response is dummy
class AdRequestHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write("OK")

# /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUY1NsgDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGJvEIAw&udid=4863585ad8c80749
class AdImpressionHandler(webapp.RequestHandler):
    def get(self):

        # Update budgeting
        # TODO: cache this
        adunit_key = self.request.get('id')
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)

        if not self.request.get('testing') == TEST_MODE:
            stats_accumulator.log(self.request, event=stats_accumulator.IMP_EVENT, adunit_id=adunit_key)


        creative_id = self.request.get('cid')
        if adunit_context:
            creative = adunit_context.get_creative_by_key(creative_id)
            if creative and creative.ad_group.bid_strategy == 'cpm' and creative.ad_group.bid:
                budget_service.apply_expense(creative.ad_group.campaign.budget_obj, creative.ad_group.bid/1000)

            raw_udid = self.request.get("udid")
            if creative:
                freq_response = AdImpressionHandler.increment_frequency_counts(creative=creative,
                                           raw_udid=raw_udid)
            else:
                freq_response = None

        self.response.out.write("OK")

    @classmethod
    def increment_frequency_counts(cls, creative=None,
                                        raw_udid=None,
                                        now=None):
        from userstore.query_managers import ImpressionEventManager

        now = now or datetime.datetime.now()

        impression_types_to_update = []
        if creative.ad_group.daily_frequency_cap:
            impression_types_to_update.append(ImpressionEventManager.DAILY)
        if creative.ad_group.hourly_frequency_cap:
            impression_types_to_update.append(ImpressionEventManager.HOURLY)

        if impression_types_to_update:
            ImpressionEventManager().log_impression(raw_udid, str(creative.adgroup.key()), now, impression_types_to_update)

class AdClickHandler(webapp.RequestHandler):
    # /m/aclk?udid=james&appid=angrybirds&id=ahRldmVudHJhY2tlcnNjYWxldGVzdHILCxIEU2l0ZRipRgw&cid=ahRldmVudHJhY2tlcnNjYWxldGVzdHIPCxIIQ3JlYXRpdmUYoh8M
    def get(self):

        if not self.request.get('testing') == TEST_MODE:
            stats_accumulator.log(self.request, event=stats_accumulator.CLK_EVENT)

        udid = self.request.get('udid')
        mobile_app_id = self.request.get('appid')
        time = datetime.datetime.now()
        adunit_id = self.request.get('id')
        creative_id = self.request.get('cid')

        # Update budgeting
        try:
            creative = Creative.get(Key(creative_id), config=CONFIG)
        except: # db error
            creative = None

        if creative and creative.ad_group.bid_strategy == 'cpc':
            budget_service.apply_expense(creative.ad_group.campaign.budget_obj, creative.ad_group.bid)

        # if driving download then we use the user datastore
        if creative and udid and mobile_app_id and mobile_app_id != CLICK_EVENT_NO_APP_ID:
            # TODO: maybe have this section run asynchronously
            ce_manager = ClickEventManager()
            ce = ce_manager.log_click_event(udid, mobile_app_id, time, adunit_id, creative_id)

        id = self.request.get("id")
        q = self.request.get("q")
        # BROKEN
        # url = self.request.get("r")
        sz = self.request.query_string
        r = sz.rfind("&r=")
        if r > 0:
            url = sz[(r + 3):]
            url = unquote(url)
            # forward on to the click URL
            self.redirect(url)
        else:
            self.response.out.write("ClickEvent:OK:")

# TODO: Process this on the logs processor
class AppOpenHandler(webapp.RequestHandler):
    # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA
    def get(self):
        from common.utils.helpers import get_udid_appid

        udid, mobile_appid = get_udid_appid(self.request)

        # bail early if udid AND mobile_appid is not provided
        if not (udid and mobile_appid):
            return

        aoe_manager = AppOpenEventManager()
        aoe, conversion_logged = aoe_manager.log_conversion(udid, mobile_appid, time=datetime.datetime.now())

        if aoe and conversion_logged:
            stats_accumulator.log(self.request, event=stats_accumulator.CONV_EVENT, adunit_id=aoe.conversion_adunit, creative_id=aoe.conversion_creative, udid=udid)
            self.response.out.write("ConversionLogged:"+str(conversion_logged)+":"+str(aoe.key()))
        else:
            self.response.out.write("ConversionLogged:"+str(conversion_logged))

class PurchaseHandler(webapp.RequestHandler):
    def get(self):
        return self.post()

    def post(self):
        from google.appengine.api import taskqueue
        trace_logging.info(self.request.get("receipt"))
        trace_logging.info(self.request.get("udid"))
        stats_accumulator.log_inapp_purchase(request=self.request,
                                      event=stats_accumulator.INAPP_EVENT,
                                      udid=self.request.get('udid'),
                                      receipt=self.request.get('receipt'),
                                      mobile_appid=self.request.get('appid'),)
        self.response.out.write("OK")

class PurchaseHandlerTxn(webapp.RequestHandler):
    def post(self):
        import base64
        import urllib2
        from common.utils import simplejson
        from userstore.query_managers import InAppPurchaseEventManager
        # verify the receipt with apple

        url = "https://buy.itunes.apple.com/verifyReceipt"
        # sandbox
        # url = "https://sandbox.itunes.apple.com/verifyReceipt"

        udid = self.request.get('udid')
        receipt_data = self.request.get('receipt')
        receipt_dict = {"receipt-data":base64.encodestring(str(receipt_data))}
        data = simplejson.dumps(receipt_dict)
        req = urllib2.Request(url, data)
        resp = urllib2.urlopen(req)
        page = resp.read()
        json_response = simplejson.loads(page)
        logging.info('inapp receipt: %s'%json_response)
        if (json_response['status']==0):
            receipt_dict = json_response.get('receipt')
            logging.info('receipt dict: %s'%receipt_dict)
            # user either the transaction id or the hash of the purchase date
            transaction_id = receipt_dict.get('transaction_id',
                hashlib.sha1(receipt_dict['original_purchase_date']).hexdigest())

            InAppPurchaseEventManager().log_inapp_purchase_event(transaction_id=transaction_id,
                                                        udid=self.request.get('udid'),
                                                        receipt=simplejson.dumps(receipt_dict),
                                                        time=datetime.datetime.fromtimestamp(float(self.request.get('time'))),
                                                        mobile_appid=self.request.get('mobile_appid'))
        else:
            logging.error("invalid receipt")


def main():
    application = mp_webapp.MPLoggingWSGIApplication([('/m/ad', adhandler.AdHandler),
                                                  ('/m/imp', AdImpressionHandler),
                                                  ('/m/aclk', AdClickHandler),
                                                  ('/m/open', AppOpenHandler),
                                                  ('/m/track', AppOpenHandler),
                                                  ('/m/test', TestHandler),
                                                  ('/m/mpid',UDIDHandler),
                                                  ('/m/mpx/mpid', MPXUDIDHandler),
                                                  ('/m/memclear', memcache_mangler.ClearHandler),
                                                  ('/m/memshow', memcache_mangler.ShowHandler),
                                                  ('/m/purchase', PurchaseHandler),
                                                  ('/m/purchase_txn', PurchaseHandlerTxn),
                                                  ('/m/req', AdRequestHandler),
                                                  ('/_ah/warmup', adhandler.AdHandler),
                                                  ('/m/budget/advance/', budget_handlers.BudgetAdvanceHandler),
                                                  ('/m/budget/advance_worker/', budget_handlers.BudgetAdvanceWorkerHandler)],
                                                  debug=DEBUG)
    run_wsgi_app(application)
    # wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
    main()
