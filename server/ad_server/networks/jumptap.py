from ad_server.networks.server_side import ServerSide
from ad_server.debug_console import trace_logging

import re
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
        key_values = {#'gateway-ip': '208.54.5.50',    # TODO: This should be the x-forwarded-for header of the device
                      'hid': self.get_udid(),
                      'client-ip': self.get_ip(), # Test value: 'client-ip': '208.54.5.50'
                      'ua': self.get_user_agent(),
                      'v': 'v29',}
        
        language = self.get_language()
        if language:
            key_values.update(l=language)
        
        # Jumptap uses all levels of pub_ids
        # 'pub' -- Account Level
        # 'site' -- App Level
        # 'spot' -- AdUnit Level
        pub_id = self.adunit.account.network_config.jumptap_pub_id if self.adunit.account.network_config else None
        if pub_id:
            key_values['pub'] = pub_id
        site_id = self.adunit.app.network_config.jumptap_pub_id if self.adunit.app.network_config else None
        if site_id:
            key_values['site'] = site_id
        spot_id = self.adunit.network_config.jumptap_pub_id if self.adunit.network_config else None
        if spot_id:
            key_values['spot'] = spot_id
        return key_values

   
    def get_query_string(self):
        query_string = urllib.urlencode(self.get_key_values())       
        return query_string
    
    def get_language(self):
        LANGUAGE_PAT = re.compile(r' (?P<language>[a-zA-Z][a-zA-Z])[-_][a-zA-Z][a-zA-Z];*[^a-zA-Z0-9-_]')
        m = LANGUAGE_PAT.search(self.get_user_agent())
        if m:
            return m.group('language')
        else:
            return None
    
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
   
    def bid_and_html_for_response(self, response):
        trace_logging.warning("Jumptap response: %s"%cgi.escape(response.content))
        if len(response.content) == 0:
            trace_logging.info("Jumptap ad is empty")
            raise Exception("Jumptap ad is empty")
       
        width, height = self._get_size(response.content)
        return 0.0,"<div style='text-align:center'>"+response.content+"</div>", width, height
