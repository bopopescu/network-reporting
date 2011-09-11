from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class InmobiRenderer(HtmlDataRenderer):
    """ For now, just do the standard """
    
    def _setup_headers(self):
        super(InmobiRenderer, self)._setup_headers()
        self.header_context.add_header("X-Launchpage", "http://c.w.inmobi.com")