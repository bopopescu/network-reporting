import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from google.appengine.ext import db

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

# Model imports
from account.models import Account, \
        NetworkConfig
from publisher.models import App, \
        AdUnit
from advertiser.models import Campaign, \
        AdGroup, \
        Creative
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper

DEFAULT_BID = 0.05

class NetworkEditViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(NetworkEditViewTestCase, self).setUp()

        app1 = generate_app(self.account)
        adunit1 = generate_adunit(app1, self.account)

    def mptest_create_simple_default_admob_network(self):
        """
        Create a default admob campaign with one app and adunit.

        Author: Tiago Bandeira
        """
        network_type = 'admob'
        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), 1)

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type, apps)

    def mptest_create_simple_custom_network(self):
        """
        Create custom network campaign.

        Author: Tiago Bandeira
        """
        network_type = 'custom'
        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), 1)

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type, apps,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

    def mptest_create_simple_admob_custom_network(self):
        """
        Create custom network campaigns of all types excluding custom and
        custom_native with one app and adunit.

        Author: Tiago Bandeira
        """
        network_type = 'admob'
        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), 1)

        # Create default admob campaign
        default_campaign = CampaignQueryManager.get_default_network_campaign(
                self.account, network_type)
        default_campaign.put()

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type, apps,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                other_campaigns=[default_campaign])

    def mptest_create_complex_default_networks(self):
        """
        Create default network campaigns of all types with multiple apps and
        adunits.

        Author: Tiago Bandeira
        """
        pass

## Helpers
#
def setup_and_make_request(test_case, network_type, apps, default_bid=
        DEFAULT_BID):
    """
    Setup and make the request to create a network campaign

    Author: Tiago Bandeira
    """
    # Set constants
    campaign_name = NETWORKS[network_type]
    url = reverse('edit_network', kwargs={'network': network_type})

    campaign_form = NetworkCampaignForm({'name': campaign_name})
    default_adgroup_form = NetworkAdGroupForm()

    # Create the adgroup forms, one per adunit
    adgroup_forms = []
    for app in apps:
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
    response = test_case.client.post(url, data, HTTP_X_REQUESTED_WITH=
            'XMLHttpRequest')

    # Print the response
    print 'RESPONSE'
    print response
    print response.__dict__

    return response

def check_response(test_case, response, network_type, apps,
        default_bid=DEFAULT_BID, network_state=NetworkStates.
        DEFAULT_NETWORK_CAMPAIGN, other_campaigns=[]):
    """
    Validate the response

    Author: Tiago Bandeira
    """
    test_case.assertEqual(response.status_code, 200)

    # New campaign in memcache?
    network_campaigns = CampaignQueryManager.get_network_campaigns(
            test_case.account, is_new=True)
    test_case.assertEqual(len(network_campaigns) - len(other_campaigns), 1)

    # Is the campaign set up properly?
    campaign = [campaign for campaign in network_campaigns if campaign.key() \
            not in [other_campaign.key() for other_campaign in \
                    other_campaigns]][0]
    test_case.assertEqual(campaign.network_type, network_type)
    test_case.assertEqual(campaign.network_state, network_state)

    # Was one adgroup per app created and are the created adgroups set up
    # properly?
    for app in apps:
        for adunit in app.adunits:
            adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                    adunit.key(), test_case.account.key(), get_from_db=True)
            test_case.assertTrue(adgroup)
            test_case.assertEqual(adgroup.network_type,
                    NETWORK_ADGROUP_TRANSLATION.get(network_type, network_type))
            test_case.assertEqual(adgroup.bid, default_bid)

