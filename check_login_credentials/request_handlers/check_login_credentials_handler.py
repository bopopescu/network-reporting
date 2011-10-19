import json
import logging
import sys
sys.path.append('/home/ubuntu/mopub_experimental/server')

import tornado.web

from ad_network_reports.ad_networks import AD_NETWORKS

class AdNetworkLoginCredentials(object):
    pass

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        callback = self.get_argument('callback')

        login_credentials = AdNetworkLoginCredentials()
        login_credentials.ad_network_name = self.get_argument(
                'ad_network_name')
        login_credentials.username = self.get_argument('username', None)
        login_credentials.password = self.get_argument('password', None)
        login_credentials.client_key = self.get_argument('client_key', None)
        login_credentials.publisher_ids = self.get_argument('publisher_ids',
                None)
        login_credentials.adunits = self.get_argument('adunits', [])
        #logging.warning(login_credentials.__dict__)

        try:
            scraper = AD_NETWORKS[login_credentials.ad_network_name]. \
                    constructor(login_credentials)
            scraper.test_login_info()
            self.write(callback + '(true)')
        except Exception as e:
            logging.error(e)
            self.write(callback + '(false)')
