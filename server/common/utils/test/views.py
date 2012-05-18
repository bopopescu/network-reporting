import unittest

from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed

from admin.randomgen import generate_account, USERNAME, PASSWORD


setup_test_environment()


class BaseViewTestCase(unittest.TestCase):

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
        self.account = generate_account()

        # log in
        self.client.login(username=USERNAME, password=PASSWORD)

    def tearDown(self):
        self.testbed.deactivate()

    @classmethod
    def tearDownClass(cls):
        pass

    def login_secondary_account(self):
        username = 'user@domain.com'
        password = 'password'
        generate_account(username, password, username)

        self.client.login(username=username, password=password)

    @staticmethod
    def test_client_reverse(viewname, urlconf=None, args=None, kwargs=None,
                     current_app=None):
        # django.test.Client uses 'testserver' as the host name.
        url = 'http://testserver'
        url += reverse(viewname, urlconf, args, kwargs, current_app)
        return url
