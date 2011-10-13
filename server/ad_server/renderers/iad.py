from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class iAdRenderer(BaseNativeRenderer):
    """
    Inheritance Hierarchy:  
    iAdRenderer => BaseNativeRenderer => BaseCreativeRenderer
    """
    def _get_ad_type(self):
        return 'iAd'
