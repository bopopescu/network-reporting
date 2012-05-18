import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup
import simplejson as json

from nose.tools import eq_, nottest, ok_

from collections import defaultdict
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

from functools import wraps

# Model imports
from account.models import Account, \
        NetworkConfig
from publisher.models import App, \
        AdUnit
from advertiser.models import Campaign, \
        AdGroup, \
        Creative
from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper, \
        AdNetworkScrapeStats

from account.query_managers import AccountQueryManager

DEFAULT_BID = 0.05
DEFAULT_HTML = 'html_data1'
DEFAULT_PUB_ID = 'pub_id'

def skip_if_no_mappers(test_method):
    @wraps(test_method)
    def wrapper(self):
        if self.network_type in REPORTING_NETWORKS and \
                self.network_type in NETWORKS_WITH_PUB_IDS:
            return test_method(self)
    return wrapper

class EditNetworkTestCase(BaseViewTestCase):
    def setUp(self):
        super(EditNetworkTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = get_apps_with_adunits(self.account)

        self.existing_campaign = generate_network_campaign(self.network_type,
            self.account, self.existing_apps)
        
        app_pub_ids = {}
        adunit_pub_ids = {}

        for app_idx, app in enumerate(self.existing_apps):
            pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
            app_pub_ids[app.key()] = pub_id

            for adunit_idx, adunit in enumerate(app.adunits):
                adunit_pub_ids[adunit.key()] = '%s_%s' % (pub_id, adunit_idx)

        self.url = reverse('edit_network',
                kwargs={'campaign_key': str(self.existing_campaign.key())})

        self.post_data = setup_post_request_data(apps=self.existing_apps,
                network_type=self.network_type, account_pub_id=None,
                app_pub_ids=app_pub_ids, adunit_pub_ids=adunit_pub_ids)

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
        """When editing a network campaign, response code should be 200.

        Author: Andrew He
        """
        response = self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

    def mptest_activates_adgroup(self):
        """Setting adgroup.active to True should work.

        Author: Andrew He
        """
        # Prepare a request that marks one of the adunits as 'enabled'.
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_active_key] = True

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that the adgroup for this adunit is marked active.
        adgroup = AdGroupQueryManager.get_network_adgroup(
                self.existing_campaign, adunit.key(), self.account.key(),
                get_from_db=True)
        eq_(adgroup.active, True)

    def mptest_only_allows_activating_adgroups_with_pub_ids(self):
        """Setting adgroup.active to True should not work if there's no pub ID.
        
        Author: Andrew He
        """
        # Prepare a request that marks one of the adunits as 'enabled' without
        # giving it a pub ID.
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        adunit_pub_id_key = 'adunit_%s-%s_pub_id' % (adunit.key(), 
                self.network_type)
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_pub_id_key] = ''
        self.post_data[adunit_active_key] = True

        # Send the request.
        response = self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        # Check that the request fails and returns a validation error for the
        # specific adunit.
        eq_(response_json['success'], False)
        ok_(adunit_pub_id_key in response_json['errors'])

    def mptest_deactivates_adgroup(self):
        """Setting adgroup.active to False should work.

        Author: Andrew He
        """
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        # Manually edit one of the existing adgroups to be active.
        campaign = self.existing_campaign
        adgroup = AdGroupQueryManager.get_network_adgroup(
                self.existing_campaign, adunit.key(), self.account.key(),
                get_from_db=True)
        adgroup.active = True
        adgroup.put()

        # Prepare a request that marks this adunit as 'disabled'.
        adunit_active_key = '%s-active' % adunit.key()
        self.post_data[adunit_active_key] = False

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that the adgroup for this adunit is marked active.
        adgroup = AdGroupQueryManager.get_network_adgroup(
                self.existing_campaign, adunit.key(), self.account.key(),
                get_from_db=True)
        eq_(adgroup.active, False)

    def mptest_updates_network_configs(self):
        """All network config objects should be updated with correct pub IDs.
        
        Author: Andrew He
        """
        if self.network_type not in NETWORKS_WITH_PUB_IDS:
            return

        # Prepare a request that changes the pub IDs for one app and one adunit.
        app_to_modify = self.existing_apps[0]
        adunit_to_modify = app_to_modify.adunits[0]

        new_app_pub_id = 'TEST_APP_PUB_ID'
        app_pub_id_key = 'app_%s-%s_pub_id' % (app_to_modify.key(),
                self.network_type)
        self.post_data[app_pub_id_key] = new_app_pub_id

        new_adunit_pub_id = 'TEST_ADUNIT_PUB_ID'
        adunit_pub_id_key = 'adunit_%s-%s_pub_id' % (adunit_to_modify.key(), 
                self.network_type)
        self.post_data[adunit_pub_id_key] = new_adunit_pub_id

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that the specified network configs were modified as expected,
        # and that all other network configs were unchanged.
        for app in get_apps_with_adunits(self.account):
            if app.key() == app_to_modify.key():
                expected_app_pub_id = new_app_pub_id
            else:
                expected_app_pub_id = self.app_pub_ids[app.key()]
            
            eq_(getattr(app.network_config, '%s_pub_id' %
                    self.network_type), expected_app_pub_id)

            for adunit in app.adunits:
                if adunit.key() == adunit_to_modify.key():
                    expected_adunit_pub_id = new_adunit_pub_id
                else:
                    expected_adunit_pub_id = self.adunit_pub_ids[adunit.key()]

                eq_(getattr(adunit.network_config, '%s_pub_id' %
                            self.network_type), expected_adunit_pub_id)

    def mptest_updates_mapper_when_updating_pub_id(self):
        """If an app is given a new pub ID, a new mapper should be created.

        Author: Andrew He
        """
        # Prepare a request that changes the pub ID for one app.
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        new_app_pub_id = 'TEST_APP_PUB_ID'
        app_pub_id_key = 'app_%s-%s_pub_id' % (app.key(),
                self.network_type)
        self.post_data[app_pub_id_key] = new_app_pub_id

        # TODO: Prepare a login?

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        
        # Fetch all mappers for our app and this network type.
        mappers = AdNetworkAppMapper.all(). \
            filter('application in', self.existing_apps). \
            filter('ad_network_name =', self.network_type).fetch(1000)

        # There should only be one mapper: the one for the app we just updated.
        eq_(len(mappers), 1)

        mapper = mappers[0]
        eq_(mapper.publisher_id, new_app_pub_id)
        eq_(mapper.ad_network_name, self.network_type)
        #eq_(mapper.ad_network_login.key(), ad_network_login.key())

    def mptest_updates_cpms(self):
        """Updating CPM (bid) should work.

        Author: Andrew He
        """
        # Prepare a request that changes the CPM for one adunit.
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        new_bid = 100.0
        adunit_bid_key = '%s-bid' % adunit.key()
        self.post_data[adunit_bid_key] = new_bid

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that the adgroup for this adunit has the new bid.
        adgroup = AdGroupQueryManager.get_network_adgroup(
                self.existing_campaign, adunit.key(), self.account.key(),
                get_from_db=True)
        eq_(adgroup.bid, new_bid)
    
    def mptest_updates_advanced_targeting(self):
        """Updating advanced targeting for a campaign should work.

        Author: Andrew He
        """
        # Prepare a request that changes a few advanced targeting settings.
        self.post_data['device_targeting'] = '1'
        self.post_data['ios_version_max'] = '4.0'
        self.post_data['geo_predicates'] = 'UG'

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that all adgroups for this campaign have the new settings.
        adgroups = AdGroup.all().fetch(1000)
        for adgroup in adgroups:
            eq_(adgroup.device_targeting, True)
            eq_(adgroup.ios_version_max, '4.0')
            eq_(adgroup.geo_predicates, [u'country_name=UG'])

    def mptest_updates_allocation_and_fcaps(self):
        """Updating allocation and frequency capping on an adgroup should work.

        Author: Andrew He
        """
        # Prepare a request that changes the allocation / frequency capping
        # options for one adunit.
        app = self.existing_apps[0]
        adunit = app.adunits[0]

        new_allocation_percentage = 50.0
        allocation_percentage_key = '%s-allocation_percentage' % adunit.key()
        self.post_data[allocation_percentage_key] = new_allocation_percentage

        new_daily_frequency_cap = 24
        daily_frequency_cap_key = '%s-daily_frequency_cap' % adunit.key()
        self.post_data[daily_frequency_cap_key] = new_daily_frequency_cap

        new_hourly_frequency_cap = 5
        hourly_frequency_cap_key = '%s-hourly_frequency_cap' % adunit.key()
        self.post_data[hourly_frequency_cap_key] = new_hourly_frequency_cap

        # Send the request.
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check that the adgroup for this adunit has the new options.
        adgroup = AdGroupQueryManager.get_network_adgroup(
                self.existing_campaign, adunit.key(), self.account.key(),
                get_from_db=True)
        eq_(adgroup.allocation_percentage, new_allocation_percentage)
        eq_(adgroup.daily_frequency_cap, new_daily_frequency_cap)
        eq_(adgroup.hourly_frequency_cap, new_hourly_frequency_cap)


