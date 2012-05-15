import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import nottest

from django.core.urlresolvers import reverse
from google.appengine.ext import db

from admin.randomgen import generate_app, generate_adunit
from common.utils.test.views import BaseViewTestCase
from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION, \
        REPORTING_NETWORKS
from publisher.query_managers import PublisherQueryManager

from networks.views import NETWORKS_WITH_PUB_IDS
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

from account.query_managers import AccountQueryManager

DEFAULT_BID = 0.05
DEFAULT_HTML = 'html_data1'
DEFAULT_PUB_ID = 'pub_id'

class CreateSimpleNetworkTestCase(BaseViewTestCase):
    _multiprocess_can_split = True
    def setUp(self):
        super(CreateSimpleNetworkTestCase, self).setUp()

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

        # Andrew: Tiago, does this assertion need to be here? It's basically
        # testing randomgen...
        self.assertEqual(len(apps), 1)

        response = setup_and_make_request(self, network_type, apps)

        # Begin test verification.
        # Andrew: I didn't set instance variables (e.g. self.apps) because
        # it's easier to figure out where the variables are being set.
        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        network_campaigns = CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True)
        new_campaign = network_campaigns[0]

        self.check_status_code(response)
        self.check_new_campaign_exists(new_campaign)

        # Andrew: Is this test even necessary?
        # self.check_campaign_should_be_added_to_memcache()

        # Andrew: Tiago, what's your opinion on named arguments? We might want
        # to decide whether the check_ methods should take them for clarity.
        self.check_campaign_init(new_campaign, network_type=network_type,
                network_state=NetworkStates.DEFAULT_NETWORK_CAMPAIGN)
        self.check_campaign_has_network_key_name(new_campaign,
                network_type=network_type)
        self.check_app_network_configs(apps, network_type)
        self.check_app_mappers(apps, network_type)
        self.check_adunit_network_configs(apps, network_type)
        self.check_adunits_adgroups(apps, new_campaign, network_type,
                DEFAULT_BID)
        self.check_onboarding_status_finished()

    @nottest
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

        check_response(self, response, network_type,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

    @nottest
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

        check_response(self, response, network_type,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                other_campaigns=[default_campaign])

    def check_status_code(self, response):
        """Checks that the response's status code is 200.

        Author: Andrew He
        """
        self.assertEqual(response.status_code, 200)
    
    def check_new_campaign_exists(self, campaign):
        self.assertTrue(campaign)

    def check_campaign_should_be_added_to_memcache(self, network_campaigns,
            existing_campaigns):
        """Checks that the new campaign is present in memcache.

        Author: Andrew He
        """
        num_campaigns_before = len(existing_campaigns)
        num_campaigns_after = len(network_campaigns)
        self.assertEqual(num_campaigns_after - num_campaigns_before, 1)

    def check_campaign_init(self, campaign, network_type=None,
            network_state=None):
        """Checks that the new campaign has the right initial properties.

        Author: Andrew He
        """
        self.assertEqual(campaign._account, self.account.key())
        self.assertEqual(campaign.campaign_type, 'network')
        self.assertEqual(campaign.network_type, network_type)
        self.assertEqual(campaign.network_state, network_state)

    def check_campaign_has_network_key_name(self, campaign, network_type=None):
        """Checks that the new campaign has the right key name.

        Author: Andrew He
        """
        # Is the key_name set for the default network campaign?
        self.assertTrue(campaign.key().name())
        # Is the key name in the form ntwk:<account_key>:<network_type>?
        self.assertEqual(campaign.key().name(), 'ntwk:%s:%s' %
                (self.account.key(), network_type))

    def check_app_network_configs(self, apps, network_type):
        """Checks that the app-level network configs were updated.

        Author: Andrew He
        """
        for index, app in enumerate(apps):
            self.assertTrue(app.network_config)
            self.assertEqual(getattr(app.network_config, '%s_pub_id' %
                    network_type), DEFAULT_PUB_ID + str(index))

    def check_app_mappers(self, apps, network_type):
        """Checks that the apps have AdNetworkAppMappers.

        Author: Andrew He
        """
        for index, app in enumerate(apps):
            mapper = AdNetworkAppMapper.all().filter('application =', app). \
                    filter('ad_network_name =', network_type).get()
            self.assertTrue(mapper)
            self.assertEqual(mapper.publisher_id, DEFAULT_PUB_ID + str(index))

    def check_adunit_network_configs(self, apps, network_type):
        """Checks that the adunit-level network configs were updated.

        Author: Andrew He
        """
        for app in apps:
            for adunit in app.adunits:
                self.assertTrue(hasattr(adunit, 'network_config'))
                self.assertEqual(getattr(adunit.network_config, '%s_pub_id' %
                            network_type), DEFAULT_PUB_ID)

    def check_adunits_adgroups(self, apps, campaign, network_type, default_bid):
        """Checks that each adgroup corresponds to one adunit.

        Author: Andrew He
        """
        for app in apps:
            for adunit in app.adunits:
                adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                            adunit.key(), self.account.key(), get_from_db=True)
                self.assertTrue(adgroup)
                self.assertEqual(adgroup.network_type,
                        NETWORK_ADGROUP_TRANSLATION.get(network_type, network_type))
                self.assertEqual(adgroup.bid, default_bid)

                creatives = list(adgroup.creatives)
                self.assertEqual(len(creatives), 1)
                creative = creatives[0]
                self.assertEqual(creative._account, self.account.key())
                self.assertEqual(creative.__class__,
                        adgroup.default_creative().__class__)

    def check_onboarding_status_finished(self):
        """Checks that the onboarding status is set to ''.

        Author: Andrew He
        """
        self.assertEqual(AccountQueryManager.get(self.account.key()).status, '')

