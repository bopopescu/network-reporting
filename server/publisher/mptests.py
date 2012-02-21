"""
Interaction tests for the mopub front-end. Interaction tests
use a live browser to test user actions like clicks, entering
and changing data, and navigation.

The tests in this module use selenium (http://seleniumhq.org/)
and assume a running selenium server on localhost. You'll also
have to have firefox installed.
"""

import unittest
import random

# Forms

class AppFormTestCase(unittest.TestCase):
    pass


class AdUnitFormTestCase(unittest.TestCase):
    pass


# View Handlers

class AppIndexViewTestCase(unittest.TestCase):
    pass

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

if __name__ == '__main__':
    unittest.main()