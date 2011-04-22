from ad_server.networks.server_side import ServerSide
import logging
import urllib
import urllib2

from xml.dom import minidom
from ad_server.debug_console import trace_logging

class AdMobServerSide(ServerSide):
    base_url = None
    pub_id_attr = 'admob_pub_id'
    network_name = 'AdMob'

    def __init__(self,request,adunit=None,*args,**kwargs):
        return super(AdMobServerSide,self).__init__(request,adunit,*args,**kwargs)

    @property
    def url(self):
        return None

    @property  
    def payload(self):
        data = {'rt': 'api',
                'u': self.get_user_agent(),
                'i': self.get_ip(),
                'o': self.get_udid(),
                'm': 'live',
                's': self.get_pub_id(),
                # 'longitude': , # long
                # 'latitude': , # lat
                # 'int_cat': , # MobFox category type
                'v': 'api_mopub',
              }
              
        return urllib.urlencode(data) + '&' + self._add_extra_headers()

    def _bid_and_html_for_response(self,response):
        return 0.0, content
        
