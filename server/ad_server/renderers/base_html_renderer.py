import os

from ad_server.renderers.creative_renderer import BaseCreativeRenderer
# NOTE: appengine specific, but can be just django
from google.appengine.ext.webapp import template

class BaseHtmlRenderer(BaseCreativeRenderer):
    """ 
    All HTML renderers will need to subclass this.

    Inheritance Hierarchy:  
    BaseHtmlRenderer => BaseCreativeRenderer

    NOTE: If the creative type to be rendered has an html_data field
    you should subclass HtmlDataRenderer (which subclasses BaseHtmlRenderer)
    rather than subclassing BaseHtmlRenderer directly
    """
    
    TEMPLATE = 'base.html'
    
    def __init__(self, *args, **kwargs):
        """
        Calls super __init__ as well as initializes html_context.
        html_context is an html renderer specific property
        used for rendering the html via django template
        """
        super(BaseHtmlRenderer, self).__init__(*args, **kwargs)
        
        self.html_context = {}
        self._setup_html_context()
        
    def _setup_html_context(self):
        """
        Initialize the html specific properties necessary for rendering
        html creative using django template. This method may need to be overridden.
        """
        self.html_context['creative'] = self.creative
        self.html_context['version'] = self.version
        self.html_context['impression_url'] = self.impression_url
        self.html_context['is_fullscreen'] = self.adunit.is_fullscreen()
        
        # determine user agent
        # TODO: we probably want to have different iphone and android version
        ua = self.client_context.user_agent.lower()
        if 'iphone' in ua:
            os = 'iphone'
        elif 'android' in ua:
            os = 'android'
        else:
            os = None
        self.html_context['os'] = os
        
    def _get_ad_type(self):
        return 'html'
        
    def _setup_content(self):
        """
        Uses the html_context and self.TEMPLATE to generate creative html.
        This method should never be overridden. In order to customize
        html creative rendering, you should override _setup_html_context
        to provide specific context to the template. You can also
        override self.TEMPLATE to provide more flexibility/customization
        """
        path = os.path.join(os.path.dirname(__file__), 
                            'templates', 
                            self.TEMPLATE)
        self.rendered_creative = template.render(path, self.html_context)
    
