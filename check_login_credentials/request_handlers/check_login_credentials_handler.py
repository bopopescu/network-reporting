import copy
import json
import logging
import sys

import tornado.web

sys.path.append('/home/ubuntu/mopub/server')
from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AdNetworkReportQueryManager

# For google.appengine.ext
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')
from google.appengine.ext import db

class AdNetworkLoginCredentials(object):
    pass

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-experimental'
    host = '38.latest.mopub-experimental.appspot.com'
    #app_id = 'mopub-inc'
    #host = '38.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func,
            host)

def auth_func():
    return 'olp@mopub.com', 'N47935'

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        callback = self.get_argument('callback')

        ad_network = self.get_argument('ad_network_name')
        initial = {}
        for network in AD_NETWORKS.keys():
            initial[network + '-ad_network_name'] = network

        args = {}
        for key, value in self.request.arguments.iteritems():
            args[key] = value[0]
        args.update(initial)

        # Can't have the same name as the model. Fixes unicode bug.
        args[ad_network + '-password_str'] = args[ad_network + '-password']
        args[ad_network + '-username_str'] = args[ad_network + '-username']
        form = LoginInfoForm(args, prefix=ad_network)

        if form.is_valid():
            login_credentials = AdNetworkLoginCredentials()
            login_credentials.ad_network_name = form.cleaned_data[
                    'ad_network_name']
            login_credentials.username = form.cleaned_data['username_str']
            login_credentials.password = form.cleaned_data['password_str']
            login_credentials.client_key = form.cleaned_data['client_key']

            try:
                scraper = AdNetwork(login_credentials).create_scraper()
                # Password and username aren't encrypted yet so we don't need
                # to call append_extra info like in update_ad_networks.
                # They're sent through ssl so this is fine.
                scraper.test_login_info()
                logging.info("Returning true.")
                self.write(callback + '(true)')
            except Exception as e:
                # We don't want Tornado to stop running if something breaks
                # somewhere.
                logging.error(e)
            else:
                setup_remote_api()
                account_key = self.get_argument('account_key')
                manager = AdNetworkReportQueryManager(db.get(account_key))
                wants_email = self.get_argument('email', False) and True
                manager.create_login_credentials_and_mappers(ad_network_name=
                        login_credentials.ad_network_name,
                        username=login_credentials.username,
                        password=login_credentials.password,
                        client_key=login_credentials.client_key,
                        send_email=wants_email)
                return

        logging.info("Returning false.")
        self.write(callback + '(false)')

