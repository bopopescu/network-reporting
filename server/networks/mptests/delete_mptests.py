import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase

from common.utils.test.test_utils import confirm_db, \
        model_eq

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
        self.generate_ad_network_login(self.network_type, self.account)
        self.post_data = {'campaign_key': str(self.campaign.key())}

    @confirm_db()
    def mptest_response_code(self):
        """Response code for GET should be 200.

        Author: Tiago Bandeira
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    @confirm_db(modified=[Campaign, AdGroup, Creative,
        AdNetworkLoginCredentials])
    def mptest_delete_campaign(self):
        """Delete a campaign and all associated adgroups, creatives and login
        credentials.

        Author: Tiago Bandeira
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        campaigns = AdvertiserQueryManager.get_campaigns_dict_for_account(
                self.account).values()
        ok_(not campaigns)

        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
                self.account).values()
        ok_(not adgroups)

        creatives = AdvertiserQueryManager.get_creatives_dict_for_account(
                self.account).values()
        ok_(not creatives)

        logins = AdNetworkLoginCredentials.all().get()
        ok_(not logins)

    @confirm_db(modified=[Campaign, AdGroup, Creative])
    def mptest_new_default_campaign_chosen(self):
        """When a default campaign is deleted and other campaigns of this
        network_type exist a new default campaign is chosen.

        Author: Tiago Bandeira
        """
        num_of_custom_campaigns = 2
        for x in range(num_of_custom_campaigns):
            self.generate_network_campaign(self.network_type, self.account,
                    self.existing_apps)
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        campaigns = AdvertiserQueryManager.get_campaigns_dict_for_account(
                self.account).values()
        eq_(len(campaigns), num_of_custom_campaigns)
        ok_([campaign for campaign in campaigns if campaign.network_state == \
                NetworkStates.DEFAULT_NETWORK_CAMPAIGN])

        login = AdNetworkLoginCredentials.all().get()
        ok_(login)

    @confirm_db()
    def mptest_delete_campaign_for_other_account(self):
        """Attempting to delete a campaign for another account should result
        in an error.

        Author: Tiago Bandeira
        """
        expected_campaign = CampaignQueryManager.get(self.campaign.key())

        self.login_secondary_account()
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

        # Verify that the campaign wasn't modified!
        model_eq(CampaignQueryManager.get(self.campaign.key()), expected_campaign)
