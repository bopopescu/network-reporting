from string import Template
from ad_server.renderers.base_native_renderer import BaseNativeRenderer   
from common.utils import simplejson

class CustomNativeRenderer(BaseNativeRenderer):
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
        creative.html_data = creative.html_data.rstrip(":")
        context.update({"method": creative.html_data})
        header_context.add_header("X-Adtype", "custom")
        header_context.add_header("X-Customselector",creative.html_data)
        super(CustomNativeRenderer, cls).network_specific_rendering(header_context, 
                                                                    creative=None,  
                                                                    format_tuple=None,
                                                                    context=None,
                                                                    keywords=None,
                                                                    adunit=None,
                                                                    **kwargs)

        

    TEMPLATE = Template('custom selector: $method')
