from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class BaseNativeRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """

    def _get_ad_type(self):
        raise NotImplementedError

    def _setup_content(self):
        self.rendered_creative = '%s native' % self._get_ad_type()
        
    def _setup_headers(self):
        super(BaseNativeRenderer, self)._setup_headers()
        self.header_context.add_header('X-Failurl', self.fail_url)    