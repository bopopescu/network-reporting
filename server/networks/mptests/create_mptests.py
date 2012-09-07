import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

import simplejson as json
from datetime import date
from nose.plugins.skip import SkipTest
from nose.tools import ok_, \
       eq_

from google.appengine.ext import db
from django.core.urlresolvers import reverse
from collections import defaultdict

from functools import wraps

from admin.randomgen import generate_app, generate_adunit

from common.utils.test.fixtures import generate_adgroup, \
        generate_campaign, \
        generate_creative
from common.utils.test.test_utils import dict_eq, \
        confirm_db, \
        confirm_all_models, \
        model_eq
from common.constants import NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION, \
        REPORTING_NETWORKS

from networks.mptests.network_test_case import NetworkTestCase, \
        requires_network_with_reporting, \
        requires_network_with_pub_ids, \
        requires_network_without_pub_ids, \
        requires_non_custom_network_type, \
        DEFAULT_BID, \
        DEFAULT_HTML, \
        DEFAULT_PUB_ID

from networks.views import NETWORKS_WITH_PUB_IDS

from account.query_managers import AccountQueryManager
from advertiser.query_managers import AdvertiserQueryManager, \
        CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager
from ad_network_reports.query_managers import AdNetworkMapperManager
from publisher.query_managers import AdUnitQueryManager, \
        AppQueryManager

from account.models import NetworkConfig
from account.query_managers import NetworkConfigQueryManager
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



