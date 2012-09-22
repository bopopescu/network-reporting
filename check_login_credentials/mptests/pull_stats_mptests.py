import sys
import urllib
import multiprocessing

import tornado.web
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

from request_handlers.pull_stats_handler import PullStatsHandler

import common.utils.test.setup
from google.appengine.ext import db
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper, AdNetworkScrapeStats
from account.models import Account, NetworkConfig, User
from publisher.models import App

CALLBACK = 'jQuery_function_name'

USERNAME = 'username'
USER_EMAIL = 'email@bs.com'
APP_NAME = 'BET WAP Site'

JUMPTAP_PUB_ID = 'pa_zaphrox_zaphrox_drd_app'
ADMOB_PUB_ID = 'a14cf615dc654dd'
IAD_PUB_ID = '329218549'
INMOBI_PUB_ID ='4028cba6328f45a10132ed37d79a060e'
MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

JUMPTAP = 'jumptap'
JUMPTAP_USERNAME = 'zaphrox'
JUMPTAP_PASSWORD = 'JR.7x89re0'

MOBFOX = 'mobfox'

ADMOB = 'admob'
ADMOB_USERNAME = 'developers@animoca.com'
ADMOB_PASSWORD = '5zfy6wmbx4kcgflq'
ADMOB_CLIENT_KEY = 'k0df241c82bfe3c34d8fe7750c1705e6'

INMOBI = 'inmobi'
INMOBI_USERNAME = '4028cb972fe21753012ffb7680350267'
INMOBI_PASSWORD = '0588884947763'

PUB_IDS_BY_NETWORK = {ADMOB: ADMOB_PUB_ID,
                      INMOBI: INMOBI_PUB_ID,
                      JUMPTAP: JUMPTAP_PUB_ID,
                      MOBFOX: MOBFOX_PUB_ID}

class TestRequestHandlers(AsyncHTTPTestCase):
    def get_app(self):
        application = tornado.web.Application([
                (r'/pull/$', PullStatsHandler),
                ], debug=True)
        return application

    def get_new_ioloop(self):
        return IOLoop.instance()

    def setUp(self):
        _clear_db()
        super(TestRequestHandlers, self).setUp()

    def tearDown(self):
        _clear_db()
        super(TestRequestHandlers, self).tearDown()

    def handler_empty_mptest(self):
        try:
            response = self.fetch('/pull/')
        except:
            assert False

    def jumptap_handler_mptest(self):
        resp = self._make_request(JUMPTAP, JUMPTAP_USERNAME, JUMPTAP_PASSWORD)
        _check_response(resp)

    def mobfox_handler_mptest(self):
        resp = self._make_request(MOBFOX)
        _check_response(resp)

    def admob_handler_mptest(self):
        resp = self._make_request(ADMOB, ADMOB_USERNAME, ADMOB_PASSWORD,
                ADMOB_CLIENT_KEY)
        _check_response(resp)

    ## Helper functions:

    def _make_request(self, network_type, username=None, password=None,
            client_key=None, email=False):
        # CREATE TEST MODELS
        #
        # these are stored in sql and won't be on GAE
        # implication: we can't access the model we can only use their keys
        # for references
        user = User(username=USERNAME, email=USER_EMAIL)
        user.put()
        account = Account(all_mpusers=[user.key()])
        account.put()

        app = App(account=account, name=APP_NAME)
        app.put()

        # these are stored on GAE
        login = AdNetworkLoginCredentials(account=account,
                                          ad_network_name=network_type,
                                          username=username,
                                          password=password,
                                          client_key=client_key,
                                          email=email)
        login.put()

        pub_id = PUB_IDS_BY_NETWORK[network_type]
        mapper = AdNetworkAppMapper(ad_network_name=network_type,
                                    publisher_id=pub_id,
                                    ad_network_login=login,
                                    application=app)
        mapper.put()

        data = {'account_key': str(account.key()),
                'callback': CALLBACK,
                'network_type': network_type}

        # Don't send email when testing is = True
        data['testing'] = True

        self.http_client.fetch(self.get_url('/pull/?' +
            urllib.urlencode(data)), self.stop)
        # Return the response
        return self.wait(timeout=20)

def _check_response(resp):
    assert AdNetworkLoginCredentials.all().count() == 1

    children = multiprocessing.active_children()
    print children
    if children:
        print children[0].pid
        children[0].join()

        # Unfortunately the app engine datastore doesn't play nice with
        # multiprocessing when testing.
#       print AdNetworkScrapeStats.all().count()
#       assert AdNetworkScrapeStats.all().count() == 14
        assert children[0].exitcode == 0

def _clear_db():
    db.delete(Account.all())
    db.delete(App.all())
    db.delete(NetworkConfig.all())
    db.delete(AdNetworkLoginCredentials.all())
    db.delete(AdNetworkAppMapper.all())
    db.delete(AdNetworkScrapeStats.all())

