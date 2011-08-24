from ad_server.renderers import TEMPLATES
from ad_server.debug_console import trace_logging   
import random  
import re      

from google.appengine.api.images import InvalidBlobKeyError         
from google.appengine.api import images     
from common.utils import simplejson  
from common.constants import FULL_NETWORKS 
import time                        
from ad_server.renderers.header_context import HeaderContext
 
class BaseCreativeRenderer(object):  
    """ Probides basic interface for renderers. """
    
    TEMPLATE = ""
    
    @classmethod
    def network_specific_rendering(cls, header_context, **kwargs):
        """ Stub method to be overwritten"""
        pass
    
    @classmethod
    def render(cls, now=None,
                    creative=None, 
                    adunit=None, 
                    keywords=None,
                    request_host=None,
                    request_url=None,   
                    version_number=None,
                    ad_click_url=None,
                    track_url=None,
                    on_fail_exclude_adgroups=None,
                    random_val=random.random()):   
                    
        header_context = HeaderContext()
        # rename network so its sensical
        if creative.adgroup.network_type:
            creative.name = creative.adgroup.network_type
                      


        trace_logging.info("##############################")
        trace_logging.info("##############################")
        trace_logging.info("Winner found, rendering: %s" % creative.name.encode('utf8') if creative.name else 'None')
        trace_logging.warning("Creative key: %s" % str(creative.key()))
        trace_logging.warning("rendering: %s" % creative.ad_type)
        


             
        header_context.add_header("X-Clickthrough", str(ad_click_url)) 
    
  
        # add creative ID for testing (also prevents that one bad bug from happening)
        header_context.add_header("X-Creativeid", "%s" % creative.key())

        
        header_context.add_header("X-Imptracker", str(track_url))


        template_name = creative.ad_type    
        
        format_tuple, network_center = _make_format_tuple_and_set_orientation(adunit, creative, header_context)
        
         
        # Build fail url
        fail_url = _build_fail_url(request_url, on_fail_exclude_adgroups)
        
        context = {}
        
        context.update(creative.__dict__.get("_entity"))
        #Line1/2 None check biznass 
        if context.has_key('line1'):
            if context['line1'] is None:
                context['line1'] = ''
        if context.has_key('line2'):
            if context['line2'] is None:
                context['line2'] = ''
        #centering non-full ads in fullspace
        if network_center: 
            #css to center things
            style = "<style type='text/css'> \
                          .network_center { \
                              position: fixed; \
                              top: 50%%; \
                              left: 50%%; \
                              margin-left: -%dpx !important; \
                              margin-top: -%dpx !important; \
                              } \
                      </style>"  
            context.update({'network_style': style % tuple(a/2 for a in format_tuple)})
        else:
            context.update({'network_style':''})
        #success tracking pixel for admob
        #set up an invisible span
        hidden_span = 'var hid_span = document.createElement("span"); hid_span.setAttribute("style", "display:none");'
        #init an image, give it the right src url, pixel size, append to span
        tracking_pix = 'var img%(name)s = document.createElement("img"); \
                        img%(name)s.setAttribute("height", 1); \
                        img%(name)s.setAttribute("width", 1);\
                        img%(name)s.setAttribute("src", "%(src)s");\
                        hid_span.appendChild(img%(name)s);'
      
        # because we send the client the HTML, and THEN send requests to admob for content, just becaues our HTML 
        # (in this case the tracking pixel) works, DOESNT mean that admob has successfully returned a creative.
        # Because of the admob pixel has to be added AFTER the admob ad actually loads, this is done via javascript.

        success = hidden_span
        success += tracking_pix % dict(name = 'first', src = track_url)           
        
        
        
        # We need randomness in order to keep clients from caching impression pixels
        if creative.tracking_url:
            creative.tracking_url += '&random=%s' % random_val
            success += tracking_pix % dict(name = 'second', src = creative.tracking_url) 
            context.update(trackingPixel='<span style="display:none;"><img src="%s"/><img src="%s"/></span>'% (creative.tracking_url, track_url))
        else:
            context.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>' % track_url)
        success += 'document.body.appendChild(hid_span);'
        
        
        cls.network_specific_rendering(header_context, 
                                       creative=creative, 
                                       adunit=adunit, 
                                       keywords=keywords,
                                       request_host=request_host,
                                       request_url=request_url,   
                                       version_number=version_number,
                                       track_url=track_url,                                 
                                       context=context,
                                       format_tuple=format_tuple,
                                       random_val=random_val,
                                       fail_url=fail_url,
                                       success=success
                                       )

        if creative.ad_type == "greystripe":
            context.update({"html_data": creative.html_data, "w": format_tuple[0], "h": format_tuple[1]})
            header_context.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
            template_name = "html"

        
        elif creative.ad_type == "html":
            pass

        
        elif creative.ad_type == "html_full":
            pass
        elif creative.ad_type == "text":  
            header_context.add_header("X-Productid","pixel_001")
      
      
        if version_number >= 2:  
            context.update(finishLoad='<script>function mopubFinishLoad(){window.location="mopub://finishLoad";}</script>')
            # extra parameters used only by admob template
            #add in the success tracking pixel
            context.update(admob_finish_load= success + 'window.location = "mopub://finishLoad";')
            context.update(admob_fail_load='window.location = "mopub://failLoad";')
        else:
            # don't use special url hooks because older clients don't understand    
            context.update(finishLoad='')
            # extra parameters used only by admob template
            context.update(admob_finish_load=success)
            context.update(admob_fail_load='')
    
        # indicate to the client the winning creative type, in case it is natively implemented (iad, clear)
    
        if str(creative.ad_type) == "iAd":
            # header_context.add_header("X-Adtype","custom")
            # header_context.add_header("X-Backfill","alert")
            # header_context.add_header("X-Nativecontext",'{"title":"MoPub Alert View","cancelButtonTitle":"No Thanks","message":"We\'ve noticed you\'ve enjoyed playing Angry Birds.","otherButtonTitle":"Rank","clickURL":"mopub://inapp?id=pixel_001"}')
            # header_context.add_header("X-Customselector","customEventTest")
            if "full_tablet" in adunit.format:
                header_context.add_header("X-Adtype", "interstitial")
                header_context.add_header("X-Fulladtype", "iAd_full")
            else:
                header_context.add_header("X-Adtype", str(creative.ad_type))
                header_context.add_header("X-Backfill", str(creative.ad_type))
        
            header_context.add_header("X-Failurl", fail_url)

        elif str(creative.ad_type) == "admob_native":
            if "full" in adunit.format:
                header_context.add_header("X-Adtype", "interstitial")
                header_context.add_header("X-Fulladtype", "admob_full")
            else:
                header_context.add_header("X-Adtype", str(creative.ad_type))
                header_context.add_header("X-Backfill", str(creative.ad_type))
            header_context.add_header("X-Failurl", _build_fail_url(request_url, on_fail_exclude_adgroups))
            nativecontext_dict = {
                "adUnitID":adunit.get_pub_id("admob_pub_id"),
                "adWidth":adunit.get_width(),
                "adHeight":adunit.get_height()
            }
            header_context.add_header("X-Nativecontext", simplejson.dumps(nativecontext_dict))
        elif creative.ad_type == "millennial_native":
            pass                     
        elif creative.ad_type == "custom_native":
            pass
        else:
            header_context.add_header("X-Adtype", str('html'))
      
    
        # pass the creative height and width if they are explicity set
        trace_logging.warning("creative size:%s"%creative.format)
        if creative.width and creative.height and 'full' not in adunit.format:
            header_context.add_header("X-Width", str(creative.width))
            header_context.add_header("X-Height", str(creative.height))
    
        # adds network info to the header_context
        if creative.adgroup.network_type:
            header_context.add_header("X-Networktype",creative.adgroup.network_type)

        if creative.launchpage:
            header_context.add_header("X-Launchpage", creative.launchpage)
    
        # render the HTML body    

        if cls.TEMPLATE:   
            rendered_creative = cls.TEMPLATE.safe_substitute(context) 
        else:    
            rendered_creative = TEMPLATES[template_name].safe_substitute(context)
        rendered_creative.encode('utf-8')
    
    
        return rendered_creative, header_context              

        

