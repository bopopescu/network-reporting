from ad_server.networks.server_side import ServerSide


class DummyServerSide(ServerSide): 
    """ This dummy server is implemented for testing purposes."""

    def make_call_and_get_html_from_response(self, html="<html> FAKE RESPONSE </html>"):   
        return html
