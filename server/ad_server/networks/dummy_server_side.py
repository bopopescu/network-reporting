from ad_server.networks.server_side import ServerSide, ServerSideException

""" Dummy server sides implemented for testing purposes."""


class DummyServerSideSuccess(ServerSide):
    """ Always returns a successful response """


    def make_call_and_get_html_from_response(self, html="<html> FAKE RESPONSE </html>"):
        return html



class DummyServerSideFailure(ServerSide):
    """ Always returns a failed response """

    def make_call_and_get_html_from_response(self, html="<html> FAKE RESPONSE </html>"):
        raise ServerSideException("This dummy server always fails.")
