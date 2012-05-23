import unittest

from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed

from common.utils.test.fixtures import generate_account

setup_test_environment()


class BaseViewTestCase(unittest.TestCase):

    PRIMARY_CREDENTIALS = {
        'username': 'test_primary@mopub.com',
        'password': 'lulzhax',
    }

    SECONDARY_CREDENTIALS = {
        'username': 'test_secondary@mopub.com',
        'password': 'lulzhax',
    }

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        # setup the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.client = Client()

        # generate data
        self.account = generate_account(**self.PRIMARY_CREDENTIALS)
        self.secondary_account = generate_account(**self.SECONDARY_CREDENTIALS)

        # log in
        self.login_primary_account()

    def tearDown(self):
        self.testbed.deactivate()

    @classmethod
    def tearDownClass(cls):
        pass

    def login_primary_account(self):
        self.client.login(**self.PRIMARY_CREDENTIALS)

    def login_secondary_account(self):
        self.client.login(**self.SECONDARY_CREDENTIALS)

    @staticmethod
    def test_client_reverse(viewname, urlconf=None, args=None, kwargs=None,
                     current_app=None):
        # django.test.Client uses 'testserver' as the host name.
        url = 'http://testserver'
        url += reverse(viewname, urlconf, args, kwargs, current_app)
        return url
