from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class BrightRollRenderer(HtmlDataRenderer):
    """ For now, just do the standard """
    
    def _setup_headers(self):
        super(BrightRollRenderer, self)._setup_headers()
        self.header_context.add_header("X-Scrollable","1")
        self.header_context.add_header("X-Interceptlinks","0")