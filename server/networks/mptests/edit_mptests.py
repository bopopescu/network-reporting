import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse

import simplejson as json

from google.appengine.ext import db

from networks.mptests.network_test_case import NetworkTestCase, \
        DEFAULT_BID, \
        DEFAULT_HTML, \
        DEFAULT_PUB_ID
from common.utils.test.test_utils import dict_eq
from common.constants import NETWORKS

from networks.views import NETWORKS_WITH_PUB_IDS

from account.query_managers import NetworkConfigQueryManager
from advertiser.query_managers import AdGroupQueryManager
from publisher.query_managers import AppQueryManager, \
        AdUnitQueryManager

from account.models import NetworkConfig
from advertiser.models import AdGroup
from ad_network_reports.models import AdNetworkAppMapper, \
        LoginStates

from ad_network_reports.forms import LoginCredentialsForm
from networks.forms import NetworkCampaignForm, \
        NetworkAdGroupForm, \
        AdUnitAdGroupForm


class EditNetworkGetTestCase(NetworkTestCase):
    def setUp(self):
        super(EditNetworkGetTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.existing_campaign = self.generate_network_campaign(
                self.network_type, self.account, self.existing_apps)

        if self.network_type in NETWORKS_WITH_PUB_IDS:
            for app_idx, app in enumerate(self.existing_apps):
                nc = NetworkConfig()
                pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
                setattr(nc, '%s_pub_id' % self.network_type, pub_id)
                NetworkConfigQueryManager.put(nc)
                app.network_config = nc
                AppQueryManager.put(app)

                for adunit_idx, adunit in enumerate(app.adunits):
                    nc = NetworkConfig()
                    setattr(nc, '%s_pub_id' % self.network_type, '%s_%s' %
                            (pub_id, adunit_idx))
                    NetworkConfigQueryManager.put(nc)
                    adunit.network_config = nc
                    AdUnitQueryManager.put(adunit)

        self.url = reverse('edit_network',
                kwargs={'campaign_key': str(self.existing_campaign.key())})

    def network_type_to_test(self):
        return 'admob'

    def mptest_response_code(self):
        """When editing a network campaign, response code should be 200.

        Author: Tiago Bandeira
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)

    def mptest_context(self):
        """The context given to the template should be valid.

        Author: Tiago Bandeira
        """
        response = self.client.get(self.url)
        context = response.context

        network_data = {'name': self.network_type,
                        'pretty_name': NETWORKS[self.network_type],
                        'show_login': False,
                        'login_state': LoginStates.NOT_SETUP}

        dict_eq(network_data, context['network'])

        eq_(str(self.account.key()), context['account_key'])

        ok_(not context['custom_campaign'] or (context['custom_campaign'] and
            self.network_type in ('custom', 'custom_native')))

        ok_(isinstance(response.context['campaign_form'], NetworkCampaignForm))

        eq_(str(self.existing_campaign.key()), context['campaign_key'])

        ok_(isinstance(response.context['login_form'], LoginCredentialsForm))

        ok_(isinstance(response.context['adgroup_form'], NetworkAdGroupForm))

        eq_(len(self.existing_apps), len(context['apps']))
        for app_idx, app in enumerate(context['apps']):
            pub_id = '%s_%s' % (DEFAULT_PUB_ID, app_idx)
            eq_(getattr(app.network_config, '%s_pub_id' % self.network_type),
                    pub_id)

            for adunit_idx, adunit in enumerate(app.adunits):
                ok_(isinstance(adunit.adgroup_form, AdUnitAdGroupForm))

                eq_(getattr(adunit.network_config, '%s_pub_id' %
                    self.network_type), '%s_%s' % (pub_id, adunit_idx))

        ok_(not response.context['reporting'])


class EditNetworkPostTestCase(NetworkTestCase):
    def setUp(self):
        super(EditNetworkPostTestCase, self).setUp()

        self.network_type = self.network_type_to_test()
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.existing_campaign = self.generate_network_campaign(self.network_type,
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

        self.post_data = self.setup_post_request_data(apps=self.existing_apps,
                network_type=self.network_type, app_pub_ids=app_pub_ids,
                adunit_pub_ids=adunit_pub_ids)

    def network_type_to_test(self):
        return 'admob'

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
        for app in self.get_apps_with_adunits(self.account):
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
