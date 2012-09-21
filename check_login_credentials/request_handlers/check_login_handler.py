import logging
import sys
import os
import traceback

import tornado.web
import multiprocessing

from datetime import datetime, date, timedelta
from pytz import timezone

#TODO: fix path stuff
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
    # For google.appengine.ext
    sys.path.append('/home/ubuntu/google_appengine')
    sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
    sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
    sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
    sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
    sys.path.append('/home/ubuntu/google_appengine/lib/webob')
    sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')

else:
    sys.path.append('/Users/mopubsf/mopub/server')
import common.utils.test.setup
from google.appengine.ext import db
from google.appengine.api import mail

from ad_network_reports.models import LoginStates, AdNetworkLoginCredentials
from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginCredentialsForm
from ad_network_reports.query_managers import AdNetworkReportManager, \
        AdNetworkLoginManager
from ad_network_reports.update_ad_networks import update_login_stats_for_check

from common.utils.connect_to_appengine import setup_remote_api

class CheckLoginHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        account_key = db.Key(self.get_argument('account_key'))
        network_type = self.get_argument('network_type', False)
        # connect to app engine
        if os.path.exists('/home/ubuntu/'):
            setup_remote_api()

        error = False
        callback = self.get_argument('callback')

        initial = {}
        for network_type in AD_NETWORKS.keys():
            initial[network_type + '-ad_network_name'] = network_type

        args = {}
        for key, value in self.request.arguments.iteritems():
            args[key] = value[0]
        args.update(initial)

        # Can't have the same name as the model. Fixes unicode bug.
        if network_type + '-username' in args:
            args[network_type + '-username_str'] = args[network + '-username']
        elif network_type + '-username_str' not in args:
            args[network_type + '-username_str'] = '-'
        if network_type + '-password' in args:
            args[network_type + '-password_str'] = args[network + '-password']
        elif network_type + '-password_str' not in args:
            args[network_type + '-password_str'] = '-'
        form = LoginCredentialsForm(args, prefix=network_type)

        if form.is_valid():
            logging.info("Form is valid")

            username = form.cleaned_data.get('username_str', '')
            password = form.cleaned_data.get('password_str', '')
            client_key = form.cleaned_data.get('client_key', '')
            # TODO: use query_managers
            login = AdNetworkLoginCredentials(account=account_key,
                                              ad_network_name=network_type,
                                              username=username,
                                              password=password,
                                              client_key=client_key)

            try:
                scraper = AdNetwork(login).create_scraper()
                # Password and username aren't encrypted yet so we don't need
                # to call append_extra info like in update_login_stats_for_check.
                # They're sent through ssl so this is fine.
                scraper.test_login_info()
                logging.info("Returning true.")
                self.write(callback + '(true)')
                # Write out response and close connection.
                self.finish()
            except Exception as exception:
                # We don't want Tornado to stop running if something breaks
                # somewhere.
                logging.error(exception)
                exc_traceback = sys.exc_info()[2]

                error_msg = repr(traceback.extract_tb(exc_traceback))

                logging.error(error_msg)
                error = True
            else:
                wants_email = self.get_argument('email', False) and True
                AdNetworkLoginManager.put(login)
        else:
            error = True
            logging.info("Invalid form.")


        if error:
            logging.info("Returning false.")
            self.write(callback + '(false)')

