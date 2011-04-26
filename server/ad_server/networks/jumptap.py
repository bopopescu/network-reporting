from ad_server.networks.server_side import ServerSide
from ad_server.debug_console import trace_logging

import cgi
import urllib
import urllib2
import string
import logging

class JumptapServerSide(ServerSide):
    base_url = "http://a.jumptap.com/a/ads" # live
    pub_id_attr = 'jumptap_pub_id'
    no_pub_id_warning = 'Warning: no %s Publisher Alias has been specified'
    network_name = 'Jumptap'
   
   
    def get_key_values(self):
        key_values = {'pub': self.get_account().jumptap_pub_id,
                      #'gateway-ip': '208.54.5.50',    # TODO: This should be the x-forwarded-for header of the device
                      'hid': self.get_udid(),
                      'client-ip': self.get_ip(), # Test value: 'client-ip': '208.54.5.50'
                      'v': 'v29' }
        if self.adunit.app.jumptap_app_id:
            key_values['site'] = self.adunit.app.jumptap_app_id
        if self.adunit.jumptap_site_id:
            key_values['spot'] = self.adunit.jumptap_site_id
        return key_values
   
    def get_query_string(self):
        query_string = urllib.urlencode(self.get_key_values())       
        return query_string
   
    @property
    def url(self):
        return self.base_url + '?' + self.get_query_string()
   
    @property
    def headers(self):
        return { 'User-Agent': self.get_user_agent() }
               #'Accept-Language': 'en-us' }  # TODO: Accept language from web request
   
    def get_response(self):
        req = urllib2.Request(self.url)
        response = urllib2.urlopen(req)
        return response.read()
   
    def _bid_and_html_for_response(self,response):
        trace_logging.warning("Jumptap response: %s"%cgi.escape(response.content))
        if len(response.content) == 0:
            trace_logging.info("Jumptap ad is empty")
            raise Exception("Jumptap ad is empty")
       
        width, height = self._get_size(response.content)
       
        return 0.0,"<div style='text-align:center'>"+response.content+"</div>", width, height
