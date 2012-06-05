import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

import simplejson as json
from datetime import date
from nose.tools import ok_, \
       eq_

from google.appengine.ext import db
from django.core.urlresolvers import reverse
from collections import defaultdict

from functools import wraps

from admin.randomgen import generate_app, generate_adunit

from common.utils.test.test_utils import dict_eq, \
        decorate_all_test_methods, \
        confirm_db, \
        confirm_all_models, \
        model_eq
from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION, \
        REPORTING_NETWORKS

from networks.mptests.network_test_case import NetworkTestCase, \
        DEFAULT_BID, \
        DEFAULT_HTML, \
        DEFAULT_PUB_ID

from networks.views import NETWORKS_WITH_PUB_IDS

from account.query_managers import AccountQueryManager
from advertiser.query_managers import AdvertiserQueryManager, \
        CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager

from account.models import NetworkConfig
from advertiser.models import Campaign, \
        AdGroup, \
        Creative, \
        NetworkStates
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        LoginStates

from ad_network_reports.forms import LoginCredentialsForm
from networks.forms import NetworkCampaignForm, \
        NetworkAdGroupForm, \
        AdUnitAdGroupForm


def skip_if_no_mappers(test_method):
    @wraps(test_method)
    def wrapper(self):
        if self.network_type in REPORTING_NETWORKS and \
                self.network_type in NETWORKS_WITH_PUB_IDS:
            return test_method(self)
    return wrapper


#@decorate_all_test_methods(confirm_db())
class CreateNetworkGetTestCase(NetworkTestCase):
    def setUp(self):
        super(CreateNetworkGetTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.url = reverse('edit_network',
                kwargs={'network': self.network_type})

    def network_type_to_test(self):
        return 'admob'

    @confirm_db()
    def mptest_response_code(self):
        """Visiting the create network page should return a 200, and not modify any state.

        Author: Tiago Bandeira
        """
        confirm_all_models(self.client.get, args=[self.url])

    @confirm_db()
    def mptest_context(self):
        """The context given to the create network template should be valid.

        Author: Tiago Bandeira
        """
        response = self.client.get(self.url)
        context = response.context

        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
                self.account).values()
        adgroups_by_adunit = {}
        for adgroup in adgroups:
            adgroups_by_adunit[adgroup.site_keys[0]] = adgroup

        network_data = {'name': self.network_type,
                        'pretty_name': NETWORKS[self.network_type],
                        'show_login': False,
                        'login_state': LoginStates.NOT_SETUP}

        dict_eq(network_data, context['network'])

        eq_(str(self.account.key()), context['account_key'])

        ok_(not context['custom_campaign'] or (context['custom_campaign'] and
            self.network_type in ('custom', 'custom_native')))

        ok_(isinstance(context['campaign_form'], NetworkCampaignForm))

        eq_('', context['campaign_key'])

        ok_(isinstance(context['login_form'], LoginCredentialsForm))

        ok_(isinstance(context['adgroup_form'], NetworkAdGroupForm))

        eq_(len(self.existing_apps), len(context['apps']))
        for app_idx, app in enumerate(context['apps']):
            pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
            eq_(app.pub_id, pub_id)

            for adunit_idx, adunit in enumerate(app.adunits):
                ok_(isinstance(adunit.adgroup_form, AdUnitAdGroupForm))
                ok_(adunit.key() in adgroups_by_adunit)
                model_eq(adunit.adgroup_form.instance,
                        adgroups_by_adunit[adunit.key()])

                eq_(adunit.pub_id, '%s_%s' % (pub_id, adunit_idx))

        ok_(not context['reporting'])


