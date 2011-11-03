import hashlib, datetime

from ad_server.networks.server_side import ServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.mobfox import MobFoxServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.ejam import EjamServerSide
from ad_server.networks.chartboost import ChartBoostServerSide

from common.utils import simplejson

from google.appengine.api import urlfetch
from google.appengine.ext import webapp

from publisher.models import AdUnit 

from ad_server.auction.client_context import ClientContext    

class TestHandler(webapp.RequestHandler):
    def get(self):
        try:
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
            adunit = AdUnit.get(key)
            network_name = self.request.get('network','BrightRoll')
            ServerSideKlass = locals()[network_name+"ServerSide"]
            
            client_context = ClientContext(adunit=adunit,
                                           keywords=None,
                                           country_code="US",
                                           excluded_adgroup_keys=[],
                                           raw_udid="FakeUDID", 
                                           ll=None,
                                           request_id=None,
                                           now=datetime.datetime.now(),
                                           user_agent='Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7',        
                                           experimental=False)
    
            server_side = ServerSideKlass(client_context, adunit)
            self.response.out.write("URL: %s <br/>PAYLOAD: %s <br/> HEADERS: %s<br/><br/>"%(server_side.url, server_side.payload, server_side.headers))
    
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
                    html = server_side.html_for_response(result)

                    # self.response.out.write(response)
                    self.response.out.write("%s<br/> %s"%(server_side.url+'?'+payload if payload else '', html))
                else:
                    self.response.out.write("status: %s"%result.status_code)    
            except urlfetch.DownloadError:
                self.response.out.write("%s<br/> %s"%(server_side.url,"response not fast enough"))
            except Exception, e:
                self.response.out.write("%s <br/> %s"%(server_side.url, e)) 
        except Exception, e:
            self.response.out.write("%s <br/> %s"%("Exception:", e)) 
          
    def post(self):
        trace_logging.info("%s"%self.request.headers["User-Agent"])  
        self.response.out.write("hello world")
        
class UDIDHandler(webapp.RequestHandler):
    def get(self):
        raw_udid = self.request.get('udid',None)
        if not raw_udid:
            self.response.out.write("Provide a raw udid")
            return
        ss = ServerSide(None)
        mopub_hashed_udid = ss.get_udid(raw_udid)
        self.response.out.write("MoPub ID: md5:%s"%mopub_hashed_udid)
        
        
class MPXUDIDHandler(webapp.RequestHandler):
    bidder_dict = {'mopubsample':"ein39vuvya",
                   'tapad':"ieir8bhbxll",
                   'adsymptotic':"otwbcmbuty",
                   'mopubsampletornado':"do20t8bhc7g9",
                   'tapsense': "asf45kdlezy",
                   'mdotm': "ak5cdoz55w",
                  }
    
    
    def post(self):
        return self.get()
    
    def get(self):
        udid_list = self.request.get_all('udid', None)
        bidder = self.request.get('bidder', None)
        response_dict = {}
        if bidder and bidder in self.bidder_dict and udid_list:
            for udid in udid_list:
                md5_udid = hashlib.md5('mopub-'+udid).hexdigest().upper()
                sha1_udid = hashlib.sha1('mopub-'+udid).hexdigest().upper() 
                sha_udid = hashlib.sha1(udid).hexdigest().upper()
                possible_udids = [udid, md5_udid, sha1_udid, sha_udid]
                possible_bidder_mpids = [hashlib.sha1(self.bidder_dict[bidder]+pudid).hexdigest().upper() 
                                            for pudid in possible_udids ]
                response_dict[udid] = possible_bidder_mpids                                
                    
        else:
            response_dict.update(error="No real bidder and/or udids provided")    
        
        self.response.out.write(simplejson.dumps(response_dict))
