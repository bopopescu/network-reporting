import sys
import urllib

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
from account.models import Account, NetworkConfig
from publisher.models import App

TEST_JUMPTAP_PUB_ID = 'pa_zaphrox_zaphrox_drd_app'
TEST_ADMOB_PUB_ID = 'a14cf615dc654dd'
TEST_IAD_PUB_ID = '329218549'
TEST_INMOBI_PUB_ID ='4028cba630724cd90130c2adc9b6024f'
TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

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

    def mptest_handler_empty_test(self):
        try:
            response = self.fetch('/check')
        except:
            assert False

    def mptest_jumptap_handler_test(self):
        # create test models
        account = Account()
        account.put()

        network_config = NetworkConfig(jumptap_pub_id=TEST_JUMPTAP_PUB_ID,
                admob_pub_id=TEST_ADMOB_PUB_ID, iad_pub_id=TEST_IAD_PUB_ID,
                inmobi_pub_id=TEST_INMOBI_PUB_ID,
                mobfox_pub_id=TEST_MOBFOX_PUB_ID)
        network_config.put()

        app = App(account=account, name="BET WAP Site", network_config=
                network_config)
        app.put()

        data = {'account_key': str(account.key()),
                'callback': 'jQuery_function_name',
                'ad_network_name': 'jumptap',
                'jumptap-username': 'zaphrox',
                'jumptap-password': 'JR.7x89re0'}

        resp = self.fetch('/check?' + urllib.urlencode(data), method='GET', request_timeout=20)

        assert resp.body.find('true') != -1
        assert AdNetworkLoginCredentials.all().count() == 1

        assert AdNetworkAppMapper.all().count() == 1

        assert AdNetworkScrapeStats.all().count() == 14

    def mptest_admob_handler_test(self):
        # create test models
        account = Account()
        account.put()

        network_config = NetworkConfig(jumptap_pub_id=TEST_JUMPTAP_PUB_ID,
                admob_pub_id=TEST_ADMOB_PUB_ID, iad_pub_id=TEST_IAD_PUB_ID,
                inmobi_pub_id=TEST_INMOBI_PUB_ID,
                mobfox_pub_id=TEST_MOBFOX_PUB_ID)
        network_config.put()

        app = App(account=account, name="BET WAP Site", network_config=
                network_config)
        app.put()

        data = {'account_key': str(account.key()),
                'callback': 'jQuery_function_name',
                'ad_network_name': 'admob',
                'admob-username': 'adnetwork@com2usamerica.com',
                'admob-password': '4w47m82l5jfdqw1x',
                'admob-client_key': 'ka820827f7daaf94826ce4cee343837a'}

        resp = self.fetch('/check?' + urllib.urlencode(data), method='GET', request_timeout=20)

        assert resp.body.find('true') != -1
        assert AdNetworkLoginCredentials.all().count() == 1

        assert AdNetworkAppMapper.all().count() == 1

        assert AdNetworkScrapeStats.all().count() == 14

def _clear_db():
    db.delete(Account.all())
    db.delete(App.all())
    db.delete(NetworkConfig.all())
    db.delete(AdNetworkLoginCredentials.all())
    db.delete(AdNetworkAppMapper.all())
    db.delete(AdNetworkScrapeStats.all())

