from string import Template
from ad_server.renderers.base_native_renderer import BaseNativeRenderer   
from common.utils import simplejson

class iAdRenderer(BaseNativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                        creative=None,  
                                        format_tuple=None,
                                        context=None,
                                        keywords=None,
                                        adunit=None,
                                        fail_url=None,
                                        **kwargs):            
        # header_context.add_header("X-Adtype","custom")
        # header_context.add_header("X-Backfill","alert")
        # header_context.add_header("X-Nativecontext",'{"title":"MoPub Alert View","cancelButtonTitle":"No Thanks","message":"We\'ve noticed you\'ve enjoyed playing Angry Birds.","otherButtonTitle":"Rank","clickURL":"mopub://inapp?id=pixel_001"}')
        # header_context.add_header("X-Customselector","customEventTest")
        if "full" in adunit.format:
            header_context.add_header("X-Adtype", "interstitial")
            header_context.add_header("X-Fulladtype", "millennial_full")
        else:
            header_context.add_header("X-Adtype", str(creative.ad_type))
            header_context.add_header("X-Backfill", str(creative.ad_type))
        header_context.add_header("X-Failurl", fail_url)
        nativecontext_dict = {
            "adUnitID":adunit.get_pub_id("millennial_pub_id"),
            "adWidth":adunit.get_width(),
            "adHeight":adunit.get_height()
        }
        header_context.add_header("X-Nativecontext", simplejson.dumps(nativecontext_dict))                  
        super(iAdRenderer, cls).network_specific_rendering(header_context, 
                                                                        creative=None,  
                                                                        format_tuple=None,
                                                                        context=None,
                                                                        keywords=None,
                                                                        adunit=None,
                                                                        **kwargs)



    TEMPLATE = Template('iAd')
