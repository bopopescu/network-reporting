import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

from networks.mptests.network_test_case import NetworkTestCase


class NetworkDetailsTestCase(NetworkTestCase):
    def setUp(self):
        super(NetworkDetailsTestCase, self).setUp()

        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.network_type = self.network_type_to_test()
        campaign = self.generate_network_campaign(self.network_type, self.account,
                self.existing_apps)

        self.url = reverse('network_details',
                kwargs={'campaign_key': campaign.key()})

    def network_type_to_test(self):
        return 'admob'

    def mptest_response_code(self):
        """Networks shall return a valid status code.

        Author: Tiago Bandeira
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)


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
