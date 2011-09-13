from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 
from google.appengine.api import images        
from google.appengine.api.images import InvalidBlobKeyError 
import logging

class TextAndTileRenderer(BaseHtmlRenderer):
    """
    Uses specific TEMPLATE for rendering text/tile creative
    """
    TEMPLATE = 'text_icon.html'
    
    def _setup_html_context(self):
        super(TextAndTileRenderer, self)._setup_html_context()  
        try:
            image_url = images.get_serving_url(self.creative.image_blob)  
        except InvalidBlobKeyError:
            logging.error("Could not find blobkey. Perhaps you are on mopub-experimental.")   
            image_url = ""
            
        self.html_context["image_url"] = image_url
        
        