NUM_APPS = 5
NUM_ADUNITS_PER_APP = 5
class CreateComplexNetworkTestCase(BaseViewTestCase):
    def setUp(self):
        super(CreateComplexNetworkTestCase, self).setUp()

        for app_index in range(NUM_APPS):
            app = generate_app(self.account)
            for adunit_index in range(NUM_ADUNITS_PER_APP):
                generate_adunit(app, self.account)

    @nottest
    def mptest2_create_complex_default_admob_network(self):
        """
        Create default admob network campaign with multiple apps and adunits.

        Author: Tiago Bandeira
        """
        network_type = 'admob'

        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), NUM_APPS)

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type)

    @nottest
    def mptest_create_complex_custom_network(self):
        """
        Create custom network campaign with multiple apps and adunits.

        Author: Tiago Bandeira
        """
        network_type = 'custom'

        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), NUM_APPS)

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

    @nottest
    def mptest_create_complex_custom_admob_network(self):
        """
        Create custom network campaign with multiple apps and adunits.

        Author: Tiago Bandeira
        """
        network_type = 'admob'

        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()
        self.assertEqual(len(apps), NUM_APPS)

        # Create default admob campaign
        default_campaign = CampaignQueryManager.get_default_network_campaign(
                self.account, network_type)
        default_campaign.put()

        response = setup_and_make_request(self, network_type, apps)

        check_response(self, response, network_type,
                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                other_campaigns=[default_campaign])

## Helpers
#
def setup_and_make_request(test_case, network_type, apps, default_bid=
        DEFAULT_BID):
    """
    Setup and make the request to create a network campaign

    Author: Tiago Bandeira
    """
    # Set constants
    test_case.account.status = 'step4'
    AccountQueryManager.put(test_case.account)
    campaign_name = NETWORKS[network_type]
    url = reverse('edit_network', kwargs={'network': network_type})

    campaign_form = NetworkCampaignForm({'name': campaign_name})
    default_adgroup_form = NetworkAdGroupForm()

    data = {'bid': default_bid}
    if network_type == 'custom':
        data['custom_html'] = DEFAULT_HTML
    if network_type == 'custom_native':
        data['custom_method'] = DEFAULT_HTML
    pub_id_data = {}
    # Create the adgroup forms, one per adunit
    adgroup_forms = []
    for index, app in enumerate(apps):
        pub_id_data['app_%s-%s_pub_id' % (app.key(), network_type)] = DEFAULT_PUB_ID + str(index)
        for adunit in app.adunits:
            pub_id_data['adunit_%s-%s_pub_id' % (adunit.key(), network_type)] = \
                    DEFAULT_PUB_ID
            adgroup_form = AdUnitAdGroupForm(data,
                    prefix=str(adunit.key()))
            adgroup_forms.append(adgroup_form)

    # Create the data dict, each adgroup form per adunit must have a prefix,
    # so we can post multiple adgroup forms, which is the adunit key
    adunit_data = [('%s-%s' % (adgroup_form.prefix, key), item) for \
            adgroup_form in adgroup_forms for key, item in \
            adgroup_form.data.items()]
    data = campaign_form.data.items() + default_adgroup_form. \
            data.items() + adunit_data + pub_id_data.items()
    data = dict(data)

    # Header HTTP_X_REQUESTED_WITH is set to XMLHttpRequest to mimic an
    # ajax request
    response = test_case.client.post(url, data, HTTP_X_REQUESTED_WITH=
            'XMLHttpRequest')

    print data

    # Print the response
    print 'RESPONSE'
    print response
    print response.__dict__

    return response

