import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from common.utils.test.test_utils import dict_eq, \
        confirm_all_models
from common.constants import NETWORKS
from networks.mptests.network_test_case import NetworkTestCase

from ad_network_reports.models import LoginStates


class NetworkDetailsTestCase(NetworkTestCase):
    def setUp(self):
        super(NetworkDetailsTestCase, self).setUp()

        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.network_type = self.network_type_to_test()
        self.existing_campaign = self.generate_network_campaign(
                self.network_type, self.account, self.existing_apps)

        self.url = reverse('network_details',
                kwargs={'campaign_key': self.existing_campaign.key()})

    def network_type_to_test(self):
        return 'admob'

    def mptest_context(self):
        """NetworkDetails shall pass a reasonable context to the template.

        Author: Tiago Bandeira
        """
        response = confirm_all_models(self.client.get,
                                      args=[self.url])
        context = response.context

        # The network data dictionary should match expected values. Note: since dict_eq only
        # compares the keys of db.Models, we exclude the 'apps' field from dict_eq.
        dict_eq(context['network'], {'name': self.network_type,
                                     'pretty_name': NETWORKS[self.network_type],
                                     'key': str(self.existing_campaign.key()),
                                     'active': True,
                                     'login_state': LoginStates.NOT_SETUP,
                                     'reporting': False,
                                     'targeting': 'All',
                                     'min_cpm': None,
                                     'max_cpm': None,},
                                     exclude=['apps'])

        eq_(len(context['network']['apps']), len(self.existing_apps))

        # The apps should have the right bids.
        for app, app_bid in context['network']['apps']:
            dict_eq(app_bid, {'min_cpm': None, 'max_cpm': None})

        # TODO: This is essentially the same as context['network']['apps'] and should be refactored.
        eq_(len(context['apps']), len(self.existing_apps))


class AdMobS2SDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'admob_s2s'


class JumpTapDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'jumptap'


class IAdDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'iad'


class InMobiDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'inmobi'


class MobfoxDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'mobfox'


class MillennialDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'millennial'


class MillennialS2SDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'millennial_s2s'


class AdsenseDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'adsense'


class TapItDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'ejam'


class BrightrollDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'brightroll'


class CustomDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'custom'


class CustomNativeDetailsTestCase(NetworkDetailsTestCase):
    def network_type_to_test(self):
        return 'custom_native'