class CreateNetworkGetTestCase(NetworkTestCase):
    """Base test case class for network campaign creation GET request.

    This base class is actually used to test AdMob, but may be subclassed to
    test any other network type as long as network_type_to_test() is overridden.

    Almost all tests in this class use the confirm_all_models() function to
    ensure that datastore models are not modified unexpectedly.

    Author: Andrew He
    """
    def setUp(self):
        super(CreateNetworkGetTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.existing_adunits = []
        for app in self.existing_apps:
            self.existing_adunits += app.adunits

        self.url = reverse('edit_network',
                kwargs={'network': self.network_type})

    def network_type_to_test(self):
        return 'admob'

    def mptest_response_code(self):
        """
        Visiting the create network page should return a 200 and not modify
        any state.

        Author: Tiago Bandeira
        """
        confirm_all_models(self.client.get, args=[self.url])

    def mptest_context(self):
        """The context given to the create network template should be valid.

        Author: Tiago Bandeira
        """
        # set up network configs
        for app_idx, app in enumerate(self.existing_apps):
            pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
            setattr(app.network_config, '%s_pub_id' % self.network_type_to_test(), pub_id)
            AppQueryManager.update_config_and_put(app, app.network_config)

            for adunit_idx, adunit in enumerate(app.adunits):
                adunit_pub_id = '%s_%s' % (pub_id, adunit_idx)
                setattr(adunit.network_config, '%s_pub_id' % self.network_type_to_test(), adunit_pub_id)
                AdUnitQueryManager.update_config_and_put(adunit, adunit.network_config)

        # send the request
        response = self.client.get(self.url)
        context = response.context

        network_data = {'name': self.network_type,
                        'pretty_name': NETWORKS[self.network_type],
                        'show_login': True,
                        'login_state': LoginStates.NOT_SETUP}

        dict_eq(network_data, context['network'])

        eq_(self.account.key(), context['account'].key())

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
                ok_(adunit.adgroup_form)

                eq_(adunit.pub_id, '%s_%s' % (pub_id, adunit_idx))

        ok_(not context['reporting'])


class CreateNetworkPostTestCase(NetworkTestCase):
    """Base test case class for network campaign creation POST request.

    This base class is actually used to test AdMob, but may be subclassed to
    test any other network type as long as network_type_to_test() is overridden.

    Almost all tests in this class use the confirm_all_models() function to
    ensure that datastore models are not modified unexpectedly.

    Author: Andrew He
    """
    def setUp(self):
        super(CreateNetworkPostTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()

        # Keep references to the fixture apps and adunits.
        self.existing_apps = self.get_apps_with_adunits(self.account)
        self.existing_adunits = []
        for app in self.existing_apps:
            self.existing_adunits += app.adunits

        self.url = reverse('edit_network',
                kwargs={'network': self.network_type})
        self.post_data = self.setup_post_request_data(
                apps=self.existing_apps, network_type=self.network_type,
                app_pub_ids={}, adunit_pub_ids={})

    def network_type_to_test(self):
        return 'admob'

    def base_network_state(self):
        return NetworkStates.DEFAULT_NETWORK_CAMPAIGN

    # -------------------- >> begin tests << --------------------

    def mptest_response_code(self):
        """Submitting an un-modified new network form should return a 200.

        Author: Andrew He
        """
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    def mptest_puts_campaign(self):
        """A new network campaign should be initialized and saved properly.

        Author: Andrew He
        """
        # Prior to making any changes, get the existing network campaigns.
        existing_campaigns = self.get_network_campaigns()

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions)

        # Verify the properties of the campaign we just added.
        new_campaign = self.get_campaigns(exclude=existing_campaigns)[0]
        expected_network_state = self.base_network_state()
        self.check_campaign_init(new_campaign, self.network_type,
                                 expected_network_state)

    def mptest_puts_custom_campaign_if_campaign_already_exists(self):
        """
        When a campaign already exists for the given network type, a custom
        (rather than default) campaign should be added to the datastore.

        Author: Andrew He
        """
        # Generate a network campaign.
        existing_campaigns = [self.generate_network_campaign(
                self.network_type, self.account, self.existing_apps)]

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions)

        # Verify the properties of the campaign we just added.
        new_campaign = self.get_campaigns(exclude=existing_campaigns)[0]
        self.check_campaign_init(new_campaign, self.network_type,
                                 NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

    def mptest_puts_one_adgroup_for_each_adunit(self):
        """There should be one new adgroup-creative pair for each adunit.

        Author: Andrew He
        """
        # Prior to making any changes, get the existing network campaigns.
        existing_campaigns = self.get_network_campaigns()

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions)

        # Verify that each adunit got one adgroup-creative pair.
        new_campaign = self.get_campaigns(exclude=existing_campaigns)[0]
        for app in self.existing_apps:
            for adunit in app.adunits:
                # Verify the contents of the adgroup for this adunit.
                adgroup = AdGroupQueryManager.get_network_adgroup(
                        new_campaign, adunit.key(), self.account.key(),
                        get_from_db=True)

                expected_network_type = NETWORK_ADGROUP_TRANSLATION.get(
                        self.network_type, self.network_type)
                expected_adgroup = generate_adgroup(
                        self.account, new_campaign, active=False,
                        bid=DEFAULT_BID, name=NETWORKS[self.network_type],
                        network_type=expected_network_type,
                        site_keys=[adunit.key()], adgroup_type='network')

                model_eq(adgroup, expected_adgroup,
                         exclude=['created', 'last_login', 't'],
                         check_primary_key=False)

                # Verify the contents of the creative for this adgroup.
                creatives = list(adgroup.creatives)
                creative = creatives[0]

                expected_creative = adgroup.default_creative()
                expected_creative.account = self.account
                if self.network_type in ('custom', 'custom_native'):
                    expected_creative.html_data = DEFAULT_HTML

                model_eq(creative, expected_creative, check_primary_key=False)

    @requires_network_without_pub_ids
    def mptest_non_pub_id_adgroup_activation(self):
        """
        If a network doesn't use publisher IDs, it should always be possible
        to set the `active` property of any adgroup.

        This test only applies to networks WITHOUT publisher IDs.

        Author: Andrew He
        """
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Mark one of the adunits as 'enabled'.
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_active_key] = True

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions)

        # Verify the contents of the new adgroup.
        new_campaign = self.get_campaigns()[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(
                new_campaign, adunit.key(), self.account.key(),
                get_from_db=True)

        expected_network_type = NETWORK_ADGROUP_TRANSLATION.get(
                self.network_type, self.network_type)
        expected_adgroup = generate_adgroup(
                self.account, new_campaign, active=True,
                bid=DEFAULT_BID, name=NETWORKS[self.network_type],
                network_type=expected_network_type,
                site_keys=[adunit.key()], adgroup_type='network')

        model_eq(adgroup, expected_adgroup,
                 exclude=['created', 'last_login', 't'],
                 check_primary_key=False)

    @requires_network_with_pub_ids
    def mptest_good_adgroup_activation(self):
        """
        If an adunit has its pub ID set, it should be possible to set the
        adunit's corresponding adgroup to be active.

        This test only applies to networks with publisher IDs.

        Author: Andrew He
        """
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Mark one of the adunits as 'enabled'.
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_active_key] = True

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

        # Verify the contents of the new adgroup.
        new_campaign = self.get_campaigns()[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(new_campaign,
                adunit.key(), self.account.key(), get_from_db=True)

        expected_network_type = NETWORK_ADGROUP_TRANSLATION.get(
                self.network_type, self.network_type)
        expected_adgroup = generate_adgroup(self.account, new_campaign,
                active=True,
                bid=DEFAULT_BID,
                name=NETWORKS[self.network_type],
                network_type=expected_network_type,
                site_keys=[adunit.key()],
                adgroup_type='network')

        model_eq(adgroup, expected_adgroup,
                 exclude=['created', 'last_login', 't'],
                 check_primary_key=False)

    @requires_network_with_pub_ids
    def mptest_bad_adgroup_activation(self):
        """
        If an adunit doesn't have its pub ID set, it should not be possible to
        set the adunit's corresponding adgroup to be active.

        This test only applies to networks with publisher IDs.

        Author: Andrew He
        """
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Mark one of the adunits as 'enabled' without giving it a pub ID.
        adunit_pub_id_key = 'adunit_%s-%s_pub_id' % (adunit.key(),
                self.network_type)
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_pub_id_key] = ''
        self.post_data[adunit_active_key] = True

        response = confirm_all_models(
                self.client.post,
                args=[self.url, self.post_data],
                kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
        response_json = json.loads(response.content)

        # Verify that the POST failed.
        eq_(response_json['success'], False)

        # Verify that the offending adunit is identified in the list of errors.
        ok_(adunit_pub_id_key in response_json['errors'])

    @requires_network_with_pub_ids
    def mptest_updates_network_configs(self):
        """All network config objects should be updated with correct pub IDs.

        Author: Andrew He
        """
        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

    @requires_network_with_reporting
    @requires_network_with_pub_ids
    def mptest_creates_new_mapper_only_if_login_saved(self):
        """If the user has no logins, mappers should not be created.

        Author: Andrew He
        """
        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Expect the correct number of models to be added.
        # There should be no new mappers!
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

    @requires_network_with_reporting
    @requires_network_with_pub_ids
    def mptest_creates_new_mapper_if_no_existing_mappers(self):
        """If a mapper does not exist, a new one should be created.

        Author: Andrew He
        """
        ad_network_login = self.generate_ad_network_login(self.network_type,
                                                          self.account)

        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits),
                              AdNetworkAppMapper: len(self.existing_apps)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

        # Verify the contents of the new mapper(s) that were created.
        mappers = list(AdNetworkMapperManager.get_mappers(self.account,
                                                          self.network_type))
        mappers_by_app_key = defaultdict(list)
        for mapper in mappers:
            mappers_by_app_key[mapper.application.key()].append(mapper)

        for app in self.existing_apps:
            # Verify that each app has a mapper.
            ok_(app.key() in mappers_by_app_key)

            mappers = mappers_by_app_key[app.key()]
            for mapper in mappers:
                # TODO: use model_eq.
                # Verify that each mapper is initialized properly.
                expected_pub_id = app_pub_ids[app.key()]
                eq_(mapper.publisher_id, expected_pub_id)
                eq_(mapper.ad_network_name, self.network_type)
                eq_(mapper.ad_network_login.key(), ad_network_login.key())

    @requires_network_with_reporting
    @requires_network_with_pub_ids
    def mptest_deletes_existing_mapper_if_no_stats(self):
        """Stats-less mappers should be replaced with new mappers.

        Author: Andrew He
        """
        # Generate a mapper that doesn't have any stats.
        existing_mapper = self.generate_ad_network_app_mapper(self.network_type,
                self.existing_apps[0], DEFAULT_PUB_ID, with_stats=False)

        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits),
                              AdNetworkAppMapper: len(self.existing_apps)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(app_pub_ids=app_pub_ids,
                adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits,
                           deleted=[existing_mapper.key()])

    @requires_network_with_reporting
    @requires_network_with_pub_ids
    def mptest_creates_new_mapper_if_existing_mapper_has_stats(self):
        """If a mapper already exists for this app / network type pair and it
        has stats, a new mapper should be created without deleting the old one.

        Author: Andrew He
        """
        # Generate a mapper that has stats.
        existing_mapper = self.generate_ad_network_app_mapper(
                self.network_type, self.existing_apps[0], DEFAULT_PUB_ID,
                with_stats=True)

        # Modify the base POST body to give each app / adunit a publisher ID.
        app_pub_ids = self.generate_app_pub_ids()
        adunit_pub_ids = self.generate_adunit_pub_ids()
        self.update_post_data_pub_ids(app_pub_ids=app_pub_ids,
                                      adunit_pub_ids=adunit_pub_ids)

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits),
                              AdNetworkAppMapper: len(self.existing_apps)}

        # Expect the NetworkConfigs for app / adunit to be modified accordingly.
        expected_edits = self.get_expected_config_edits(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

    def mptest_updates_onboarding(self):
        """An account should be finished onboarding once a campaign is created.

        Author: Andrew He
        """
        self.account.status = 'step4'
        AccountQueryManager.put(self.account)

        # Expect the correct number of models to be added.
        expected_additions = {Campaign: 1,
                              AdGroup:  len(self.existing_adunits),
                              Creative: len(self.existing_adunits)}

        # Expect the account's status to change.
        expected_edits = {self.account.key(): {'status': ''}}

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added=expected_additions,
                           edited=expected_edits)

    # -------------------- >> end tests << --------------------

    # -------------------- >> begin helpers << ------------------

    def generate_app_pub_ids(self, prefix=DEFAULT_PUB_ID):
        app_pub_ids = {}
        for app_idx, app in enumerate(self.existing_apps):
            pub_id = '%s_%s' % (prefix, app_idx)
            app_pub_ids[app.key()] = pub_id
        return app_pub_ids

    def generate_adunit_pub_ids(self, prefix=DEFAULT_PUB_ID):
        adunit_pub_ids = {}
        for app_idx, app in enumerate(self.existing_apps):
            for adunit_idx, adunit in enumerate(app.adunits):
                adunit_pub_ids[adunit.key()] = \
                        '%s_%s_%s' % (prefix, app_idx, adunit_idx)
        return adunit_pub_ids

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

    def get_network_campaigns(self):
        """Retrieves all network campaigns corresponding to self.account.

        Author: Andrew He
        """
        return CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True)

    def check_campaign_init(self, campaign, network_type=None,
            network_state=None):
        """Checks that the given campaign has the right initial properties.

        Author: Andrew He
        """
        expected_campaign = generate_campaign(self.account,
                                              name=NETWORKS[self.network_type],
                                              campaign_type='network',
                                              network_type=network_type,
                                              network_state=network_state)

        model_eq(campaign, expected_campaign, exclude=['created'], check_primary_key=False)

        if network_state == NetworkStates.DEFAULT_NETWORK_CAMPAIGN:
            # Default network campaigns should have a key name.
            eq_(campaign.key().name(), 'ntwk:%s:%s' %
                (self.account.key(), network_type))
        else:
            # Custom network campaigns don't have a key name.
            ok_(campaign.key().name() is None)

    def get_campaigns(self, exclude=None):
        """Retrieves all network campaigns besides those in the `exclude` list.

        Author: Andrew He
        """
        if not exclude:
            exclude = []

        excluded_campaigns_keys = [c.key() for c in exclude]

        all_campaigns = self.get_network_campaigns()
        filtered_campaigns = filter(
                lambda c: c.key() not in excluded_campaigns_keys,
                all_campaigns)

        return filtered_campaigns

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        """
        Updates the given POST body dictionary with new app / adunit
        publisher IDs.

        Author: Andrew He
        """

        if not app_pub_ids:
            return

        if not adunit_pub_ids:
            return

        for app_key, pub_id in app_pub_ids.iteritems():
            app_post_key = 'app_%s-%s_pub_id' % (app_key, self.network_type)
            self.post_data[app_post_key] = pub_id

        for adunit_key, pub_id in adunit_pub_ids.iteritems():
            adunit_post_key = 'adunit_%s-%s_pub_id' % (adunit_key, self.network_type)
            self.post_data[adunit_post_key] = pub_id

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        """
        Given dictionaries mapping app / adunit keys to new publisher IDs,
        returns an 'edit' dictionary that may be passed as the `edited` keyword
        argument to confirm_all_models.

        Example:

        If app_pub_ids = {'app_key0': 'new_pub_id'} and self.network_type is
        'admob', this method returns

            {'app_key0': {'admob_pub_id': 'new_pub_id'}}

        Author: Andrew He
        """

        expected_edits = {}

        pub_id_prop_key = '%s_pub_id' % self.network_type

        for app in self.existing_apps:
            new_app_pub_id = app_pub_ids[app.key()]
            expected_edits[app.network_config.key()] = {
                pub_id_prop_key: new_app_pub_id}

        for adunit in self.existing_adunits:
            new_adunit_pub_id = adunit_pub_ids[adunit.key()]
            expected_edits[adunit.network_config.key()] = {
                pub_id_prop_key: new_adunit_pub_id}

        return expected_edits


