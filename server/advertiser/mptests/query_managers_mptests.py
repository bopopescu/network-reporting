__doc__ = """
Tests query managers for advertiser app -- orders, marketplace, networks.

Author: Haydn Dufrene and John Pena
"""

import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager)
from common.utils.test.fixtures import (generate_app, generate_adunit,
                                        generate_campaign, generate_adgroup)
from common.utils.test.test_utils import confirm_db, model_eq
from common.utils.test.views import BaseViewTestCase


setup_test_environment()


class CampaignQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(CampaignQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        self.marketplace_campaign.put()

        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

    @confirm_db()
    def mptest_get_marketplace_campaign_not_from_db(self):
        """
        Get marketplace campaign by creating it and confirm it has the correct
        properties.
        """

        marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        model_eq(marketplace_campaign, self.marketplace_campaign, ['created'],
                 False)

    @confirm_db()
    def mptest_get_marketplace_campaign_from_db(self):
        """
        Get marketplace campaign from the db and confirm it has the correct
        properties.
        """

        marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account, from_db=True)
        model_eq(marketplace_campaign, self.marketplace_campaign)


class AdGroupQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdGroupQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        self.marketplace_campaign.put()

        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

    @confirm_db()
    def mptest_get_marketplace_adgroup_not_from_db(self):
        """
        Get marketplace adgroup for our adunit by creating it and confirm it has
        the correct properties.
        """

        marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key())
        model_eq(marketplace_adgroup, self.marketplace_adgroup,
                 check_primary_key=False, exclude=['created', 't'])

    @confirm_db()
    def mptest_get_marketplace_adgroup_from_db(self):
        """
        Get marketplace adgroup for our adunit from the db and confirm it has
        the correct properties.
        """

        marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key(), get_from_db=True)
        model_eq(marketplace_adgroup, self.marketplace_adgroup)


class DirectSoldQueryManagerTestCase(BaseViewTestCase):
    def setUp(self):
        super(DirectSoldQueryManagerTestCase, self).setUp()

        self.order = generate_campaign(self.account, True)
        self.line_item = generate_adgroup(self.account, self.order, True,
                                          adgroup_type='gtee')

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


class MarketplaceQueryManagerTestCase(BaseViewTestCase):
    pass


class NetworkQueryManagerTestCase(BaseViewTestCase):
    pass