class CreateNetworkTestCase(BaseViewTestCase):
    def setUp(self):
        super(CreateNetworkTestCase, self).setUp()
        
        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = get_apps_with_adunits(self.account)

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
        self.post_data = setup_post_request_data(apps=self.existing_apps,
                network_type=self.network_type, account_pub_id=None,
                app_pub_ids=self.app_pub_ids,
                adunit_pub_ids=self.adunit_pub_ids)

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
        response = self.client.post(self.url, self.post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

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

    def mptest_puts_custom_campaign_if_default_exists(self):
        """When a default campaign already exists for the given network type,
        a custom campaign should be added to the datastore.

        Author: Andrew He
        """
        if self.network_type in ('custom', 'custom_native'):
            return

        default_campaign = self.generate_network_campaign(self.network_type)

        existing_campaigns = self.get_network_campaigns()
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        newly_added_campaigns = self.get_campaigns(
                exclude=existing_campaigns)
        eq_(len(newly_added_campaigns), 1)

        new_campaign = newly_added_campaigns[0]
        self.check_campaign_init(new_campaign, self.network_type,
                NetworkStates.CUSTOM_NETWORK_CAMPAIGN)

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

        response = self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        campaign = self.get_campaigns()[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                adunit.key(), self.account.key(), get_from_db=True)

        eq_(adgroup.active, True)

    def mptest_only_allow_activating_adgroups_with_pub_ids(self):
        """Setting adgroup.active should not work if its pub ID isn't set.

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

        print self.post_data
        response = self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        eq_(response_json['success'], False)
        ok_(adunit_pub_id_key in response_json['errors'])

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

        actual_apps = get_apps_with_adunits(self.account)
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
    def mptest_creates_new_mapper_only_if_login_saved(self):
        """If the user has no logins, mappers should not be created.

        Author: Andrew He
        """
        self.client.post(self.url, self.post_data,
                HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        actual_mappers = AdNetworkAppMapper.all().fetch(1000)
        eq_(len(actual_mappers), 0)

    @skip_if_no_mappers
    def mptest_creates_new_mapper_if_no_existing_mappers(self):
        """If a mapper does not exist, a new one should be created.
        
        Author: Andrew He
        """
        ad_network_login = self.generate_ad_network_login(self.network_type)
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

    def generate_network_campaign(self, network_type):
        """Creates and saves a network campaign of the given type.

        Author: Andrew He
        """
        if network_type in ('custom', 'custom_native'):
            campaign = Campaign(name=NETWORKS[network_type])
            campaign.campaign_type = 'network'
            campaign.network_type = network_type
        else:  
            campaign = CampaignQueryManager.get_default_network_campaign(
                self.account, network_type)

        campaign.put()
        return campaign

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
    

# Helper functions.

def get_apps_with_adunits(account):
        apps = PublisherQueryManager.get_objects_dict_for_account(
                account=account).values()
        return sorted(apps, key=lambda a: a.name)

def generate_network_campaign(network_type, account, apps):
    """Creates a network campaign along with any necessary adgroups/creatives.

    Author: Andrew He
    """
    # Generate the campaign object.
    if network_type in ('custom', 'custom_native'):
        campaign = Campaign(name=NETWORKS[network_type])
        campaign.campaign_type = 'network'
        campaign.network_type = network_type
    else:  
        campaign = CampaignQueryManager.get_default_network_campaign(
            account, network_type)

    campaign.put()

    # Generate one adgroup per adunit.
    for app in apps:
        for adunit in app.adunits:
            adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                    adunit.key(), account.key())
            adgroup.put()

            # Generate the creative for this adgroup.
            if network_type in ('custom', 'custom_native'):
                creative = adgroup.default_creative(html_data=DEFAULT_HTML)
            else:
                creative = adgroup.default_creative()
            creative.account = account
            creative.put()

    return campaign

def setup_post_request_data(apps=[], network_type=None, account_pub_id=None,
        app_pub_ids={}, adunit_pub_ids={}):

    post_data = {}

    campaign_name = NETWORKS[network_type]
    campaign_form = NetworkCampaignForm({'name': campaign_name})
    post_data.update(campaign_form.data)

    default_adgroup_form = NetworkAdGroupForm()
    post_data.update(default_adgroup_form.data)

    if network_type == 'jumptap':
        post_data['jumptap_pub_id'] = account_pub_id

    for app in apps:
        app_post_key = 'app_%s-%s_pub_id' % (app.key(), network_type)
        post_data[app_post_key] = app_pub_ids[app.key()]

        for adunit in app.adunits:
            adunit_post_key = 'adunit_%s-%s_pub_id' % \
                    (adunit.key(), network_type)
            post_data[adunit_post_key] = adunit_pub_ids[adunit.key()]

            adgroup_form_data = {'bid': DEFAULT_BID}
            if network_type == 'custom':
                adgroup_form_data['custom_html'] = DEFAULT_HTML
            elif network_type == 'custom_native':
                adgroup_form_data['custom_method'] = DEFAULT_HTML
            adgroup_form = AdUnitAdGroupForm(adgroup_form_data)

            for key, item in adgroup_form.data.items():
                prefixed_key = '%s-%s' % (adunit.key(), key)
                post_data[prefixed_key] = item

    print post_data
    return post_data


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
