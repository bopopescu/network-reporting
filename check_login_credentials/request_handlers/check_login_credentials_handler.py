import copy
import json
import logging
import sys
sys.path.append('/home/ubuntu/mopub_experimental/server')

import tornado.web

from ad_network_reports.ad_networks import AD_NETWORKS
from ad_network_reports.forms import LoginInfoForm

class AdNetworkLoginCredentials(object):
    pass

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        callback = self.get_argument('callback')
        logging.warning("Arguments")
        logging.warning(self.request.arguments)

        ad_network = self.get_argument('ad_network_name')
        initial = {}
        for network in AD_NETWORKS.keys():
            initial[network + '-ad_network_name'] = network

        args = {}
        for key, value in self.request.arguments.iteritems():
            args[key] = value[0]
        args.update(initial)

        form = LoginInfoForm(args, prefix=ad_network)

        if form.is_valid():
            login_credentials = AdNetworkLoginCredentials()
            login_credentials.ad_network_name = form.cleaned_data[
                    'ad_network_name']
            login_credentials.username = form.cleaned_data['username']
            login_credentials.password = form.cleaned_data['password']
            login_credentials.client_key = form.cleaned_data['client_key']
            logging.warning(login_credentials.__dict__)

            try:
                logging.warning("Creating the scraper object")
                scraper = AD_NETWORKS[login_credentials.ad_network_name]. \
                        constructor(login_credentials)
                logging.warning("Testing the login info")
                scraper.test_login_info()
                logging.warning("Returning true")
                self.write(callback + '(true)')
                return
            except Exception as e:
                logging.error(e)

        logging.warning("Returning false")
        self.write(callback + '(false)')

