import sys, os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import django
import unittest
import random
import datetime

from google.appengine.ext import testbed
from google.appengine.api import memcache

from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login

from nose.tools import eq_

from account.models import Account, MarketPlaceConfig, NetworkConfig
from account.query_managers import AccountQueryManager
from registration.models import RegistrationManager
from admin.randomgen import generate_account


import warnings
warnings.filterwarnings("ignore")

setup_test_environment()

# Forms

class AppFormTestCase(unittest.TestCase):
    pass


class AdUnitFormTestCase(unittest.TestCase):
    pass


# View Handlers

class AppIndexViewTestCase(unittest.TestCase):
    """
    /inventory/
    """
    def setUp(self):
        # bootstrap the test environment
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_user_stub()

        self.account = generate_account()
        setCurrentUser('test@mopub.com', 'test')

        self.c = Client()
        self.c.login(username="test@mopub.com", password="test")
        self.name = "app_index"

    def tearDown(self):
        self.testbed.deactivate()

    def login(self):
        pass

    def testFuckThis(self):
        response = self.c.get(reverse(self.name))
        print response.context
        eq_(response.status_code, 200)


class GeoPerformanceViewTestCase(unittest.TestCase):
    pass

class AppDetailViewTestCase(unittest.TestCase):
    pass

class AdUnitDetailViewTestCase(unittest.TestCase):
    pass

class AppCreateViewTestCase(unittest.TestCase):
    pass

class AdUnitCreateViewTestCase(unittest.TestCase):
    pass

class ExportViewTestCase(unittest.TestCase):
    pass

class AppUpdateViewTestCase(unittest.TestCase):
    pass

class AdUnitUpdateViewTestCase(unittest.TestCase):
    pass

class AppDeleteViewTestCase(unittest.TestCase):
    pass

class AdUnitDeleteViewTestCase(unittest.TestCase):
    pass

class PublisherViewHelpersTestCase(unittest.TestCase):
    pass


import os

def setCurrentUser(email, user_id='1', is_admin=False):
    os.environ['USER_EMAIL'] = email or ''
    os.environ['USER_ID'] = user_id or ''
    os.environ['USER_IS_ADMIN'] = '1' if is_admin else '0'

def logoutCurrentUser():
    setCurrentUser(None, None)

if __name__ == '__main__':
    unittest.main()