from ad_server.networks.server_side import ServerSide
from ad_server.debug_console import trace_logging

import cgi
import urllib2
import urllib
import logging
from ad_server.networks.server_side import ServerSideException  

class MillennialServerSide(ServerSide):
    base_url = "http://ads.mp.mydas.mobi/getAd.php5"
    pub_id_attr = 'millennial_pub_id'
    network_name = 'Millennial'

    @property    
    def payload(self):
        data = {'apid':self.get_pub_id(),
                'auid':self.get_udid(),
                'uip':self.get_ip(),
                'ua':self.get_user_agent()
                }
        return urllib.urlencode(data)
    
    @property
    def headers(self):
        return {}

    def html_for_response(self, response):
        # TODO: do any sort of manipulation here that we want, like resizing the image, LAME
        # trace_logging.warning("Received Millennial Response: %s"%cgi.escape(response.content).replace('\n',''))fix 
        if len(response.content) == 0 or \
          response.status_code != 200 or \
          '<title>404' in response.content: # **See Note below
            trace_logging.info("Millennial ad is empty")
            raise ServerSideException("Millennial ad is empty")
  
        width, height = self._get_size(response.content)
        return 0.0,"<div style='text-align:center'>"+response.content+"</div>", width, height

