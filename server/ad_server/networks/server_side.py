import hashlib
import re

from ad_server.debug_console import trace_logging
from common.utils import helpers


class ServerSide(object):
    base_url = "http://www.test.com/ad?"
    no_pub_id_warning = 'Warning: no %s Publisher ID has been specified'
    pub_id_attr = 'None' # must be specified by sub class
    network_name = 'Generic Server Side'
    
    def __init__(self,request,adunit=None,*args,**kwargs):
        self.request = request
        self.adunit = adunit
    @property
    def format(self):
        return self.adunit.format
  
    def get_udid(self,udid=None):
        """
        udid from the device comes as 
        udid=md5:asdflkjbaljsadflkjsdf (new clients) or
        udid=pqesdlsdfoqeld (old clients)
        For the newer clients we can just pass over the hashed string
        after "md5:"

        For older clients we must md5 hash the udid with salt 
        "mopub-" prepended.

        returns hashed_udid

        """  
        raw_udid = udid or self.request.get('udid')
        raw_udid_parts = raw_udid.split('md5:')

        # if has md5: then just pull out value
        if len(raw_udid_parts) == 2:
            # get the part after 'md5:'
            hashed_udid = raw_udid_parts[-1]
        # else salt the udid and hash it    
        else:
            m = hashlib.md5()
            m.update('mopub-')
            m.update(raw_udid_parts[0])
            hashed_udid = m.hexdigest().upper()
        return hashed_udid    
    def get_ip(self):
        """gets ths ip from either a query parameter or the header"""
        return helpers.get_ip(self.request)
    
    def get_user_agent(self):
        """gets the user agent from either a query paramter or the header"""
        return helpers.get_user_agent(self.request)
        
    def get_pub_id(self,warn=False):
        """ Gets the most specifically defined pub id """
        pub_id = self.adunit.get_pub_id(self.pub_id_attr)
        if warn and not pub_id:
            trace_logging.info(self.no_pub_id_warning%self.network_name)  
        return pub_id

    @property
    def headers(self):
        return {}  

    @property  
    def payload(self):
        return None
        
    def _get_size(self,content):
        width_pat = re.compile(r'width="(?P<width>\d+?)"')
        height_pat = re.compile(r'height="(?P<height>\d+?)"')

        width_match = re.search(width_pat,content)
        height_match = re.search(height_pat,content)

        width = 0
        height = 0
        if height_match and width_match:
            width = int(width_match.groups('width')[0])
            height = int(height_match.groups('height')[0])
        return width,height      

    def bid_and_html_for_response(self,response):
        self.get_pub_id(warn=True) # get the pub id and warn if not present
        if response.status_code == 200:
            response_tuple = list(self.bid_and_html_for_response(response))
            
            # Encode incoming text
            unencoded = response_tuple[1]
            if isinstance(unencoded, basestring):
                  if not isinstance(unencoded, unicode):
                      response_tuple[1] = unicode(unencoded, 'utf-8')
            return tuple(response_tuple)          
        else:    
            trace_logging.info("Failed to load ad from %s"%self.network_name)    
            return None
        
    def bid_and_html_for_response(self, response):
        return 0.0,"<html>BLAH</html>"     
