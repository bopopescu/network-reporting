# !/usr/bin/env python
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

import os

import urllib
import datetime

urllib.getproxies_macosx_sysconf = lambda: {}
                          
from ad_server.adserver_templates import TEMPLATES

from google.appengine.api import users, urlfetch, memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images

from publisher.models import *
from advertiser.models import *

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from userstore.query_managers import ClickEventManager, AppOpenEventManager

from urllib import unquote

from mopub_logging import mp_logging
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging
from ad_server import memcache_mangler

###################
# Import Handlers #
###################
from ad_server.handlers import TestHandler
from ad_server.handlers import adhandler

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
        creative_id = self.request.get('cid')
        creative = adunit_context.get_creative_by_key(creative_id)
        if creative.ad_group.bid_strategy == 'cpm':
            budget_service.apply_expense(creative.ad_group.campaign, creative.ad_group.bid/1000)
        
        if not self.request.get('testing') == TEST_MODE:
            mp_logging.log(self.request,event=mp_logging.IMP_EVENT,adunit=adunit_context.adunit)  
            
        self.response.out.write("OK")
    
class AdClickHandler(webapp.RequestHandler):
    # /m/aclk?udid=james&appid=angrybirds&id=ahRldmVudHJhY2tlcnNjYWxldGVzdHILCxIEU2l0ZRipRgw&cid=ahRldmVudHJhY2tlcnNjYWxldGVzdHIPCxIIQ3JlYXRpdmUYoh8M
    def get(self):
        
        if not self.request.get('testing') == TEST_MODE:
            mp_logging.log(self.request, event=mp_logging.CLK_EVENT)  
  
        udid = self.request.get('udid')
        mobile_app_id = self.request.get('appid')
        time = datetime.datetime.now()
        adunit_id = self.request.get('id')
        creative_id = self.request.get('cid')

        # Update budgeting
        creative = Creative.get(Key(creative_id))
        if creative.ad_group.bid_strategy == 'cpc':
            budget_service.apply_expense(creative.ad_group.campaign, creative.ad_group.bid/1000)


        # if driving download then we use the user datastore
        if udid and mobile_app_id and mobile_app_id != CLICK_EVENT_NO_APP_ID:
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
        udid = self.request.get('udid')
        mobile_appid = self.request.get('id')
        aoe_manager = AppOpenEventManager()
        aoe, conversion_logged = aoe_manager.log_conversion(udid, mobile_appid, time=datetime.datetime.now())

        if aoe and conversion_logged:
            mp_logging.log(self.request, event=mp_logging.CONV_EVENT, adunit_id=aoe.conversion_adunit, creative_id=aoe.conversion_creative, udid=udid)
            self.response.out.write("ConversionLogged:"+str(conversion_logged)+":"+str(aoe.key())) 
        else:
            self.response.out.write("ConversionLogged:"+str(conversion_logged)) 


class TestHandler(webapp.RequestHandler):
  # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
    def get(self):
        from ad_server.networks.greystripe import GreyStripeServerSide
        from ad_server.networks.millennial import MillennialServerSide
        from ad_server.networks.brightroll import BrightRollServerSide
        from ad_server.networks.jumptap import JumptapServerSide
        from ad_server.networks.mobfox import MobFoxServerSide
        from ad_server.networks.inmobi import InMobiServerSide
        from ad_server.networks.ejam import EjamServerSide
        from ad_server.networks.chartboost import ChartBoostServerSide
        key = self.request.get('id') or 'agltb3B1Yi1pbmNyCgsSBFNpdGUYAgw'
        delay = self.request.get('delay') or '5'
        delay = int(delay)
        adunit = Site.get(key)
        network_name = self.request.get('network','BrightRoll')
        ServerSideKlass = locals()[network_name+"ServerSide"]
        
        
        server_side = ServerSideKlass(self.request,adunit)
        self.response.out.write("URL: %s <br/>PAYLOAD: %s <br/> HEADERS: %s<br/><br/>"%(server_side.url,server_side.payload,server_side.headers))
        
        rpc = urlfetch.create_rpc(delay) # maximum delay we are willing to accept is 1000 ms
        
        payload = server_side.payload
        if payload == None:
            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
        else:
            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)
        
        
        # ... do other things ...
        
        try:
            result = rpc.get_result()
            if result.status_code == 200:
                server_tuple = server_side.bid_and_html_for_response(result)
                bid = server_tuple[0]
                response = server_tuple[1]
                if len(server_tuple) > 2:
                    width = server_tuple[2]
                    height = server_tuple[3]
                else:
                    width = "UNKOWN"
                    height = "UNKOWN"    
                # self.response.out.write(response)
            self.response.out.write("%s<br/> %s %s %s %s"%(server_side.url+'?'+payload if payload else '',bid,response, width, height))
        except urlfetch.DownloadError:
            self.response.out.write("%s<br/> %s"%(server_side.url,"response not fast enough"))
        except Exception, e:
            self.response.out.write("%s <br/> %s"%(server_side.url, e)) 
          
    def post(self):
        trace_logging.info("%s"%self.request.headers["User-Agent"])  
        self.response.out.write("hello world")
        
class PurchaseHandler(webapp.RequestHandler):
    def get(self):
        return self.post()
    
    def post(self):
        from google.appengine.api import taskqueue
        trace_logging.info(self.request.get("receipt"))
        trace_logging.info(self.request.get("udid"))
        mp_logging.log_inapp_purchase(request=self.request,
                                      event=mp_logging.INAPP_EVENT,
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
            InAppPurchaseEventManager().log_inapp_purchase_event(transaction_id=receipt_dict['transaction_id'],
                                                        udid=self.request.get('udid'),
                                                        receipt=simplejson.dumps(receipt_dict),
                                                        time=datetime.datetime.fromtimestamp(float(self.request.get('time'))),
                                                        mobile_appid=self.request.get('mobile_appid'))
        else:
            logging.error("invalid receipt")                                                
                                                        

def main():
    application = webapp.WSGIApplication([('/m/ad', adhandler.AdHandler), 
                                          ('/m/imp', AdImpressionHandler),
                                          ('/m/aclk', AdClickHandler),
                                          ('/m/open', AppOpenHandler),
                                          ('/m/track', AppOpenHandler),
                                          ('/m/test', TestHandler),
                                          ('/m/clear', memcache_mangler.ClearHandler),
                                          ('/m/purchase', PurchaseHandler),
                                          ('/m/purchase_txn', PurchaseHandlerTxn),
                                          ('/m/req',AdRequestHandler),], 
                                          debug=DEBUG)
    run_wsgi_app(application)
    # wsgiref.handlers.CGIHandler().run(application)
    
if __name__ == '__main__':
    main()
