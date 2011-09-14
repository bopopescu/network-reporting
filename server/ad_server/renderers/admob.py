from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 

from google.appengine.api import images 

class AdMobRenderer(BaseHtmlRenderer):
    """ 
    Uses specific admob TEMPLATE for rendering

    Inheritance Hierarchy:  
    AdMobRenderer => BaseHtmlRenderer => BaseCreativeRenderer
    """
    
    TEMPLATE = 'admob.html'
    
    def _setup_html_context(self):
        super(AdMobRenderer, self)._setup_html_context()
        self.html_context['site_id'] = self.adunit.get_pub_id("admob_pub_id")
        self.html_context['bgcolor'] = self.adunit.app.admob_bgcolor
        self.html_context['textcolor']= self.adunit.app.admob_textcolor
        
    def _setup_headers(self):
        super(AdMobRenderer, self)._setup_headers()
        self.header_context.fail_url = self.fail_url