class CreateAdMobS2SDetailsTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'admob_s2s'


class CreateJumptapNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'jumptap'

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        super(CreateJumptapNetworkTestCase, self).update_post_data_pub_ids(
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

        # Jumptap also supports an account-level publisher ID.
        self.post_data['jumptap_pub_id'] = DEFAULT_PUB_ID

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        edits = super(CreateJumptapNetworkTestCase, self). \
                get_expected_config_edits(app_pub_ids=app_pub_ids,
                                          adunit_pub_ids=adunit_pub_ids)

        # Include the account-level publisher ID in the expected edits dict.
        edits[self.account.network_config.key()] = {
                'jumptap_pub_id': DEFAULT_PUB_ID}
        return edits


class CreateIAdNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'iad'

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        # iAd doesn't use publisher IDs.
        pass

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        return {}


class CreateInmobiNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'inmobi'


class CreateMobfoxNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'mobfox'


class CreateMillennialNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'millennial'


class CreateMillennialS2SNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'millennial_s2s'


class CreateAdsenseNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'adsense'

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        # AdSense doesn't use publisher IDs.
        pass

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        return {}


class CreateEjamNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'ejam'


class CreateBrightrollNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'brightroll'


class CreateCustomNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'custom'

    def base_network_state(self):
        return NetworkStates.CUSTOM_NETWORK_CAMPAIGN

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        # Custom networks don't use publisher IDs.
        pass

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        return {}


class CreateCustomNativeNetworkTestCase(CreateNetworkPostTestCase):
    def network_type_to_test(self):
        return 'custom_native'

    def base_network_state(self):
        return NetworkStates.CUSTOM_NETWORK_CAMPAIGN

    def update_post_data_pub_ids(self, app_pub_ids=None, adunit_pub_ids=None):
        # Custom native networks don't use publisher IDs.
        pass

    def get_expected_config_edits(self, app_pub_ids=None, adunit_pub_ids=None):
        return {}


NUM_APPS = 3
NUM_ADUNITS = 3
class ComplexCreateNetworkPostTestCase(CreateNetworkPostTestCase):
    """Test case with a more complex fixture (multiple apps and adunits).

    Author: Andrew He
    """
    def set_up_existing_apps_and_adunits(self):
        """Overrides method in superclass."""
        for app_index in range(NUM_APPS):
            app = generate_app(self.account)
            AppQueryManager.update_config_and_put(
                    app, NetworkConfig(account=self.account))

            for adunit_index in range(NUM_ADUNITS):
                adunit = generate_adunit(app, self.account)
                AdUnitQueryManager.update_config_and_put(
                        adunit, NetworkConfig(account=self.account))
