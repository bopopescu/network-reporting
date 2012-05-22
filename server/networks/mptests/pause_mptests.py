import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup
from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase

from advertiser.query_managers import CampaignQueryManager
from common.utils.test.test_utils import decorate_all_test_methods, \
        confirm_db


@decorate_all_test_methods(confirm_db())
class PauseNetworkTestCase(NetworkTestCase):
    def setUp(self):
        super(PauseNetworkTestCase, self).setUp()

        self.url = reverse('pause_network')

        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        # all network campaigns are treated the same
        network_type = 'admob'
        self.campaign = self.generate_network_campaign(network_type,
                self.account, self.existing_apps)

        self.campaign.put()
        self.post_data = {'campaign_key': self.campaign.key(),
                          'active': True}

    def mptest_response_code(self):
        """When adding a network campaign, response code should be 200.

        Author: Tiago Bandeira
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)


    def mptest_activate_campaign(self):
        """Activate campaign.

        Author: Tiago Bandeira
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.campaign = CampaignQueryManager.get(self.campaign.key())
        eq_(self.campaign.active, True)

    def mptest_pause_campaign(self):
        """Pause campaign.

        Author: Tiago Bandeira
        """
        del(self.post_data['active'])
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.campaign = CampaignQueryManager.get(self.campaign.key())
        eq_(self.campaign.active, False)

    def mptest_activate_campaign_for_other_account(self):
        """Attempting to activate a campaign for another account should result
        in an error.

        Author: Tiago Bandeira
        """
        self.login_secondary_account()
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)
