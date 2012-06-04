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

    @confirm_db(campaign=EDITED_1, adgroup=EDITED_1, creative=EDITED_1,
        adnetwork_login_credentials=EDITED_1)
    def mptest_response_code(self):
        """Response code for GET should be 200.

        Author: Tiago Bandeira
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    def mptest_delete_campaign(self):
        """Delete a campaign and all associated adgroups, creatives and login
        credentials.

        Author: Tiago Bandeira
        """

        marked_as_deleted = [self.campaign.key()] + [adgroup.key() for adgroup
                in self.campaign.adgroups] + [creative.key() for adgroup in
                        self.campaign.adgroups for creative in
                        adgroup.creatives] + [self.login.key()]

        confirm_all_models(self.client.post, args=[self.url, self.post_data],
                kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                marked_as_deleted=marked_as_deleted)


    @confirm_db(campaign=EDITED_1, adgroup=EDITED_1, creative=EDITED_1)
    def mptest_new_default_campaign_chosen(self):
        """When a default campaign is deleted and other campaigns of this
        network_type exist a new default campaign is chosen.

        Author: Tiago Bandeira
        """
        num_of_custom_campaigns = 2
        for x in range(num_of_custom_campaigns):
            self.generate_network_campaign(self.network_type, self.account,
                    self.existing_apps)
        campaigns = CampaignQueryManager.get_network_campaigns(self.account,
                is_new=True)
        print '# of network campaigns: %d' % len(campaigns)
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        campaigns = CampaignQueryManager.get_network_campaigns(self.account,
                is_new=True)
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
        model_eq(CampaignQueryManager.get(self.campaign.key()),
                expected_campaign)