########### HELPER FUNCTIONS ############     

def _make_format_tuple_and_set_orientation(adunit,
                       creative,
                       header_context):
    """ Sets orientation appropriately. REFACTOR clean this up"""                   
                       
    format = adunit.format.split('x')
    network_center = False
    if len(format) < 2:
        ####################################
        # HACK FOR TUNEWIKI
        # TODO: We should make this smarter
        # if the adtype is not html (e.g. image)
        # then we set the orientation to only landscape
        # and the format to 480x320
        ####################################
        if not creative.ad_type == "html":
            if adunit.landscape:
                header_context.add_header("X-Orientation","l")
                format = ("480","320")
            else:
                header_context.add_header("X-Orientation","p")
                format = (320,480)    
                                        
        elif not creative.adgroup.network_type or creative.adgroup.network_type in FULL_NETWORKS:
            format = (320,480)
        elif creative.adgroup.network_type:
            #TODO this should be a littttleee bit smarter. This is basically saying default
            #to 300x250 if the adunit is a full (of some kind) and the creative is from
            #an ad network that doesn't serve fulls
            network_center = True
            if adunit.landscape:
                header_context.add_header("X-Orientation","l")
            else:
                header_context.add_header("X-Orientation","p")
            format = (300, 250)
            
    return format, network_center

def _build_fail_url(original_url, on_fail_exclude_adgroups):
    """ Remove all the old &exclude= substrings and replace them with our new ones """
    clean_url = re.sub("&exclude=[^&]*", "", original_url)

    if not on_fail_exclude_adgroups:
        return clean_url
    else:
        return clean_url + '&exclude=' + '&exclude='.join(on_fail_exclude_adgroups)
 

