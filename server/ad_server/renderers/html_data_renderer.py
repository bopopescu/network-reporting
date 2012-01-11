from ad_server.renderers.base_html_renderer import BaseHtmlRenderer

ORMMA_ADTYPE = 'ormma'

class HtmlDataRenderer(BaseHtmlRenderer):
    """ 
    Simple extension to BaseHtmlRenderer. Overrides _setup_html_context
    to provide additional 'html_data' field for rendering. To be used
    when creative.html_data is present

    Inheritance Hierarchy:  
    HtmlDataRenderer => BaseHtmlRenderer => BaseCreativeRenderer 
    """

    TEMPLATE = 'html_data.html'

    def _setup_html_context(self):
        super(HtmlDataRenderer, self)._setup_html_context()
        self.html_context['html_data'] = self.creative.html_data
        self.html_context['random_val'] = self.random_val

    def _setup_headers(self):
        super(HtmlDataRenderer, self)._setup_headers()
        # TODO: clean this up
        # for ORMMA HTML we need to pass
        # banner: 'ormma' as the adtype, None as full_ad_type
        # interstitial: 'interstitial' as the adtype, 'ormma' as full_ad_type
        if getattr(self.creative, 'ormma_html', False):
            if self.adunit.is_fullscreen():
                self.header_context.ad_type = "interstitial"
                self.header_context.full_ad_type = ORMMA_ADTYPE
            else:
                self.header_context.ad_type = ORMMA_ADTYPE