class CreateNetworkPostTestCase(NetworkTestCase):
    def setUp(self):
        super(CreateNetworkPostTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.app_pub_ids = {}
        self.adunit_pub_ids = {}

        for app_idx, app in enumerate(self.existing_apps):
            pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
            self.app_pub_ids[app.key()] = pub_id

            for adunit_idx, adunit in enumerate(app.adunits):
                self.adunit_pub_ids[adunit.key()] = '%s_%s' % (pub_id,
                        adunit_idx)

        self.url = reverse('edit_network',
                kwargs={'network': self.network_type})
        self.post_data = self.setup_post_request_data(apps=self.existing_apps,
                network_type=self.network_type, app_pub_ids=self.app_pub_ids,
                adunit_pub_ids=self.adunit_pub_ids)

    def network_type_to_test(self):
        return 'admob'

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_response_code(self):
        """When adding a network campaign, response code should be 200.

        Author: Andrew He
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_puts_campaign(self):
        """A new network campaign should be initialized and saved properly.

        Author: Andrew He
        """
        existing_campaigns = self.get_network_campaigns()
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        newly_added_campaigns = self.get_campaigns(
                exclude=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)

        new_campaign = newly_added_campaigns[0]

        if self.network_type in ('custom', 'custom_native'):
            expected_network_state = NetworkStates.CUSTOM_NETWORK_CAMPAIGN
        else:
            expected_network_state = NetworkStates.DEFAULT_NETWORK_CAMPAIGN

        self.check_campaign_init(new_campaign, self.network_type,
                expected_network_state)

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_puts_custom_campaign_if_default_exists(self):
        """When a default campaign already exists for the given network type,
        a custom campaign should be added to the datastore.

        Author: Andrew He
        """
        if self.network_type in ('custom', 'custom_native'):
            return

        self.generate_network_campaign(self.network_type, self.account,
                self.existing_apps)

        existing_campaigns = self.get_network_campaigns()
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        newly_added_campaigns = self.get_campaigns(
                exclude=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)

        new_campaign = newly_added_campaigns[0]
        self.check_campaign_init(new_campaign, self.network_type,
                NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_puts_one_adgroup_for_each_adunit(self):
        """There should be one new adgroup w/ a valid creative for each adunit.

        Author: Andrew He
        """
        existing_campaigns = self.get_network_campaigns()
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        newly_added_campaigns = self.get_campaigns(
                exclude=existing_campaigns)
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

                if self.network_type in ('custom', 'custom_native'):
                    eq_(creative.html_data, DEFAULT_HTML)

    def mptest_activates_adgroups_properly_on_creation(self):
        """Setting adgroup.active should work.

        Author: Andrew He
        """
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Mark one of the adunits as 'enabled'.
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_active_key] = True

        expected_edits = {app.network_config.key(): {'admob_pub_id': self.app_pub_ids[app.key()]},
                adunit.network_config.key(): {'admob_pub_id': self.adunit_pub_ids[adunit.key()]}}

        response = confirm_all_models(self.client.post,
                                      args=[self.url, self.post_data],
                                      kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                                      added={Campaign: 1, AdGroup: 1, Creative: 1},
                                      edited=expected_edits)

        campaign = self.get_campaigns()[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                adunit.key(), self.account.key(), get_from_db=True)

        eq_(adgroup.active, True)

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_only_allow_activating_adgroups_with_pub_ids(self):
        """Setting adgroup.active should not work if its pub ID isn't set.

        Author: Andrew He
        """
        if self.network_type not in NETWORKS_WITH_PUB_IDS:
            return

        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Mark one of the adunits as 'enabled' without giving it a pub ID.
        adunit_pub_id_key = 'adunit_%s-%s_pub_id' % (adunit.key(),
                self.network_type)
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_pub_id_key] = ''
        self.post_data[adunit_active_key] = True

        response = self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        eq_(response_json['success'], False)
        ok_(adunit_pub_id_key in response_json['errors'])

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_updates_network_configs(self):
        """All network config objects should be updated with correct pub IDs.

        Author: Andrew He
        """
        if self.network_type not in NETWORKS_WITH_PUB_IDS:
            return

        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        if self.network_type == 'jumptap':
            self.account = AccountQueryManager.get(self.account.key())
            eq_(self.account.network_config.jumptap_pub_id, DEFAULT_PUB_ID)

        actual_apps = self.get_apps_with_adunits(self.account)
        for app in actual_apps:
            expected_app_pub_id = self.app_pub_ids[app.key()]
            eq_(getattr(app.network_config, '%s_pub_id' %
                    self.network_type), expected_app_pub_id)

            for adunit in app.adunits:
                expected_adunit_pub_id = self.adunit_pub_ids[adunit.key()]
                ok_(hasattr(adunit, 'network_config'))
                eq_(getattr(adunit.network_config, '%s_pub_id' %
                            self.network_type), expected_adunit_pub_id)

    @skip_if_no_mappers
    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_creates_new_mapper_only_if_login_saved(self):
        """If the user has no logins, mappers should not be created.

        Author: Andrew He
        """
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_mappers = AdNetworkAppMapper.all().fetch(1000)
        eq_(len(actual_mappers), 0)

    @skip_if_no_mappers
    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper, AdNetworkLoginCredentials])
    def mptest_creates_new_mapper_if_no_existing_mappers(self):
        """If a mapper does not exist, a new one should be created.

        Author: Andrew He
        """
        ad_network_login = self.generate_ad_network_login(self.network_type,
                self.account)
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application in', self.existing_apps). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), len(self.existing_apps))

        mappers_for_app_key = defaultdict(list)
        for mapper in actual_mappers:
            mappers_for_app_key[mapper.application.key()].append(mapper)

        for app in self.existing_apps:
            # Each app should have mappers.
            ok_(app.key() in mappers_for_app_key)

            mappers = mappers_for_app_key[app.key()]
            for mapper in mappers:
                # Each mapper should be initialized properly.
                expected_pub_id = self.app_pub_ids[app.key()]
                eq_(mapper.publisher_id, expected_pub_id)
                eq_(mapper.ad_network_name, self.network_type)
                eq_(mapper.ad_network_login.key(), ad_network_login.key())

    @skip_if_no_mappers
    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper, AdNetworkLoginCredentials])
    def mptest_deletes_existing_mapper_if_no_stats(self):
        """Stats-less mappers should be replaced with new mappers.

        Author: Andrew He
        """
        existing_mapper = self.generate_ad_network_app_mapper(self.network_type,
                self.existing_apps[0], DEFAULT_PUB_ID, with_stats=False)

        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application =', self.existing_apps[0]). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), 1)

        ok_(existing_mapper.key() != actual_mappers[0].key())

    @skip_if_no_mappers
    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper, AdNetworkLoginCredentials])
    def mptest_creates_new_mapper_if_existing_mapper_has_stats(self):
        """If a mapper already exists for this app / network type pair and it
        has stats, a new mapper should be created without deleting the old one.

        Author: Andrew He
        """
        existing_mapper = self.generate_ad_network_app_mapper(self.network_type,
                self.existing_apps[0], DEFAULT_PUB_ID, with_stats=True)

        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_mappers = AdNetworkAppMapper.all(). \
                filter('application =', self.existing_apps[0]). \
                filter('ad_network_name =', self.network_type).fetch(1000)
        eq_(len(actual_mappers), 2)

        # Check that old mapper wasn't modified.
        old_mapper = AdNetworkAppMapper.get_by_publisher_id(DEFAULT_PUB_ID,
                self.network_type)
        eq_(old_mapper.key(), existing_mapper.key())

    @confirm_db(modified=[Campaign, AdGroup, Creative, NetworkConfig,
        AdNetworkAppMapper])
    def mptest_updates_onboarding(self):
        """An account should be finished onboarding once a campaign is created.

        Author: Andrew He
        """
        self.account.status = 'step4'
        AccountQueryManager.put(self.account)

        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        account_after = AccountQueryManager.get(self.account.key())
        eq_(account_after.status, '')

    # Helper methods.

    def get_network_campaigns(self):
        """Retrieves all network campaigns corresponding to self.account.

        Author: Andrew He
        """
        return CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True)

    def generate_ad_network_app_mapper(self, ad_network_name, app, publisher_id,
            with_stats=False):
        """Creates and saves an AdNetworkAppMapper using the given parameters.

        Author: Andrew He
        """
        # Obtain a valid login or create a new one.
        login = AdNetworkLoginCredentials.get_by_ad_network_name(
                self.account, ad_network_name)
        if not login:
            login = self.generate_ad_network_login(ad_network_name,
                    self.account)

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
            # Default network campaigns should have a key name.
            eq_(campaign.key().name(), 'ntwk:%s:%s' %
                (self.account.key(), network_type))
        else:
            # Custom network campaigns don't have a key name.
            ok_(campaign.key().name() is None)

    def get_campaigns(self, exclude=[]):
        """Retrieves all network campaigns besides those in existing_campaigns.

        Author: Andrew He
        """
        excluded_campaigns_keys = [c.key() for c in exclude]

        all_campaigns = self.get_network_campaigns()
        filtered_campaigns = filter(
                lambda c: c.key() not in excluded_campaigns_keys,
                all_campaigns)

        return filtered_campaigns


# class CreateJumptapNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'jumptap'

# class CreateIAdNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'iad'


# class CreateInmobiNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'inmobi'


# class CreateMobfoxNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'mobfox'


# class CreateMillennialNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'millennial'


# class CreateAdsenseNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'adsense'


# class CreateEjamNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'ejam'


# class CreateBrightrollNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'brightroll'


# class CreateCustomNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'custom'


# class CreateCustomNativeNetworkTestCase(CreateNetworkPostTestCase):
#     def network_type_to_test(self):
#         return 'custom_native'


# NUM_APPS = 3
# NUM_ADUNITS = 3
# class ComplexEditNetworkTestCase(CreateNetworkPostTestCase):
#     def set_up_existing_apps_and_adunits(self):
#         """Overrides method in superclass."""
#         for app_index in range(NUM_APPS):
#             app = generate_app(self.account)
#             for adunit_index in range(NUM_ADUNITS):
#                 generate_adunit(app, self.account)
