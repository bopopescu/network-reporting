import unittest

from django.test import Client
from django.test.utils import setup_test_environment
from google.appengine.ext import testbed

from admin.randomgen import generate_account, USERNAME, PASSWORD


setup_test_environment()


class BaseViewTestCase(unittest.TestCase):
    model_types = [Account, App, AdUnit, Campaign, AdGroup, Creative]

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

    def dict_eq(self, dict1, dict2):
        eq_(dict1.keys(), dict2.keys())

        for key in dict1.keys():
            # Possibly refactor to include more type comparisons.
            eq_(dict1[key], dict2[key])

    def model_eq(self, model1, model2):
        eq_(model1.key(), model2.key())
