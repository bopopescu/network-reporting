import unittest

from django.test import Client
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed

from admin.randomgen import generate_account, USERNAME, PASSWORD


setup_test_environment()


class BaseViewTestCase(unittest.TestCase):
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
        self.client.post('/account/login/', {'username': USERNAME,
                                             'password': PASSWORD})

    def tearDown(self):
        self.testbed.deactivate()
