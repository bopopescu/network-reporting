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
    sys.path.append('/Users/tiagobandeira/mopub/server')
import common.utils.test.setup
from google.appengine.ext import db
from google.appengine.api import mail

from ad_network_reports.models import LoginStates
from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginCredentialsForm
from ad_network_reports.query_managers import AdNetworkReportManager, \
        AdNetworkLoginManager
from ad_network_reports.update_ad_networks import update_login_stats_for_check

from common.utils.connect_to_appengine import setup_remote_api

# Create temp login so we don't have to deal with encryption when checking if
# login credentials are valid
class Login(object):
    pass

class CheckLoginCredentialsHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        req_type = self.get_argument('req_type', 'both')
        account_key = self.get_argument('account_key')
        network = self.get_argument('network', False)
        # TODO: remove legacy shit
        if not network:
            network = self.get_argument('ad_network_name')

        # connect to app engine
        if os.path.exists('/home/ubuntu/'):
            setup_remote_api()
        account = db.get(account_key)

        error = False
        if req_type in ('check', 'both'):
            callback = self.get_argument('callback')

            initial = {}
            for network_type in AD_NETWORKS.keys():
                initial[network_type + '-ad_network_name'] = network_type

            args = {}
            for key, value in self.request.arguments.iteritems():
                args[key] = value[0]
            args.update(initial)

            # Can't have the same name as the model. Fixes unicode bug.
            if network + '-username' in args:
                args[network + '-username_str'] = args[network +
                        '-username']
            else:
                args[network + '-username_str'] = '-'
            if network + '-password' in args:
                args[network + '-password_str'] = args[network +
                        '-password']
            else:
                args[network + '-password_str'] = '-'
            form = LoginCredentialsForm(args, prefix=network)

            if form.is_valid():
                login = Login()
                login.ad_network_name = network
                login.username = form.cleaned_data.get(
                        'username_str', '')
                login.password = form.cleaned_data.get(
                        'password_str', '')
                login.client_key = form.cleaned_data.get(
                        'client_key', '')

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
                    if os.path.exists('/home/ubuntu/'):
                        mail.send_mail(sender='olp@mopub.com',
                                       to='tiago@mopub.com',
                                       subject="New user signed up",
                                       body="account: " + account_key + "\n" +
                                       "emails: " + ', '.join(db.get(
                                           account_key).emails) + "\n" +
                                       "network: " + network)
                    wants_email = self.get_argument('email', False) and True
                    accounts_login = set([creds.ad_network_name for
                        creds in AdNetworkLoginManager.get_logins(
                            account)])
                    AdNetworkReportManager. \
                            create_login_credentials_and_mappers(account=
                                    account,
                                    ad_network_name=
                                        login.ad_network_name,
                                    username=login.username,
                                    password=login.password,
                                    client_key=login.client_key,
                                    send_email=wants_email)
            else:
                error = True
                logging.info("Invalid form.")

        if not error and req_type in ('pull', 'both'):
            login = AdNetworkLoginManager.get_logins(account, network).get()
            if login.state == LoginStates.NOT_SETUP:
                login.state = LoginStates.PULLING_DATA
                login.put()
                # Collect the last two weeks of data for these credentials and
                # add it to the database if the login credentials for the
                # network are new.
                if login.ad_network_name not in \
                        accounts_login:
                    pacific = timezone('US/Pacific')
                    two_weeks_ago = (datetime.now(pacific) -
                            timedelta(days=14)).date()

                    # Set testing
                    testing = self.get_argument('testing', False)

                    process = multiprocessing.Process(target=
                            update_login_stats_for_check,
                            args=(login,
                                  two_weeks_ago,
                                  None,
                                  testing,
                                  ))
                    #process.daemon = True
                    process.start()

                    #children = multiprocessing.active_children()
                    #logging.info(children)
                    #logging.info(children[0].pid)

        if error:
            logging.info("Returning false.")
            self.write(callback + '(false)')
        return


