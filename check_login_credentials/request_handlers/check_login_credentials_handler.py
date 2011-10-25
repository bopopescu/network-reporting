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
        logging.warning(self.request.arguments)

        initial = {}
        for network in AD_NETWORKS.keys():
            initial[network + '-ad_network_name'] = network

        ad_network = self.request.POST['ad_network_name']
        wants_email = self.request.POST.get('email', False) and True

        postcopy = copy.deepcopy(self.request.arguments)
        postcopy.update(initial)

        form = LoginInfoForm(postcopy, prefix=ad_network)

        if form.is_valid():
            login_credentials = AdNetworkLoginCredentials()
            login_credentials.ad_network_name = form.cleaned_data[
                    'ad_network_name']
            login_credentials.username = form.cleaned_data['username']
            login_credentials.password = form.cleaned_data['password']
            login_credentials.client_key = form.cleaned_data['client_key']
            login_credentials.publisher_ids = form.cleaned_data['publisher_ids']
            login_credentials.adunits = []
            #logging.warning(login_credentials.__dict__)

            try:
                scraper = AD_NETWORKS[login_credentials.ad_network_name]. \
                        constructor(login_credentials)
                scraper.test_login_info()
                self.write(callback + '(true)')
            except Exception as e:
                logging.error(e)

        self.write(callback + '(false)')

