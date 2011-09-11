from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 
from google.appengine.api import images   

class TextAndTileRenderer(BaseHtmlRenderer):
    """ For now, just do the standard """
    TEMPLATE = 'text_icon.html'
    
    def _setup_html_context(self):
        image_url = images.get_serving_url(self.creative.image_blob) 
        self.html_context["image_url"] = image_url
        
        super(TextAndTileRenderer, self)._setup_html_context()