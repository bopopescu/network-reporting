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
        if self._is_mraid():
            self.html_context['use_impression_pixel'] = False

    def _is_mraid(self):
        return getattr(self.creative, 'ormma_html', False)

    def _get_ad_type(self):
        if self._is_mraid():
            return 'mraid'
        return super(HtmlDataRenderer, self)._get_ad_type()

    def _get_template(self):
        if self._is_mraid():
            return 'mraid.html'
        return super(HtmlDataRenderer, self)._get_template()
