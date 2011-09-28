from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class BrightRollRenderer(HtmlDataRenderer):
    """
    Inheritance Hierarchy:  
    BrightRollRenderer => HtmlDataRenderer => 
        BaseHtmlRenderer => BaseCreativeRenderer
    """

    def _setup_headers(self):
        super(BrightRollRenderer, self)._setup_headers()
        self.header_context.scrollable = "1"
        self.header_context.intercept_links = "0"
