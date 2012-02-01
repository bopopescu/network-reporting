from ad_server.renderers.creative_renderer import BaseCreativeRenderer

class BaseNativeRenderer(BaseCreativeRenderer):
    """
    Base class to be used for all native renderers

    Inheritance Hierarchy:  
    BaseNativeRenderer => BaseCreativeRenderer
    """
    
    def _get_ad_type(self):
        """
        Each native renderer must override this method
        """
        raise NotImplementedError

    def _setup_content(self):
        self.rendered_creative = '%s native' % self._get_ad_type()
        
    def _setup_headers(self):
        super(BaseNativeRenderer, self)._setup_headers()
