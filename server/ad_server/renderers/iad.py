from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class iAdRenderer(BaseNativeRenderer):
    """
    Inheritance Hierarchy:  
    iAdRenderer => BaseNativeRenderer => BaseCreativeRenderer
    """
    def _get_ad_type(self):
        if self.adunit.is_fullscreen():
            return 'iAd_full'
        else:
            return 'iAd'
