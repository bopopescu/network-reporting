import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase

from common.constants import NETWORKS

from account.query_managers import AccountQueryManager

class NetworksTestCase(NetworkTestCase):
    def setUp(self):
        super(NetworksTestCase, self).setUp()

        self.account.display_new_networks = True
        AccountQueryManager.put(self.account)

        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        for network_type in NETWORKS:
            self.generate_network_campaign(network_type, self.account,
                    self.existing_apps)

        self.url = reverse('networks')

    def mptest_response_code(self):
        """Networks shall return a valid status code.

        Author: Tiago Bandeira
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)
