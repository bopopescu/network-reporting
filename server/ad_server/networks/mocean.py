from ad_server.networks.server_side import ServerSide

import cgi
import urllib
import re

from ad_server.debug_console import trace_logging


class MoceanServerSide(ServerSide):
    base_url = "http://ads.mocean.mobi/ad"
    pub_id_attr = 'mocean_pub_id'
    network_name = 'Mocean'

    @property
    def url(self):
        data =	{'zone': self.get_pub_id(), 'ip': self.get_ip(), 'ua': self.get_user_agent(), }
        return self.base_url + "?" + urllib.urlencode(data)

    def _bid_and_html_for_response(self,response):
        if re.match("^<!--.*--\>$", response.content) == None and len(response.content) != 0:
            trace_logging.warning("Received " + self.network_name + " response: %s"%cgi.escape(response.content))
            return 0.0, "<div style='text-align:center'>"+response.content+"</div>"
        trace_logging.info(self.network_name + " failed to return ad")
        raise Exception(self.network_name + " ad is empty")