from ad_server.renderers.base_html_renderer import BaseHtmlRenderer 

from google.appengine.api import images 

class ImageRenderer(BaseHtmlRenderer):
    """ For now, just do the standard """
    
    TEMPLATE = 'image.html'
    
    def _setup_html_context(self):
        img_height = self.creative.image_height
        img_width = self.creative.image_width
        
        self.html_context['w'] = img_width
        self.html_context['h'] = img_height
        self.html_context['w_divided_2'] = img_width/2
        self.html_context['h_divided_2'] = img_height/2
        
        image_url = images.get_serving_url(self.creative.image_blob) 
        self.html_context["image_url"] = image_url
        
        super(ImageRenderer, self)._setup_html_context()