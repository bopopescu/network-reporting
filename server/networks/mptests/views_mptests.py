import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse

from admin.randomgen import generate_app, generate_adunit
from common.utils.test.views import BaseViewTestCase
from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION
from publisher.query_managers import PublisherQueryManager

from networks.forms import NetworkCampaignForm, \
        NetworkAdGroupForm, \
        AdUnitAdGroupForm

from advertiser.models import NetworkStates
from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager

class NetworkEditViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(NetworkEditViewTestCase, self).setUp()

        self.app1 = generate_app(self.account)
        self.adunit1 = generate_adunit(self.app1, self.account)

    def mptest_create_network(self):
        apps_dict = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account)
        self.assertEqual(len(apps_dict), 1)

        # Set constants
        network_type = 'admob'
        campaign_name = NETWORKS[network_type]
        default_bid = 0.05

        url = reverse('edit_network', kwargs={'network': network_type})

        campaign_form = NetworkCampaignForm({'name': campaign_name})
        default_adgroup_form = NetworkAdGroupForm()

        # Create the adgroup forms, one per adunit
        adgroup_forms = []
        for app in apps_dict.values():
            for adunit in app.adunits:
                adgroup_form = AdUnitAdGroupForm({'bid': default_bid},
                        prefix=str(adunit.key()))
                adgroup_forms.append(adgroup_form)

        # Create the data dict, each adgroup form per adunit must have a prefix,
        # so we can post multiple adgroup forms, which is the adunit key
        adunit_data = [('%s-%s' % (adgroup_form.prefix, key), item) for \
                adgroup_form in adgroup_forms for key, item in \
                adgroup_form.data.items()]
        data = campaign_form.data.items() + default_adgroup_form. \
                data.items() + adunit_data
        data = dict(data)

        # Header HTTP_X_REQUESTED_WITH is set to XMLHttpRequest to mimic an
        # ajax request
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=
                'XMLHttpRequest')

        # Print the response
        print 'RESPONSE'
        print response
        print response.__dict__

        self.assertEqual(response.status_code, 200)

        # New campaign in memcache?
        network_campaigns = CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True)
        self.assertEqual(len(network_campaigns), 1)

        # Is the campaign set up properly?
        campaign = network_campaigns[0]
        self.assertEqual(campaign.network_type, network_type)
        self.assertEqual(campaign.network_state, NetworkStates.
                DEFAULT_NETWORK_CAMPAIGN)

        # Was one adgroup per app created and are the created adgroups set up
        # properly?
        for app in apps_dict.values():
            for adunit in app.adunits:
                adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                        adunit.key(), self.account.key(), get_from_db=True)
                self.assertTrue(adgroup)
                self.assertEqual(adgroup.network_type,
                        NETWORK_ADGROUP_TRANSLATION[network_type])
                self.assertEqual(adgroup.bid, default_bid)

