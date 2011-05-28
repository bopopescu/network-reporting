import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from ad_server.networks.ejam import EjamServerSide
import unittest


from account.models import Account, NetworkConfig

from publisher.models import App
from publisher.models import Site as AdUnit

from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )


from google.appengine.ext import testbed

from google.appengine.api import urlfetch

class MoceanUnitTests(unittest.TestCase):
    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # Set up default models
        self.account = Account()
        self.account.put()

        self.app = App(account=self.account, name="Test App")
        self.app.put()

        self.network_config = NetworkConfig(ejam_pub_id = '23710')
        self.network_config.put()
        
        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit", network_config=self.network_config)
        self.adunit.put()

    def tearDown(self):
        self.testbed.deactivate()
    
    def mptest_mocean_basictest(self):
        request = Request(dict(REQUEST_METHOD = 'get',
                        QUERY_STRING   = '',
                        HTTP_USER_AGENT = 'FakeAndroidOS',
                        SERVER_NAME = 'localhost',
                        SERVER_PORT = 8000,
                       ))
        mocean = EjamServerSide(request, self.adunit)
        url = mocean.url
        url += "&test=1"
        print url
        
        response = urlfetch.fetch(url)
        
        print response.content
        
        response_tuple = mocean.bid_and_html_for_response(response)
        
        print response_tuple
        assert(response_tuple[1])