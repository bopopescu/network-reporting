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

from ad_network_reports.models import LoginStates
from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginCredentialsForm
from ad_network_reports.query_managers import AdNetworkReportManager, \
        AdNetworkLoginManager
from ad_network_reports.update_ad_networks import update_login_stats_for_check

from common.utils.connect_to_appengine import setup_remote_api

class PullStatsHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        account_key = db.Key(self.get_argument('account_key'))
        network_type = self.get_argument('network_type', False)
        # connect to app engine
        if os.path.exists('/home/ubuntu/'):
            setup_remote_api()

        error = False
        callback = self.get_argument('callback')

        login = AdNetworkLoginManager.get_logins(account_key, network_type).get()
        if login.state == LoginStates.NOT_SETUP:
            login.state = LoginStates.PULLING_DATA
            AdNetworkLoginManager.put(login)
            # Collect the last two weeks of data for these credentials and
            # add it to the database if the login credentials for the
            # network are new.
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

