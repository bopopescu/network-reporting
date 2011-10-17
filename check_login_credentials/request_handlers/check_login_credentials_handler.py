import logging
import sys
sys.path.append('/home/ubuntu/mopub_experimental/server')

import tornado.web

from ad_network_reports.ad_networks import AD_NETWORKS

class AdNetworkLoginCredentials(object):
    pass

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    def post(self, *args, **kwargs):
        #logging.warning(self.request.arguments)

        login_credentials = AdNetworkLoginCredentials()
        login_credentials.ad_network_name = self.get_argument(
                '_ad_network_name')
        login_credentials.username = self.get_argument('_username', None)
        login_credentials.password = self.get_argument('_password', None)
        login_credentials.client_key = self.get_argument('_client_key', None)
        login_credentials.publisher_ids = self.get_argument('_publisher_ids',
                None)
        login_credentials.adunits = self.get_argument('_adunits', None)

        try:
            scraper = AD_NETWORKS[login_credentials.ad_network_name]. \
                    constructor(login_credentials)
            scraper.test_login_info()
        except Exception as e:
            logging.error(e)
            raise tornado.web.HTTPError(401)
        self.write('')
