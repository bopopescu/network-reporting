# don't remove, necessary to set up the test env
import sys, os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import logging
import unittest
import random
import datetime

from google.appengine.ext import testbed
from google.appengine.api import memcache
from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from nose.tools import eq_
from admin.randomgen import generate_account, generate_app, generate_adunit



setup_test_environment()

# Forms

class AppFormTestCase(unittest.TestCase):
    pass


class AdUnitFormTestCase(unittest.TestCase):
    pass


# View Handlers

class PublisherViewTestCase(unittest.TestCase):
    """
    Sets up (and tears down) some basic stuff you'd need to
    test publisher views (accounts, apps, adunits) and logs
    in the account.
    """
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
        r = self.c.post('/account/login/', {'username':"test@mopub.com",
                                            'password':"test"})


    def tearDown(self):
        self.testbed.deactivate()


class AppIndexViewTestCase(PublisherViewTestCase):
    """
    /inventory/
    """
    def testInventoryPageLoads(self):
        url = 'app_index'
        response = self.c.get(reverse(url))
        eq_(response.status_code, 200)

    def testInventoryContext(self):
        # response = self.c.get(reverse('app_index'))
        # app_keys = response.context[-1]
        # print app_keys
        # expected_app_keys = [app.key() for app in [self.app1, self.app2, self.app3]]
        # eq_(sorted(app_keys), sorted(expected_app_keys))
        pass

    def testStatsForDateRange(self):
        pass

    def testBootstrappingData(self):
        pass

    def testStatsBreakdownData(self):
        pass




class GeoPerformanceViewTestCase(PublisherViewTestCase):
    """
    this view is deprecated
    """
    pass


class AppDetailViewTestCase(PublisherViewTestCase):
    def testAppDetailPageLoads(self):
        url = 'publisher_app_show'
        response = self.c.get(reverse(url, kwargs={'app_key': self.app1.key()}))
        eq_(response.status_code, 200)

    def testStatsForDateRange(self):
        pass

    def testBootstrappingData(self):
        pass

    def testStatsBreakdownData(self):
        pass


class AdUnitDetailViewTestCase(PublisherViewTestCase):
    def testAdUnitDetailPageLoads(self):
        url = 'publisher_adunit_show'
        response = self.c.get(reverse(url, kwargs={'adunit_key': self.adunit1.key()}))
        eq_(response.status_code, 200)

    def testStatsForDateRange(self):
        pass

    def testBootstrappingData(self):
        pass

    def testStatsBreakdownData(self):
        pass


class AppCreateViewTestCase(PublisherViewTestCase):
    def testCreateApp(self):
        pass


class AdUnitCreateViewTestCase(PublisherViewTestCase):
    def testCreateAdUnit(self):
        pass


class ExportViewTestCase(PublisherViewTestCase):
    def testExportApp(self):
        pass

    def testExportAdunit(self):
        pass

    def testExportInventory(self):
        pass


class AppUpdateViewTestCase(PublisherViewTestCase):
    def testAppUpdate(self):
        pass


class AdUnitUpdateViewTestCase(PublisherViewTestCase):
    def testAdunitUpdate(self):
        pass


class AppDeleteViewTestCase(PublisherViewTestCase):
    def testDeleteApp(self):
        pass


class AdUnitDeleteViewTestCase(PublisherViewTestCase):
    def testDeleteAdUnitDelete(self):
        pass


class PublisherViewHelpersTestCase(unittest.TestCase):
    def testCalculateEcpm(self):
        pass


if __name__ == '__main__':
    unittest.main()
