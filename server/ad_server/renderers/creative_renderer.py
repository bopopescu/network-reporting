from ad_server.debug_console import trace_logging   
import random  
import re      
import urllib

import time                        
from ad_server.renderers.header_context import HeaderContext
 
class BaseCreativeRenderer(object):  
    """ Probides basic interface for renderers. """
    
    TEMPLATE = None
    
    def __init__(self, creative,
                       adunit,
                       udid,
                       now,
                       request_host,
                       request_url,
                       request_id,
                       version,
                       on_fail_exclude_adgroups,
                       keywords=None,
                       random_val=None): 
        self.creative = creative
        self.adunit = adunit
        self.udid = udid
        self.keywords = keywords or []
        
        self.now = now
        self.request_host = request_host
        self.request_url = request_url
        self.request_id = request_id
        self.version = version
        self.tried_adgroups = on_fail_exclude_adgroups               
        self.random_val = random_val or random.random() 
        self.fail_url = _build_fail_url(request_url, on_fail_exclude_adgroups)
        self.impression_url, self.click_url = self._get_imp_and_click_url()

        self.header_context = HeaderContext()
        self.rendered_creative = None

    def render(self, version_number=None):
        version_number = version_number # quiet PyLint
        self.log_winner()

        self._setup_headers()
        self._setup_content()

        return self.rendered_creative, self.header_context
    
    def _get_imp_and_click_url(self):
        appid = self.creative.conv_appid or ''
        request_time = time.mktime(self.now.timetuple())
        
        params = {'id': self.adunit.key(),
                  'cid': self.creative.key(),
                  'c': self.creative.key(),
                  'req': self.request_id,
                  'reqt': request_time,
                  'udid': self.udid,
                  'appid': appid,}

        get_query = urllib.urlencode(params)     
        ad_click_url = "http://" + self.request_host + "/m/aclk" + "?" \
                            + get_query
        track_url = "http://" + self.request_host + "/m/imp" + "?" \
                            + get_query
        
        cost_tracker = "&rev=%.07f" 
        if self.creative.adgroup.bid_strategy == 'cpm':
            price_per_imp = (float(self.creative.adgroup.bid)/1000)
            cost_tracker = cost_tracker % price_per_imp
            track_url += cost_tracker
        elif self.creative.adgroup.bid_strategy == 'cpc':
            cost_tracker = cost_tracker % self.creative.adgroup.bid
            ad_click_url += cost_tracker
        return track_url, ad_click_url

    def _setup_headers(self):
        if self.adunit.is_fullscreen():
            self.header_context.add_header("X-Adtype", "interstitial")
            self.header_context.add_header("X-Fulladtype", self._get_ad_type())
        else:
            self.header_context.add_header("X-Adtype", self._get_ad_type())    
        
        self.header_context.add_header("X-Clickthrough", 
                                       str(self.click_url))   
        # add creative ID for testing (also prevents that one 
        # bad bug from happening)
        self.header_context.add_header("X-Creativeid", 
                                       "%s" % self.creative.key())
        self.header_context.add_header("X-Imptracker", 
                                       str(self.impression_url))
        # pass the creative height and width if they are explicity set
        trace_logging.warning("creative size:%s" % self.creative.format)
        if self.creative.width and self.creative.height \
          and not self.adunit.is_fullscreen():
            self.header_context.add_header("X-Width", 
                                           str(self.creative.width))
            self.header_context.add_header("X-Height", 
                                           str(self.creative.height))
    
        # adds network info to the header_context
        if self.creative.adgroup.network_type:
            self.header_context.add_header("X-Networktype", 
                                    self.creative.adgroup.network_type)

        if self.creative.launchpage:
            self.header_context.add_header("X-Launchpage", 
                                    self.creative.launchpage)
            
    def _get_ad_type(self):
        raise NotImplementedError
        
    def _setup_content(self):
        raise NotImplementedError
        
    def log_winner(self):
        trace_logging.info("##############################")
        trace_logging.info("##############################")
        trace_logging.info("Winner found, rendering: %s" % \
                            self.creative.name.encode('utf8') \
                                if self.creative.name else 'None')
        trace_logging.warning("Creative key: %s" \
                                % str(self.creative.key()))
        trace_logging.warning("rendering: %s" % self.creative.ad_type)


########### HELPER FUNCTIONS ############

# def _make_format_tuple_and_set_orientation(adunit,
#                                            creative,
#                                            header_context):
#     """ Sets orientation appropriately. REFACTOR clean this up"""
# 
#     format = adunit.format.split('x')
#     if len(format) < 2:
#         ####################################
#         # HACK FOR TUNEWIKI
#         # TODO: We should make this smarter
#         # if the adtype is not html (e.g. image)
#         # then we set the orientation to only landscape
#         # and the format to 480x320
#         ####################################
#         if not creative.ad_type == "html":
#             if adunit.landscape:
#                 header_context.add_header("X-Orientation","l")
#                 format = ("480","320")
#             else:
#                 header_context.add_header("X-Orientation","p")
#                 format = (320,480)    
#                                         
#         elif not creative.adgroup.network_type \
#           or creative.adgroup.network_type in FULL_NETWORKS:
#             format = (320,480)
#         elif creative.adgroup.network_type:
#             #TODO this should be a littttleee bit smarter. 
#             # This is basically saying default
#             #to 300x250 if the adunit is a full (of some kind) 
#             #and the creative is from
#             #an ad network that doesn't serve fulls
#             if adunit.landscape:
#                 header_context.add_header("X-Orientation","l")
#             else:
#                 header_context.add_header("X-Orientation","p")
#             format = (300, 250)
#             
#     return format

def _build_fail_url(original_url, on_fail_exclude_adgroups):
    """ Remove all the old &exclude= substrings and replace them with 
    our new ones 
    """
    clean_url = re.sub("&exclude=[^&]*", "", original_url)

    if not on_fail_exclude_adgroups:
        return clean_url
    else:
        return clean_url + '&exclude=' + '&exclude='.join(on_fail_exclude_adgroups)
 

