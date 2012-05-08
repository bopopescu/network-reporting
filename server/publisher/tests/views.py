# don't remove, necessary to set up the test env
import sys, os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import logging
import unittest
import random
import datetime

from google.appengine.ext import testbed
#from google.appengine.api import memcache
from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from nose.tools import eq_
from admin.randomgen import generate_account, generate_app, generate_adunit


class BaseViewTestCase(unittest.TestCase):
    def setUp(self):
        # bootstrap the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.c = Client()

        # set up some data for testing
        self.account = generate_account()
        self.app1 = generate_app(self.account)
        self.app2 = generate_app(self.account)
        self.app3 = generate_app(self.account)
        self.adunit1 = generate_adunit(self.app1, self.account)

        # log us in
        self.c.post('/account/login/', {'username': "test@mopub.com",
                                        'password': "test"})

    def tearDown(self):
        self.testbed.deactivate()


class AppIndexViewTestCase(BaseViewTestCase):
    """
    /inventory/
    """
    def testInventoryPageLoads(self):
        url = reverse('app_index')
        logging.error(url)
        response = self.c.get(url)
        logging.error(response)
        eq_(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()
