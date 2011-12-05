import logging
import sys
import os

import tornado.web

from datetime import date, timedelta
from subprocess import call

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

sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
import common.utils.test.setup
from google.appengine.ext import db

from ad_network_reports.ad_networks import AD_NETWORKS, AdNetwork
from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.query_managers import AdNetworkReportQueryManager
from ad_network_reports.update_ad_networks import update_ad_networks


class AdNetworkLoginCredentials(object):
    pass

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    #app_id = 'mopub-experimental'
    #host = '38.latest.mopub-experimental.appspot.com'
    app_id = 'mopub-inc'
    host = '38.latest.mopub-inc.appspot.com'
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
        args[ad_network + '-username_str'] = args[ad_network + '-username']
        args[ad_network + '-password_str'] = args[ad_network + '-password']
        form = LoginInfoForm(args, prefix=ad_network)

        if form.is_valid():
            login_credentials = AdNetworkLoginCredentials()
            login_credentials.ad_network_name = form.cleaned_data[
                    'ad_network_name']
            login_credentials.username = form.cleaned_data['username_str']
            login_credentials.password = form.cleaned_data['password_str']
            login_credentials.client_key = form.cleaned_data['client_key']

            try:
                account_key = self.get_argument('account_key')
                manager = AdNetworkReportQueryManager(db.get(account_key))
                scraper = AdNetwork(login_credentials).create_scraper()
                # Password and username aren't encrypted yet so we don't need
                # to call append_extra info like in update_ad_networks.
                # They're sent through ssl so this is fine.
                scraper.test_login_info()
                logging.info("Returning true.")
                self.write(callback + '(true)')
                # Write out response and close connection.
                self.finish()
            except Exception as e:
                # We don't want Tornado to stop running if something breaks
                # somewhere.
                logging.error(e)
            else:
                if os.path.exists('/home/ubuntu/'):
                    setup_remote_api()
                wants_email = self.get_argument('email', False) and True
                accounts_login_credentials = \
                        list(manager.get_login_credentials())
                login_credentials = manager. \
                        create_login_credentials_and_mappers(ad_network_name=
                        login_credentials.ad_network_name,
                        username=login_credentials.username,
                        password=login_credentials.password,
                        client_key=login_credentials.client_key,
                        send_email=wants_email)

                # Collect the last two weeks of data for these credentials and
                # add it to the database if the login credentials for the
                # network are new.
                logging.warning([creds.ad_network_name for creds in
                    accounts_login_credentials])
                if login_credentials.ad_network_name not in \
                        [creds.ad_network_name for creds in
                                accounts_login_credentials]:
                    logging.warning("HERE")
                    # spawnDaemon('/Users/tiagobandeira/Documents/mopub/server/' \
                    #         'ad_network_reports/update_ad_networks.py',
                    #         str(login_credentials.key()))
                    call(['/Users/tiagobandeira/Documents/mopub/server/' \
                            'ad_network_reports/update_ad_networks.py',
                            str(login_credentials.key())])
#                    two_weeks_ago = date.today() - timedelta(days=14)
#                    update_ad_networks(start_date=two_weeks_ago,
#                            only_these_credentials=login_credentials)
                return

        logging.info("Returning false.")
        self.write(callback + '(false)')

def spawnDaemon(path_to_executable, *args):
    """Spawn a completely detached subprocess (i.e., a daemon).

    E.g. for mark:
    spawnDaemon("../bin/producenotify.py", "producenotify.py", "xx")
    """
    logging.warning('1')
    # fork the first time (to make a non-session-leader child process)
    try:
        pid = os.fork()
    except OSError, e:
        raise RuntimeError("1st fork failed: %s [%d]" % (e.strerror, e.errno))
    if pid == 0:
        # detach from controlling terminal (to make child a session-leader)
        os.setsid()
        # logging.warning('return')
        # # parent (calling) process is all done
        # return

    logging.warning('2')
    try:
        pid = os.fork()
    except OSError, e:
        raise RuntimeError("2nd fork failed: %s [%d]" % (e.strerror, e.errno))
        raise Exception, "%s [%d]" % (e.strerror, e.errno)
    if pid != 0:
        # child process is all done
        os._exit(0)

    logging.warning('3')
    # grandchild process now non-session-leader, detached from parent
    # grandchild process must now close all open files
    try:
        maxfd = os.sysconf("SC_OPEN_MAX")
    except (AttributeError, ValueError):
        maxfd = 1024

    for fd in range(maxfd):
        try:
           os.close(fd)
        except OSError: # ERROR, fd wasn't open to begin with (ignored)
           pass

    logging.warning('4')
    # redirect stdin, stdout and stderr to /dev/null
    # os.open(REDIRECT_TO, os.O_RDWR) # standard input (0)
    # os.dup2(0, 1)
    # os.dup2(0, 2)

    # and finally let's execute the executable for the daemon!
    try:
      logging.warning('EXECUTING NEW PROCESS')
      os.execv(path_to_executable, args)
    except Exception, e:
      # oops, we're cut off from the world, let's just give up
      os._exit(255)
