from ad_server.renderers.base_html_renderer import BaseHtmlRenderer

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

    def _get_ad_type(self):
        if getattr(self.creative, 'ormma_html', False):
            return 'ormma'
        return super(HtmlDataRenderer, self)._get_ad_type()
