from string import Template   
import random                 
from ad_server.renderers.base_html_renderer import BaseHTMLRenderer

class GreyStripeRenderer(BaseHTMLRenderer):
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
        context.update({"html_data": creative.html_data, "w": format_tuple[0], "h": format_tuple[1]})
        header_context.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
        super(GreyStripeRenderer, cls).network_specific_rendering(header_context, 
                                                                  creative=creative,  
                                                                  format_tuple=format_tuple,
                                                                  context=context,
                                                                  keywords=keywords,
                                                                  adunit=adunit,
                                                                  fail_url=fail_url,
                                                                  **kwargs)
        
        
