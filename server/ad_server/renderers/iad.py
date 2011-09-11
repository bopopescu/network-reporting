from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class iAdRenderer(BaseNativeRenderer):
    """ For now, just do the standard """

    def _get_ad_type(self):
        return 'iAd'