import random                 
from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class BaseNativeRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    @classmethod
    def network_specific_rendering(cls, header_context, **kwargs):
        pass
                                   
