import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup
from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase

from advertiser.query_managers import CampaignQueryManager
from common.utils.test.test_utils import confirm_all_models


#@decorate_all_test_methods(confirm_db())
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

    def mptest_no_change_campaign(self):
        """No change.

        Author: Tiago Bandeira
        """
        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

    def mptest_activate_campaign(self):
        """Activate campaign.

        Author: Tiago Bandeira
        """
        self.campaign.active = False
        CampaignQueryManager.put(self.campaign)

        edited = {self.campaign.key(): {'active': True}}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           edited=edited)

    def mptest_pause_campaign(self):
        """Pause campaign.

        Author: Tiago Bandeira
        """
        del(self.post_data['active'])

        edited = {self.campaign.key(): {'active': False}}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           edited=edited)

    def mptest_activate_campaign_for_other_account(self):
        """Attempting to activate a campaign for another account should result
        in an error.

        Author: Tiago Bandeira
        """
        self.login_secondary_account()
        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           response_code=404)

