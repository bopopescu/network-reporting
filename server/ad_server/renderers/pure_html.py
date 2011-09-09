from string import Template   
import random                 
from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class PureHTMLRenderer(HtmlDataRenderer):
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
        # must pass in parameters to fully render template
        # TODO: NOT SURE WHY I CAN'T USE: html_data = c.html_data % dict(track_pixels=success)
            
        super(PureHTMLRenderer, cls).network_specific_rendering(header_context, 
                                                                creative=creative,  
                                                                format_tuple=format_tuple,
                                                                context=context,
                                                                keywords=keywords,
                                                                adunit=adunit,
                                                                success=success,
                                                                network_center=network_center,
                                                                **kwargs)
                

    TEMPLATE = Template("$html_data")
