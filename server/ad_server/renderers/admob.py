from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 

from google.appengine.api import images 

class AdMobRenderer(BaseHtmlRenderer):
    """ For now, just do the standard """
    
    TEMPLATE = 'admob.html'
    
    def _setup_html_context(self):

        self.html_context['site_id'] = self.adunit.network_config.admob_pub_id
        self.html_context['bgcolor'] = self.adunit.app.admob_bgcolor
        self.html_context['textcolor']= self.adunit.app.admob_textcolor
        
        super(AdMobRenderer, self)._setup_html_context()