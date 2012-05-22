import unittest

from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed

from admin.randomgen import generate_account, USERNAME, PASSWORD
from advertiser.query_managers import CampaignQueryManager

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

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
                self.account)
        self.marketplace_campaign.put()

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

    @staticmethod
    def test_client_reverse(viewname, urlconf=None, args=None, kwargs=None,
                     current_app=None):
        # django.test.Client uses 'testserver' as the host name.
        url = 'http://testserver'
        url += reverse(viewname, urlconf, args, kwargs, current_app)
        return url
