import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase

from common.utils.test.test_utils import confirm_db, \
        model_eq, EDITED_1, DELETED_1, confirm_all_models

from advertiser.query_managers import AdvertiserQueryManager, \
        CampaignQueryManager

from advertiser.models import NetworkStates, \
        Campaign, \
        AdGroup, \
        Creative
from ad_network_reports.models import AdNetworkLoginCredentials

class DeleteNetworkTestCase(NetworkTestCase):
    def setUp(self):
        super(DeleteNetworkTestCase, self).setUp()

        self.url = reverse('delete_network')

        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.network_type = 'admob'
        self.campaign = self.generate_network_campaign(self.network_type,
                self.account, self.existing_apps)
        self.login = self.generate_ad_network_login(self.network_type,
                self.account)
        self.post_data = {'campaign_key': str(self.campaign.key())}


    def mptest_delete_campaign(self):
        """Delete a campaign and all associated adgroups, creatives and login
        credentials.

        Author: Tiago Bandeira
        """

        marked_as_deleted = [self.campaign.key()] + [adgroup.key() for adgroup
                in self.campaign.adgroups] + [creative.key() for adgroup in
                        self.campaign.adgroups for creative in
                        adgroup.creatives] + [self.login.key()]

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           marked_as_deleted=marked_as_deleted)


    def mptest_new_default_campaign_chosen(self):
        """When a default campaign is deleted and other campaigns of this
        network_type exist a new default campaign is chosen.

        Author: Tiago Bandeira
        """
        num_of_custom_campaigns = 1
        additional_campaigns = []
        for x in range(num_of_custom_campaigns):
            additional_campaigns.append(self.generate_network_campaign(
                self.network_type, self.account, self.existing_apps))

        marked_as_deleted = [self.campaign.key()] + [adgroup.key() for adgroup
                in self.campaign.adgroups] + [creative.key() for adgroup in
                        self.campaign.adgroups for creative in
                        adgroup.creatives]

        edited = {additional_campaigns[0].key(): {'network_state':
            NetworkStates.DEFAULT_NETWORK_CAMPAIGN}}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           marked_as_deleted=marked_as_deleted,
                           edited=edited)


    def mptest_delete_campaign_for_other_account(self):
        """Attempting to delete a campaign for another account should result
        in an error.

        Author: Tiago Bandeira
        """
        expected_campaign = CampaignQueryManager.get(self.campaign.key())

        self.login_secondary_account()
        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           response_code=404)
