import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from common.utils.test.fixtures import generate_app, generate_adunit
from common.utils.test.test_utils import confirm_db, model_eq
from common.utils.test.views import BaseViewTestCase


class CampaignQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(CampaignQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)
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
        model_eq(marketplace_campaign, self.marketplace_campaign)

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

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)
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
