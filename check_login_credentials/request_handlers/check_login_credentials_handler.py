import logging
import sys
import os

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

from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AdNetworkReportManager, \
        AdNetworkLoginManager
from ad_network_reports.update_ad_networks import update_login_stats_for_check

from common.utils.connect_to_appengine import setup_remote_api

class AdNetworkLoginCredentials(object):
    pass

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
        if ad_network + '-username' in args:
            args[ad_network + '-username_str'] = args[ad_network + '-username']
        else:
            args[ad_network + '-username_str'] = '-'
        if ad_network + '-password' in args:
            args[ad_network + '-password_str'] = args[ad_network + '-password']
        else:
            args[ad_network + '-password_str'] = '-'
        form = LoginInfoForm(args, prefix=ad_network)

        if form.is_valid():
            login_credentials = AdNetworkLoginCredentials()
            login_credentials.ad_network_name = ad_network
            login_credentials.username = form.cleaned_data.get('username_str',
                    '')
            login_credentials.password = form.cleaned_data.get('password_str',
                    '')
            login_credentials.client_key = form.cleaned_data.get('client_key',
                    '')

            try:
                account_key = self.get_argument('account_key')
                if os.path.exists('/home/ubuntu/'):
                    setup_remote_api()
                account = db.get(account_key)
                scraper = AdNetwork(login_credentials).create_scraper()
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
            else:
                if os.path.exists('/home/ubuntu/'):
                    mail.send_mail(sender='olp@mopub.com',
                                   to='tiago@mopub.com',
                                   subject="New user signed up",
                                   body="account: " + account_key + "\n" +
                                   "emails: " + ', '.join(db.get(account_key).emails) + "\n" +
                                   "network: " + ad_network)
                wants_email = self.get_argument('email', False) and True
                accounts_login_credentials = set([creds.ad_network_name for
                    creds in AdNetworkLoginManager.get_logins(account)])
                login_credentials = AdNetworkReportManager. \
                        create_login_credentials_and_mappers(account=account,
                                ad_network_name=
                                    login_credentials.ad_network_name,
                                username=login_credentials.username,
                                password=login_credentials.password,
                                client_key=login_credentials.client_key,
                                send_email=wants_email)

                # Collect the last two weeks of data for these credentials and
                # add it to the database if the login credentials for the
                # network are new.
                if login_credentials.ad_network_name not in \
                        accounts_login_credentials:
                    pacific = timezone('US/Pacific')
                    two_weeks_ago = (datetime.now(pacific) -
                            timedelta(days=14)).date()

                    # Set testing
                    testing = self.get_argument('testing', False)

                    process = multiprocessing.Process(target=update_login_stats_for_check,
                            args=(login_credentials,
                                  two_weeks_ago,
                                  None,
                                  testing,
                                  ))
                    logging.info(process.daemon)
                    #process.daemon = True
                    process.start()
                    logging.info(process.daemon)

                    children = multiprocessing.active_children()
                    logging.info(children)
                    logging.info(children[0].pid)
                return
        else:
            logging.info("Invalid form.")

        logging.info("Returning false.")
        self.write(callback + '(false)')

