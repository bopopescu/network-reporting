__doc__="""
Tests query managers for advertiser app -- orders, marketplace, networks.

Author: Haydn Dufrene and John Pena
"""


# don't remove, necessary to set up the test env
import sys
import os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from common.utils.test.test_utils import (dict_eq, time_almost_eq, 
                                          model_eq, model_key_eq, 
                                          confirm_db, decorate_all_test_methods)

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager)

from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_
import unittest

setup_test_environment()

class QueryManagerTestCase(unittest.TestCase):

    PRIMARY_CREDENTIALS = {
        'username': 'test_primary@mopub.com',
        'password': 'lulzhax',
    }

    SECONDARY_CREDENTIALS = {
        'username': 'test_secondary@mopub.com',
        'password': 'lulzhax',
    }

    
    @classmethod
    def setUpClass(cls):
        pass
        
    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_user_stub()

        self.account = generate_account(**self.PRIMARY_CREDENTIALS)
        self.secondary_account = generate_account(**self.SECONDARY_CREDENTIALS)
        
    def tearDown(self):
        self.testbed.deactivate()

    @classmethod
    def tearDownClass(cls):
        pass


class DirectSoldQueryManagerTestCase(unittest.TestCase):

    def setUp(self):
        super(DirectSoldQueryManagerTestCase, self).setUp()

        self.order = generate_campaign(self.account)
        self.line_item = generate_adgroup(self.order, [],
                                          self.account, 'gtee')

    def campaign_query_manager_gets_orders_mptest(self):
        # Generate some non-order campaigns

        # Assure that the query manager `get_order_campaigns` method
        # only gets the orders.
        orders = CampaignQueryManager.get_order_campaigns(self.account)
        for order in orders:
            ok_(order.is_order)
            ok_(not order.is_marketplace)
            ok_(not order.is_network)
        

    def adgroups_query_manager_gets_all_line_items_mptest(self):
        
        line_items = AdGroupQueryManager.get_line_items(self.account)
        eq_(len(line_items), 1)
        
    def adgroups_query_manager_gets_all_line_items_for_order_mptest(self):

        line_items = AdGroupQueryManager.get_line_items(self.account,
                                                        order=self.order)

        eq_(len(line_items), 1)

    def adgroups_query_manager_gets_all_line_items_for_multiple_orders_mptest(self):
        
        line_items = AdGroupQueryManager.get_line_items(self.account)
        eq_(len(line_items), 1)

        
class MarketplaceQueryManagerTestCase(unittest.TestCase):
    pass


class NetworkQueryManagerTestCase(unittest.TestCase):
    pass