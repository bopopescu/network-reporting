from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class InmobiRenderer(HtmlDataRenderer):
    """
    Inheritance Hierarchy:  
    InmobiRenderer => HtmlDataRenderer => 
       BaseHtmlRenderer => BaseCreativeRenderer
    """
    
    def _setup_headers(self):
        super(InmobiRenderer, self)._setup_headers()
        self.header_context.launch_page = "http://c.w.inmobi.com"
