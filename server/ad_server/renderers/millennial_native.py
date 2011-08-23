from string import Template
from ad_server.renderers.creative_renderer import BaseCreativeRenderer   
from common.utils import simplejson

class MillennialNativeRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, headers, 
                                        creative=None,  
                                        format_tuple=None,
                                        context=None,
                                        keywords=None,
                                        adunit=None,
                                        fail_url=None,
                                        **kwargs):            
        if "full" in adunit.format:
            headers.add_header("X-Adtype", "interstitial")
            headers.add_header("X-Fulladtype", "millennial_full")
        else:
            headers.add_header("X-Adtype", str(creative.ad_type))
            headers.add_header("X-Backfill", str(creative.ad_type))
        headers.add_header("X-Failurl", fail_url)
        nativecontext_dict = {
            "adUnitID":adunit.get_pub_id("millennial_pub_id"),
            "adWidth":adunit.get_width(),
            "adHeight":adunit.get_height()
        }
        headers.add_header("X-Nativecontext", simplejson.dumps(nativecontext_dict))                  
    
    TEMPLATE = Template("""millennial native sdk""")
