from string import Template
from ad_server.renderers.base_native_renderer import BaseNativeRenderer   
from common.utils import simplejson

class AdMobNativeRenderer(BaseNativeRenderer):
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


        if "full" in adunit.format:
            header_context.add_header("X-Adtype", "interstitial")
            header_context.add_header("X-Fulladtype", "admob_full")
        else:
            header_context.add_header("X-Adtype", str(creative.ad_type))
            header_context.add_header("X-Backfill", str(creative.ad_type))
            header_context.add_header("X-Failurl", fail_url)
            nativecontext_dict = {
                "adUnitID":adunit.get_pub_id("admob_pub_id"),
                "adWidth":adunit.get_width(),
                "adHeight":adunit.get_height()
                }
            header_context.add_header("X-Nativeparams", simplejson.dumps(nativecontext_dict))
        super(AdMobNativeRenderer, cls).network_specific_rendering(header_context, 
                                                                   creative=creative,  
                                                                   format_tuple=format_tuple,
                                                                   context=context,
                                                                   keywords=keywords,
                                                                   adunit=adunit,
                                                                   **kwargs)
        
    TEMPLATE = Template("""admob native sdk""")
