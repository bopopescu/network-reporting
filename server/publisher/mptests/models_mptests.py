import os
import sys
import unittest

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.test.utils import setup_test_environment
from nose.tools import eq_

from publisher.models import App


setup_test_environment()


GLOBAL_ID_TESTS = [
    ('android', '', '', None),
    ('android', '', 'com.company.appname', 'com.company.appname'),
    ('android', 'http://itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', None),
    ('iphone', '', '', None),
    ('iphone', '', 'com.company.appname', None),
    ('iphone', 'http://itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', '415569164'),
    ('iphone', 'http://itunes.apple.com/us/app/tap-pet-hotel/ID415569164?mt=8', '', '415569164'),
    ('iphone', 'http://itunes.apple.com/us/app/tap-pet-hotel/id?mt=8', '', None),
    ('ipad', '', '', None),
    ('ipad', '', 'com.company.appname', None),
    ('ipad', 'http://itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', '415569164'),
    ('ipad', 'http://itunes.apple.com/us/app/tap-pet-hotel/ID415569164?mt=8', '', '415569164'),
    ('ipad', 'http://itunes.apple.com/us/app/tap-pet-hotel/id?mt=8', '', None),
    ('mweb', '', '', None),
    ('mweb', '', 'com.company.appname', None),
    ('mweb', 'itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', 'itunes.apple.com'),
    ('mweb', 'www.itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', 'itunes.apple.com'),
    ('mweb', 'http://itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', 'itunes.apple.com'),
    ('mweb', 'http://www.itunes.apple.com/us/app/tap-pet-hotel/id415569164?mt=8', '', 'itunes.apple.com'),
]


class AppModelTestCase(unittest.TestCase):
    """
    Author: Peter
    """

    def mptest_global_id(self):
        """
        Confirm that global_id returns the correct value for different
        app_types, urls, and packages.
        """

        ERROR_MESSAGE = ("global_id was %(global_id)s but should have been " +
            "%(expected_global_id)s for app_type=%(app_type)s, url=%(url)s, " +
            "and package=%(package)s.")

        for app_type, url, package, expected_global_id in GLOBAL_ID_TESTS:
            app = App(name='Test App', app_type=app_type, url=url, package=package)
            eq_(app.global_id, expected_global_id, ERROR_MESSAGE % {
                'global_id': app.global_id,
                'expected_global_id': expected_global_id,
                'app_type': app_type,
                'url': url,
                'package': package
            })
