from string import Template
import random                 
from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class BaseHtmlRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                   creative=None,  
                                   format_tuple=None,
                                   context=None,
                                   keywords=None,
                                   adunit=None,
                                   fail_url=None,
                                   request_host=None,
                                   track_url=None,
                                   network_center=None,
                                   success=None,
                                   **kwargs):   
        header_context.add_header("X-Adtype", str('html'))
        if 'full' in adunit.format:
            context['trackingPixel'] = ""
            trackImpressionHelper = "<script>\nfunction trackImpressionHelper(){\n%s\n}\n</script>"%success
            context.update(trackImpressionHelper=trackImpressionHelper)
        else:
            context['trackImpressionHelper'] = ''    
                

