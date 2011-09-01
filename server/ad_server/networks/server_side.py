import re

from ad_server.debug_console import trace_logging
from common.utils import helpers
from common.utils.decorators import returns_unicode       
from google.appengine.api import urlfetch


class ServerSide(object):
    base_url = "http://www.test.com/ad?"
    no_pub_id_warning = 'Warning: no %s Publisher ID has been specified'
    pub_id_attr = 'None' # Must be specified by sub class
    network_name = 'Generic Server Side'
    SERVER_TIMEOUT = 2 # We time out after 2000 ms
    
    def __init__(self, client_context, adunit, *args, **kwargs):
        self.client_context = client_context
        self.adunit = adunit    
        self.rpc
        rpc = urlfetch.create_rpc(self.SERVER_TIMEOUT)

    @property
    def headers(self): 
        """ The payload that we send to the ad network when making our request """
        raise NotImplementedError

    @property  
    def payload(self):
        """ The payload that we send to the ad network when making our request """
        raise NotImplementedError
    
    
    def make_call_and_get_html_from_response(self):   
        """ When we don't need to do any asynchronous processing while
            we wait for a result, we can call this function. """
        self.make_fetch_call()
        response = self.get_result()
        return html_for_response(response)
    
    def make_fetch_call(self): 
        """ Initiates the rpc to get the html from the network. Result is 
            accessed with get_html_from_result"""
        if self.payload == None:
            urlfetch.make_fetch_call(self.rpc, 
                                     self.url, 
                                     headers=self.headers)
        else:
            urlfetch.make_fetch_call(self.rpc, 
                                     self.url, 
                                     headers=self.headers, 
                                     method=urlfetch.POST, 
                                     payload=self.payload)
        
        
    def get_result(self):  
        """ Called after make_fetch_call. Waits for callback to resolve and then
            returns the html provided by the network. Returns a response object """ 
        return self.rpc.get_result()
    
    @returns_unicode
    def html_for_response(self, response): 
        raise NotImplementedError  
        
        # Here is an example html parsing
        
        self.get_pub_id(warn=True) # get the pub id and warn if not present
        if response.status_code == 200:
            return "<html>BLAH</html>"       
        else:    
            trace_logging.info("Failed to load ad from %s"%self.network_name)    
            return None

 
 
    # TODO: MAKE THESE HELPER METHODS PRIVATE
    @property
    def format(self):
        return self.adunit.format  

    def get_ip(self):
        """ Gets the client's ip from either a query parameter or the header"""   
        return self.client_context.client_ip

    def get_user_agent(self):
        """gets the user agent from either a query paramter or the header"""
        return self.client_context.user_agent

    def get_pub_id(self, warn=False):
        """ Gets the most specifically defined pub id """
        pub_id = self.adunit.get_pub_id(self.pub_id_attr)
        if warn and not pub_id:
            trace_logging.info(self.no_pub_id_warning%self.network_name)  
        return pub_id
     
        
    def _get_size(self, content):
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




