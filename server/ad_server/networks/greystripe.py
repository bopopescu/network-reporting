from ad_server.networks.server_side import ServerSide
import urllib
import urllib2
from ad_server.debug_console import trace_logging
from ad_server.networks.server_side import ServerSideException  
class GreyStripeServerSide(ServerSide):    
    """ Greystripe is deprecated. """

    def make_call_and_get_html_from_response(self):
        raise ServerSideException("Greystripe is deprecated")
