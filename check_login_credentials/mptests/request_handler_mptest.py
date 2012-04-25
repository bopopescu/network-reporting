import sys
import urllib
import multiprocessing

import tornado.web
from tornado.ioloop import IOLoop
from tornado.testing import AsyncHTTPTestCase

from request_handlers.check_login_credentials_handler import \
        CheckLoginCredentialsHandler

#TODO: Make path universal
sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
import common.utils.test.setup
from google.appengine.ext import db
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper, AdNetworkScrapeStats
from account.models import Account, NetworkConfig, User
from publisher.models import App

CALLBACK = 'jQuery_function_name'

VALID_REQUEST = 'true'
INVALID_REQUEST = 'false'

USERNAME = 'username'
USER_EMAIL = 'email@bs.com'
APP_NAME = 'BET WAP Site'

JUMPTAP_PUB_ID = 'pa_zaphrox_zaphrox_drd_app'
ADMOB_PUB_ID = 'a14cf615dc654dd'
IAD_PUB_ID = '329218549'
INMOBI_PUB_ID ='4028cba6328f45a10132ed37d79a060e'
MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

INVALID_USERNAME = 'invalid_username'
INVALID_PASSWORD = 'invalid_password'
INVALID_CLIENT_KEY = 'invalid_client_key'

JUMPTAP = 'jumptap'
JUMPTAP_USERNAME = 'zaphrox'
JUMPTAP_PASSWORD = 'JR.7x89re0'

MOBFOX = 'mobfox'

ADMOB = 'admob'
ADMOB_USERNAME = 'adnetwork@com2usamerica.com'
ADMOB_PASSWORD = '4w47m82l5jfdqw1x'
ADMOB_CLIENT_KEY = 'ka820827f7daaf94826ce4cee343837a'

INMOBI_USERNAME = '4028cb972fe21753012ffb7680350267'
INMOBI_PASSWORD = '0588884947763'

class TestRequestHandlers(AsyncHTTPTestCase):
    def get_app(self):
        application = tornado.web.Application([
                (r'/check', CheckLoginCredentialsHandler),
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
            response = self.fetch('/check')
        except:
            assert False

    def invalid_username_jumptap_handler_mptest(self):
        resp = self._make_request(JUMPTAP, INVALID_USERNAME, JUMPTAP_PASSWORD)
        _check_response(resp, INVALID_REQUEST)

    def invalid_password_jumptap_handler_mptest(self):
        resp = self._make_request(JUMPTAP, JUMPTAP_USERNAME, INVALID_PASSWORD)
        _check_response(resp, INVALID_REQUEST)

    def jumptap_handler_mptest(self):
        resp = self._make_request(JUMPTAP, JUMPTAP_USERNAME, JUMPTAP_PASSWORD)
        _check_response(resp, VALID_REQUEST)

    def mobfox_handler_mptest(self):
        resp = self._make_request(MOBFOX)
        _check_response(resp, VALID_REQUEST)

    def invalid_password_admob_handler_mptest(self):
        resp = self._make_request(ADMOB, ADMOB_USERNAME, INVALID_PASSWORD,
                ADMOB_CLIENT_KEY)
        _check_response(resp, INVALID_REQUEST)

    def invalid_username_admob_handler_mptest(self):
        resp = self._make_request(ADMOB, INVALID_USERNAME, ADMOB_PASSWORD,
                ADMOB_CLIENT_KEY)
        _check_response(resp, INVALID_REQUEST)

    def invalid_client_key_admob_handler_mptest(self):
        resp = self._make_request(ADMOB, ADMOB_USERNAME, ADMOB_PASSWORD,
                INVALID_CLIENT_KEY)
        _check_response(resp, INVALID_REQUEST)

    def admob_handler_mptest(self):
        resp = self._make_request(ADMOB, ADMOB_USERNAME, ADMOB_PASSWORD,
                ADMOB_CLIENT_KEY)
        _check_response(resp, VALID_REQUEST)

    ## Helper functions:

    def _make_request(self, network, username=None, password=None,
            client_key=None, email=False):
        # create test models
        user = User(username=USERNAME, email=USER_EMAIL)
        user.put()
        account = Account(all_mpusers=[user.key()])
        account.put()

        network_config = NetworkConfig(jumptap_pub_id=JUMPTAP_PUB_ID,
                admob_pub_id=ADMOB_PUB_ID, iad_pub_id=IAD_PUB_ID,
                inmobi_pub_id=INMOBI_PUB_ID,
                mobfox_pub_id=MOBFOX_PUB_ID)
        network_config.put()

        app = App(account=account, name=APP_NAME, network_config=
                network_config)
        app.put()

        data = {'account_key': str(account.key()),
                'callback': CALLBACK,
                'network': network}
        if username:
            data['%s-username' % network] = username
        if password:
            data['%s-password' % network] = password
        if client_key:
            data['%s-client_key' % network] = client_key
        if email:
            data['email'] = True

        # Don't send email when testing is = True
        data['testing'] = True

        self.http_client.fetch(self.get_url('/check?' +
            urllib.urlencode(data)), self.stop)
        # Return the response
        return self.wait(timeout=20)

def _check_response(resp, check_string):
    if check_string == VALID_REQUEST:
        assert resp.body.find(VALID_REQUEST) != -1
        assert AdNetworkLoginCredentials.all().count() == 1

        assert AdNetworkAppMapper.all().count() == 1

        children = multiprocessing.active_children()
        print children
        if children:
            print children[0].pid
            children[0].join()

            # Unfortunately the app engine datastore doesn't play nice with
            # multiprocessing when testing.
#            print AdNetworkScrapeStats.all().count()
#            assert AdNetworkScrapeStats.all().count() == 14
            assert children[0].exitcode == 0
    else:
        assert resp.body.find(INVALID_REQUEST) != -1
        assert AdNetworkLoginCredentials.all().count() == 0

        assert AdNetworkAppMapper.all().count() == 0

def _clear_db():
    db.delete(Account.all())
    db.delete(App.all())
    db.delete(NetworkConfig.all())
    db.delete(AdNetworkLoginCredentials.all())
    db.delete(AdNetworkAppMapper.all())
    db.delete(AdNetworkScrapeStats.all())