def check_response(test_case, response, network_type,
        default_bid=DEFAULT_BID, network_state=NetworkStates.
        DEFAULT_NETWORK_CAMPAIGN, other_campaigns=[]):
    """
    Validate the response

    Author: Tiago Bandeira
    """
    test_case.assertEqual(response.status_code, 200)

    apps = PublisherQueryManager.get_objects_dict_for_account(
            account=test_case.account).values()

    # New campaign in memcache?
    network_campaigns = CampaignQueryManager.get_network_campaigns(
            test_case.account, is_new=True)
    test_case.assertEqual(len(network_campaigns) - len(other_campaigns), 1)

    # Is the campaign set up properly?
    campaign = [campaign for campaign in network_campaigns if campaign.key() \
            not in [other_campaign.key() for other_campaign in \
                    other_campaigns]][0]
    test_case.assertEqual(campaign._account, test_case.account.key())
    test_case.assertEqual(campaign.campaign_type, 'network')
    test_case.assertEqual(campaign.network_type, network_type)
    test_case.assertEqual(campaign.network_state, network_state)

    if campaign.network_state == NetworkStates.DEFAULT_NETWORK_CAMPAIGN:
        # Is the key_name set for the default network campaign?
        test_case.assertTrue(campaign.key().name())
        # Is the key name in the form ntwk:<account_key>:<network_type>?
        test_case.assertEqual(campaign.key().name(), 'ntwk:%s:%s' %
                (test_case.account.key(), network_type))

    # Was one adgroup per app created and are the created adgroups set up
    # properly?
    for index, app in enumerate(apps):
        if network_type in NETWORKS_WITH_PUB_IDS:
            test_case.assertTrue(app.network_config)
            test_case.assertEqual(getattr(app.network_config, '%s_pub_id' %
                network_type), DEFAULT_PUB_ID + str(index))

            if campaign.network_type in REPORTING_NETWORKS and \
                    campaign.network_state == NetworkStates. \
                    DEFAULT_NETWORK_CAMPAIGN:
                mapper = AdNetworkAppMapper.all().filter('application =', app).filter('ad_network_name =', network_type).get()
                #print 'MAPPER MAPPER'
                #print mapper
                test_case.assertTrue(mapper)
                test_case.assertEqual(mapper.publisher_id, DEFAULT_PUB_ID + str(index))

        for adunit in app.adunits:
            if network_type in NETWORKS_WITH_PUB_IDS:
                test_case.assertTrue(hasattr(adunit, 'network_config'))
                test_case.assertEqual(getattr(adunit.network_config, '%s_pub_id' %
                    network_type), DEFAULT_PUB_ID)

            adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                    adunit.key(), test_case.account.key(), get_from_db=True)
            test_case.assertTrue(adgroup)
            test_case.assertEqual(adgroup.network_type,
                    NETWORK_ADGROUP_TRANSLATION.get(network_type, network_type))
            test_case.assertEqual(adgroup.bid, default_bid)

            creatives = list(adgroup.creatives)
            test_case.assertEqual(len(creatives), 1)
            creative = creatives[0]
            test_case.assertEqual(creative._account, test_case.account.key())
            test_case.assertEqual(creative.__class__,
                    adgroup.default_creative().__class__)

            if campaign.network_type in ('custom', 'custom_native'):
                test_case.assertEqual(creative.html_data, DEFAULT_HTML)

    test_case.assertEqual(AccountQueryManager.get(test_case.account.key()). \
            status, '')

