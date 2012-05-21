import unittest

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
        self._create_secondary_account()

        # log in
        self.client.login(username=USERNAME, password=PASSWORD)

    def tearDown(self):
        self.testbed.deactivate()

    @classmethod
    def tearDownClass(cls):
        pass

    def login_secondary_account(self):
        username, password = self._secondary_credentials()
        self.client.login(username=username, password=password)

    def _create_secondary_account(self):
        username, password = self._secondary_credentials()
        generate_account(username, password, username)

    def _secondary_credentials(self):
        return 'username', 'password'
