import os

from ad_server.renderers.creative_renderer import BaseCreativeRenderer
# NOTE: appengine specific, but can be just django
from google.appengine.ext.webapp import template

class BaseHtmlRenderer(BaseCreativeRenderer):
    """ For now, just do the standard """
    
    TEMPLATE = 'base.html'
    
    def __init__(self, *args, **kwargs):
        super(BaseHtmlRenderer, self).__init__(*args, **kwargs)
        
        self.html_context = {}
        self._setup_html_context()
        
    def _setup_html_context(self):
        self.html_context['creative'] = self.creative
        self.html_context['version'] = self.version
        self.html_context['impression_url'] = self.impression_url
        self.html_context['is_fullscreen'] = self.adunit.is_fullscreen()
        
    def _get_ad_type(self):
        return 'html'
        
    def _setup_content(self):
        path = os.path.join(os.path.dirname(__file__), 
                            'templates', 
                            self.TEMPLATE)
        self.rendered_creative = template.render(path, self.html_context)
    
