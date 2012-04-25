import os
import sys

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from ad_server.networks.chartboost import ChartBoostServerSide
import unittest


from account.models import Account, NetworkConfig

from publisher.models import App
from publisher.models import Site as AdUnit

from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )


from google.appengine.ext import testbed

from google.appengine.api import urlfetch

class ChartBoostUnitTests(unittest.TestCase):
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

        self.network_config = NetworkConfig(chartboost_pub_id = '4de55942bb93162f4500006c')
        self.network_config.put()
        
        self.adunit = AdUnit(account=self.account, app_key=self.app, name="Test AdUnit", network_config=self.network_config)
        self.adunit.put()

    def tearDown(self):
        self.testbed.deactivate()
    
    def chartboost_basictest(self):     
        """ DISABLED due to chartboost not returning pings. 
            prefix with MPTEST to undisable"""
        request = Request(dict(REQUEST_METHOD = 'get',
                        QUERY_STRING   = '',
                        SERVER_NAME = 'localhost',
                        SERVER_PORT = 8000,
                       ))
        chartboost = ChartBoostServerSide(request, self.adunit)
        url = chartboost.url
        response = urlfetch.fetch(url)
       
        response_tuple = chartboost.bid_and_html_for_response(response)
        
        assert False
        
        assert(response_tuple[1]=="""<div style=\'text-align:center\'><a href="http://www.chartboost.com/api/banner_click.json?app=4de55942bb93162f4500006c&uuid=467A52DB6F573AC18431045FB136B22E" target="_blank"><img src="https://s3.amazonaws.com/chartboost/banners/banner_ad_tapzoo.jpg"/></a></div>""")
