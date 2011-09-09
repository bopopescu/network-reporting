from string import Template   
import random                 
from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class GreyStripeRenderer(HtmlDataRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                   creative=None,  
                                   format_tuple=None,
                                   context=None,
                                   keywords=None,
                                   adunit=None,
                                   fail_url=None,
                                   track_url=None,
                                   **kwargs):   
        header_context.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
        super(GreyStripeRenderer, cls).network_specific_rendering(header_context, 
                                                                  creative=creative,  
                                                                  format_tuple=format_tuple,
                                                                  context=context,
                                                                  keywords=keywords,
                                                                  adunit=adunit,
                                                                  fail_url=fail_url,
                                                                  track_url=track_url,
                                                                  **kwargs)
        
        
