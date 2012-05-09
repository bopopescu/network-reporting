import unittest

from django.test import Client
from google.appengine.ext import testbed

from admin.randomgen import (generate_account, generate_app, generate_adunit,
                             USERNAME, PASSWORD)


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
        self.app1 = generate_app(self.account)
        self.app2 = generate_app(self.account)
        self.app3 = generate_app(self.account)
        self.adunit1 = generate_adunit(self.app1, self.account)

        # log in
        self.client.post('/account/login/', {'username': USERNAME,
                                             'password': PASSWORD})

    def tearDown(self):
        self.testbed.deactivate()
