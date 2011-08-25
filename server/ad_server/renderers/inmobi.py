from string import Template   
import random                 
from ad_server.renderers.base_html_renderer import BaseHTMLRenderer

class InmobiRenderer(BaseHTMLRenderer):
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
        
        
        # add the launchpage header for inmobi in case they have dynamic ads that use
        # window.location = 'http://some.thing/asdf'
        if creative.adgroup.network_type == "inmobi":
            header_context.add_header("X-Launchpage","http://c.w.mkhoj.com")
            
        super(InmobiRenderer, cls).network_specific_rendering(header_context, 
                                                              creative=creative,  
                                                              format_tuple=format_tuple,
                                                              context=context,
                                                              keywords=keywords,
                                                              adunit=adunit,
                                                              **kwargs)
                    
    
