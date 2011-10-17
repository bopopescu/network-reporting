from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class CustomNativeRenderer(BaseNativeRenderer):
    """
    Inheritance Hierarchy:  
    CustomNativeRenderer => BaseNativeRenderer => BaseCreativeRenderer
    """
    
    def _get_ad_type(self):
        return 'custom'
    
    def _setup_headers(self):
        super(CustomNativeRenderer, self)._setup_headers()
        self.header_context.ad_type = self._get_ad_type()
        self.header_context.full_ad_type = None
        self.header_context.custom_selector = self.creative.html_data.rstrip(":")
        
    def _setup_content(self):
        self.rendered_creative = 'custom selector: %s' % \
                                    self.creative.html_data
