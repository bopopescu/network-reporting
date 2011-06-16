from ad_server.networks.server_side import ServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.mobfox import MobFoxServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.ejam import EjamServerSide
from ad_server.networks.chartboost import ChartBoostServerSide

from google.appengine.api import urlfetch
from google.appengine.ext import webapp

from publisher.models import AdUnit

class TestHandler(webapp.RequestHandler):
    def get(self):
        # get parameters from URL
        key = self.request.get('id') or 'agltb3B1Yi1pbmNyCgsSBFNpdGUYAgw'
        delay = self.request.get('delay') or '5'
        delay = int(delay)
        adunit = AdUnit.get(key)
        network_name = self.request.get('network','MobFox')
        
        # get the appropriate network adapter
        ServerSideKlass = globals()[network_name+"ServerSide"]
    
        server_side = ServerSideKlass(self.request,adunit)
        self.response.out.write("URL: %s <br/>PAYLOAD: %s <br/> HEADERS: %s<br/><br/>"%(server_side.url,server_side.payload,server_side.headers))
    
        rpc = urlfetch.create_rpc(delay) # maximum delay we are willing to accept is 5000 ms

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
                self.response.out.write("%s<br/> %s %s %s %s"%(server_side.url+'?'+payload if payload else '',bid,response, width, height))
        except urlfetch.DownloadError:
            self.response.out.write("%s<br/> %s"%(server_side.url,"response not fast enough"))
        except Exception, e:
            self.response.out.write("%s <br/> %s"%(server_side.url, e)) 
      
    def post(self):
        logging.info("%s"%self.request.headers["User-Agent"])  
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