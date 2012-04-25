from ad_server.networks.server_side import ServerSide
from ad_server.networks.server_side import ServerSideException  
class AppNexusServerSide(ServerSide):           
    """ Deprecated """

    def make_call_and_get_html_from_response(self):
        raise ServerSideException("AppNexus is deprecated")
