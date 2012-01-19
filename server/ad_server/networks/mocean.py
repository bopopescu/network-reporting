from ad_server.networks.server_side import ServerSide
from common.utils.decorators import returns_unicode

import cgi
import urllib
import re

from ad_server.debug_console import trace_logging
from ad_server.networks.server_side import ServerSideException  

"""
    mocean is an adserving platform that lets players build on top of them. EJam is built on top of mocean
"""

class MoceanServerSide(ServerSide):
    base_url = "http://r.tapit.com/adrequest.php"
    pub_id_attr = 'mocean_pub_id'
    network_name = 'Mocean'

    @property  
    def payload(self):
        data = {'zone': self.get_pub_id(),
                'ip': self.get_ip(),
                'ua': self.get_user_agent(),
                'format': 'html',
                }
              
        return urllib.urlencode(data)


    @property
    def headers(self): 
        return {}

    @returns_unicode
    def html_for_response(self, response):
        if re.match("^<!--.*--\>$", response.content) == None and len(response.content) != 0:
            trace_logging.warning("Received " + self.network_name + " response: %s"%cgi.escape(response.content))
            return response.content

        trace_logging.info(self.network_name + " failed to return ad")
        raise ServerSideException(self.network_name + " ad is empty")
