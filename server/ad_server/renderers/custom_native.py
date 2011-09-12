from ad_server.renderers.base_native_renderer import BaseNativeRenderer   

class CustomNativeRenderer(BaseNativeRenderer):
    """ For now, just do the standard """
    
    def _get_ad_type(self):
        return 'custom'
    
    def _setup_headers(self):
        super(CustomNativeRenderer, self)._setup_headers()
        self.header_context.add_header("X-Customselector", 
                                       self.creative.html_data.rstrip(":"))
        
    def _setup_content(self):
        self.rendered_creative = 'custom selector: %s' % \
                                    self.creative.html_data
