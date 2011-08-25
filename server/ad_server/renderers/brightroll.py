from string import Template   
import random                 
from ad_server.renderers.base_html_renderer import BaseHTMLRenderer

class BrightRollRenderer(BaseHTMLRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, 
                                   creative=None,  
                                   format_tuple=None,
                                   context=None,
                                   keywords=None,
                                   adunit=None,
                                   fail_url=None,
                                   success=None,
                                   network_center=None,
                                   **kwargs):   
        html_data = creative.html_data.replace(r'%(track_pixels)s',success)
        context.update(html_data=html_data)
        header_context.add_header("X-Scrollable","1")
        header_context.add_header("X-Interceptlinks","0")
        super(BrightRollRenderer, cls).network_specific_rendering(header_context, 
                                                                  creative=creative,  
                                                                  format_tuple=format_tuple,
                                                                  context=context,
                                                                  keywords=keywords,
                                                                  adunit=adunit,
                                                                  fail_url=fail_url,
                                                                  success=success,
                                                                  network_center=network_center,
                                                                  **kwargs)
                

    TEMPLATE = Template('$html_data')
