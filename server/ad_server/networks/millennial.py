from ad_server.networks.server_side import ServerSide
from ad_server.debug_console import trace_logging

import cgi
import urllib2
import urllib
import logging

class MillennialServerSide(ServerSide):
    base_url = "http://ads.mp.mydas.mobi/getAd.php5"
    pub_id_attr = 'millenial_pub_id'
    network_name = 'Millennial'
    
          
    def get_key_values(self):
        return {'apid':self.get_pub_id(),
                'auid':self.get_udid(),
                'uip':self.get_ip(),
                'ua':self.get_user_agent()}
      
    @property
    def url(self):
        return self.base_url + '?' + urllib.urlencode(self.get_key_values())

    @property    
    def payload(self):
        return None
        
    def get_pub_id(self,warn=False):
        if self.adunit.millennial_site_id:
            pub_id = self.adunit.millennial_site_id
        elif self.adunit.app.millennial_app_id:
            pub_id = self.adunit.millennial_app_id
        else:    
            pub_id = self.get_account().millenial_pub_id    
        if warn and not pub_id:
            trace_logging.info(self.no_pub_id_warning%self.network_name)  
        return pub_id

    # def get_user_agent(self):
    #     return "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7"
  
    def _bid_and_html_for_response(self,response):
      # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
        trace_logging.warning("Received Millennial Response: %s"%cgi.escape(response.content))
        if len(response.content) == 0 or \
          response.status_code != 200 or \
          '<title>404' in response.content: # **See Note below
            trace_logging.info("Millenial ad is empty")
            raise Exception("Millenial ad is empty")
  
        width, height = self._get_size(response.content)
        return 0.0,"<div style='text-align:center'>"+response.content+"</div>", width, height


# **
# On March 4, we were getting the following response
# from millenial. This doesn't really makes sense,
# but the above <title>404 check is intended to block 
# this type of response
#
# <!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
# <html><head>
# <title>404 Not Found</title>
# </head><body>
# <h1>Not Found</h1>
# <p>The requested URL /rich/T/test/ipad/728.php was not found on this server.</p>
# </body></html>        
