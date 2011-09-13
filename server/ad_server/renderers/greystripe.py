from string import Template   
import random                 
from ad_server.renderers.html_data_renderer import HtmlDataRenderer

class GreyStripeRenderer(HtmlDataRenderer):

    def _setup_headers(self):
        super(GreyStripeRenderer, self)._setup_headers()
        self.header_context.launch_page = \
            "http://adsx.greystripe.com/openx/www/delivery/ck.php"
