import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import eq_, nottest, ok_

from datetime import date
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
        AdNetworkAppMapper, AdNetworkScrapeStats

from account.query_managers import AccountQueryManager

DEFAULT_BID = 0.05
DEFAULT_HTML = 'html_data1'
DEFAULT_PUB_ID = 'pub_id'

class CreateNetworkTestCase(BaseViewTestCase):
    def setUp(self):
        super(CreateNetworkTestCase, self).setUp()
        
        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits()

    def tearDown(self):
        self.testbed.deactivate()

    def network_type_to_test(self):
        return 'admob'

    def set_up_existing_apps_and_adunits(self):
        """Creates one app with one adunit for use as a test fixture.

        This method may be overridden in a test case subclass to modify the
        test fixture.

        Author: Andrew He
        """
        app = generate_app(self.account)
        generate_adunit(app, self.account)

    def mptest_response_code(self):
        """When adding a network campaign, response code should be 200.

        Author: Andrew He
        """
        response = self.setup_and_make_request(self.network_type)
        eq_(response.status_code, 200)

    def mptest_puts_campaign(self):
        """A new network campaign should be initialized and saved properly.

        Author: Andrew He
        """
        existing_campaigns = self.get_network_campaigns()
        self.setup_and_make_request(self.network_type)

        newly_added_campaigns = self.get_newly_added_campaigns(
                existing_campaigns=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)

        new_campaign = newly_added_campaigns[0]

        if self.network_type in NETWORKS_WITH_PUB_IDS:
            expected_network_state = NetworkStates.DEFAULT_NETWORK_CAMPAIGN
        else:
            expected_network_state = NetworkStates.CUSTOM_NETWORK_CAMPAIGN

        self.check_campaign_init(new_campaign, self.network_type,
                expected_network_state)

    def mptest_puts_custom_campaign_if_default_exists(self):
        """When a default campaign already exists for the given network type,
        a custom campaign should be added to the datastore.

        Author: Andrew He
        """
        default_campaign = self.generate_default_network_campaign(
                self.network_type)

        existing_campaigns = self.get_network_campaigns()
        self.setup_and_make_request(self.network_type)

        newly_added_campaigns = self.get_newly_added_campaigns(
                existing_campaigns=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)

        new_campaign = newly_added_campaigns[0]
        expected_network_state = NetworkStates.CUSTOM_NETWORK_CAMPAIGN
        self.check_campaign_init(new_campaign, self.network_type,
                expected_network_state)

    def mptest_puts_one_adgroup_for_each_adunit(self):
        """There should be one new adgroup w/ a valid creative for each adunit.

        Author: Andrew He
        """
        existing_campaigns = self.get_network_campaigns()
        self.setup_and_make_request(self.network_type)

        newly_added_campaigns = self.get_newly_added_campaigns(
                existing_campaigns=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)
        new_campaign = newly_added_campaigns[0]

        for app in self.existing_apps:
            for adunit in app.adunits:
                adgroup = AdGroupQueryManager.get_network_adgroup(new_campaign,
                            adunit.key(), self.account.key(), get_from_db=True)
                ok_(adgroup is not None)
                eq_(adgroup.network_type,
                        NETWORK_ADGROUP_TRANSLATION.get(self.network_type, 
                                                        self.network_type))
                eq_(adgroup.bid, DEFAULT_BID)

                creatives = list(adgroup.creatives)
                eq_(len(creatives), 1)
                creative = creatives[0]
                eq_(creative._account, self.account.key())
                eq_(creative.__class__, adgroup.default_creative().__class__)

    def mptest_updates_network_configs(self):
        """All network config objects should be updated with correct pub IDs.

        Author: Andrew He
        """
        if self.network_type not in NETWORKS_WITH_PUB_IDS:
            return

        self.setup_and_make_request(self.network_type)

        actual_apps = self.get_apps_with_adunits()
        for index, app in enumerate(actual_apps):
            ok_(app.network_config is not None)
            eq_(getattr(app.network_config, '%s_pub_id' %
                    self.network_type), DEFAULT_PUB_ID + str(index))

            for adunit in app.adunits:
                ok_(hasattr(adunit, 'network_config'))
                eq_(getattr(adunit.network_config, '%s_pub_id' %
                            self.network_type), DEFAULT_PUB_ID)

    def mptest_creates_new_mapper_only_if_login_saved(self):
        """If there are no logins, AdNetworkAppMappers should not be created.

        Author: Andrew He
        """
        if self.network_type not in REPORTING_NETWORKS:
            return

        self.setup_and_make_request(self.network_type)

        actual_mappers = AdNetworkAppMapper.all().fetch(1000)
        eq_(len(actual_mappers), 0)

    def mptest_creates_new_mapper_if_no_existing_mappers(self):
        """If a mapper does not exist, a new one should be created.
        
        Author: Andrew He
        """

        if self.network_type not in REPORTING_NETWORKS:
            return

        ad_network_login = self.generate_ad_network_login(self.network_type)
        self.setup_and_make_request(self.network_type)

        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application =', self.existing_apps[0]). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), 1)

        # TODO: verify mapper is initialized properly

    def mptest_deletes_existing_mapper_if_no_stats(self):
        """Stats-less mappers should be replaced with new mappers.

        Author: Andrew He
        """
        if self.network_type not in REPORTING_NETWORKS:
            return

        existing_mapper = self.generate_ad_network_app_mapper(self.network_type,
                self.existing_apps[0], DEFAULT_PUB_ID, with_stats=False)

        self.setup_and_make_request(self.network_type)
        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application =', self.existing_apps[0]). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), 1)

    def mptest_creates_new_mapper_if_existing_mapper_has_stats(self):
        """If a mapper already exists for this app / network type pair and it \
        has stats, a new mapper should be created without deleting the old one.

        Author: Andrew He
        """
        if self.network_type not in REPORTING_NETWORKS:
            return

        existing_mapper = self.generate_ad_network_app_mapper(self.network_type,
                self.existing_apps[0], DEFAULT_PUB_ID, with_stats=True)

        self.setup_and_make_request(self.network_type)
        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application =', self.existing_apps[0]). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), 2)

        # TODO: check that existing mapper looks the same as it did before

    def mptest_updates_onboarding(self):
        """An account should be finished onboarding once a campaign is created.

        Author: Andrew He
        """
        self.account.status = 'step4'
        AccountQueryManager.put(self.account)

        self.setup_and_make_request(self.network_type)

        account_after = AccountQueryManager.get(self.account.key())
        eq_(account_after.status, '')
    
    # Helper methods.

    def get_apps_with_adunits(self):
        return PublisherQueryManager.get_objects_dict_for_account(
                account=self.account).values()

    def get_network_campaigns(self):
        return CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True)

    def generate_default_network_campaign(self, network_type):
        default = CampaignQueryManager.get_default_network_campaign(
                self.account, network_type)
        default.put()
        return default

    def generate_ad_network_login(self, network_type):
        """Creates and saves an AdNetworkLoginCredentials object.

        Author: Andrew He
        """
        login = AdNetworkLoginCredentials(account=self.account,
                                          ad_network_name=network_type)
        login.put()
        return login

    def generate_ad_network_app_mapper(self, ad_network_name, app, publisher_id,
            with_stats=False):
        """Creates and saves an AdNetworkAppMapper using the given parameters.

        Author: Andrew He
        """
        # Obtain a valid login or create a new one.
        login = AdNetworkLoginCredentials.get_by_ad_network_name(
                self.account, ad_network_name)
        if not login:
            login = self.generate_ad_network_login(ad_network_name)
        
        # Create the mapper and save it.
        mapper = AdNetworkAppMapper(ad_network_login=login,
                                    ad_network_name=ad_network_name,
                                    application=app,
                                    publisher_id=publisher_id)
        mapper.put()

        if with_stats:
            # If desired, create some default stats for this mapper.
            stats = AdNetworkScrapeStats(ad_network_app_mapper=mapper,
                                         date=date.today())
            stats.put()

        return mapper

    def setup_and_make_request(self, network_type):
        """
        Setup and make the request to create a network campaign

        Author: Tiago Bandeira
        """
        # Set constants
        campaign_name = NETWORKS[network_type]
        url = reverse('edit_network', kwargs={'network': network_type})

        campaign_form = NetworkCampaignForm({'name': campaign_name})
        default_adgroup_form = NetworkAdGroupForm()

        data = {'bid': DEFAULT_BID}
        if network_type == 'custom':
            data['custom_html'] = DEFAULT_HTML
        if network_type == 'custom_native':
            data['custom_method'] = DEFAULT_HTML
        pub_id_data = {}
        # Create the adgroup forms, one per adunit
        adgroup_forms = []
        for index, app in enumerate(self.existing_apps):
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
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH=
                'XMLHttpRequest')

        print data

        # Print the response
        print 'RESPONSE'
        print response
        print response.__dict__

        return response

    def check_campaign_init(self, campaign, network_type=None,
            network_state=None):
        """Checks that the new campaign has the right initial properties.

        Author: Andrew He
        """
        eq_(campaign._account, self.account.key())
        eq_(campaign.campaign_type, 'network')
        eq_(campaign.network_type, network_type)
        eq_(campaign.network_state, network_state)

        if network_state == NetworkStates.DEFAULT_NETWORK_CAMPAIGN:
            ok_(campaign.key().name() is not None)
            eq_(campaign.key().name(), 'ntwk:%s:%s' %
                (self.account.key(), network_type))
        else:
            ok_(campaign.key().name() is None)

    def get_newly_added_campaigns(self, existing_campaigns=[]):
        """Retrieves all network campaigns besides those in existing_campaigns.

        Author: Andrew He
        """
        existing_campaigns_keys = [c.key() for c in existing_campaigns]
        existing_campaigns_keys_set = set(existing_campaigns_keys)

        actual_campaigns_keys = [c.key() for c in self.get_network_campaigns()]
        actual_campaigns_keys_set = set(actual_campaigns_keys)

        newly_added_campaigns_key_set = actual_campaigns_keys_set - \
                existing_campaigns_keys_set

        return [Campaign.get(key) for key in newly_added_campaigns_key_set]


class CreateJumptapNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'jumptap'


class CreateIAdNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'iad'


class CreateInmobiNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'inmobi'


class CreateMobfoxNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'mobfox'


class CreateMillennialNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'millennial'


class CreateAdsenseNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'adsense'


class CreateEjamNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'ejam'


class CreateBrightrollNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'brightroll'


class CreateCustomNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'custom'


class CreateCustomNativeNetworkTestCase(CreateNetworkTestCase):
    def network_type_to_test(self):
        return 'custom_native'

NUM_APPS = 3
NUM_ADUNITS = 3
class ComplexEditNetworkTestCase(CreateNetworkTestCase):
    def set_up_existing_apps_and_adunits(self):
        """Overrides method in superclass."""
        for app_index in range(NUM_APPS):
            app = generate_app(self.account)
            for adunit_index in range(NUM_ADUNITS):
                generate_adunit(app, self.account)
