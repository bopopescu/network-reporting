from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 
                                                                     
from google.appengine.api.images import InvalidBlobKeyError
import logging
from google.appengine.api import images 

class ImageRenderer(BaseHtmlRenderer):
    """
    Uses image specific TEMPLATE for rendering image creative

    Inheritance Hierarchy:  
    ImageRenderer => BaseHtmlRenderer => BaseCreativeRenderer
    """
    
    TEMPLATE = 'image.html'
    
    def _setup_html_context(self):
        super(ImageRenderer, self)._setup_html_context()
        img_height = self.creative.image_height
        img_width = self.creative.image_width
        
        self.html_context['w'] = img_width
        self.html_context['h'] = img_height
        self.html_context['w_divided_2'] = img_width/2
        self.html_context['h_divided_2'] = img_height/2
        try:
            image_url = images.get_serving_url(self.creative.image_blob)  
        except InvalidBlobKeyError:
            logging.error("Could not find blobkey. Perhaps you are on mopub-experimental.")   
            image_url = "" 
        except NotImplementedError:
            image_url = "http://localhost:8080/_ah/img/blobby"

        self.html_context["image_url"] = image_url
