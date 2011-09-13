from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class iAdRenderer(BaseNativeRenderer):

    def _get_ad_type(self):
        return 'iAd'
