import os
import sys
sys.path.append(os.environ['PWD'])

from datetime import date
import simplejson as json

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse
from common.utils.test.test_utils import confirm_all_models, \
        model_eq

from networks.mptests.network_test_case import NetworkTestCase

from ad_network_reports.models import AdNetworkScrapeStats, \
        AdNetworkAppMapper, \
        LoginStates
from ad_network_reports.query_managers import AdNetworkMapperManager

class ContentFilterViewTestCase(NetworkTestCase):
    """
    Author: Tiago (9/13/2012)
    """

    def setUp(self):
        super(ContentFilterViewTestCase, self).setUp()

        self.url = reverse('login_state')

        self.network_type = 'admob'

        self.post_data = {'account_key': str(self.account.key()),
                          'network_type': self.network_type, }

    def mptest_no_login(self):
        """Verify login_state is 0 if no login exists

        Author: Tiago (9/13/2012)
        """
        response = confirm_all_models(self.client.post,
                                      args=[self.url, self.post_data],
                                      kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},)

        response_json = json.loads(response.content)
        eq_(response_json['login_state'], LoginStates.NOT_SETUP)

    def mptest_login_working(self):
        """Test that a set login state is returned

        Author: Tiago (9/13/2012)
        """
        self.login = self.generate_ad_network_login(self.network_type, self.account)
        self.login.state = LoginStates.WORKING

        response = confirm_all_models(self.client.post,
                                      args=[self.url, self.post_data],
                                      kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},)

        response_json = json.loads(response.content)
        eq_(response_json['login_state'], LoginStates.NOT_SETUP)

