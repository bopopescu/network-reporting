import copy
import datetime
import os
import sys
import unittest

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from google.appengine.api import memcache
from google.appengine.ext import testbed

from advertiser.models import Campaign, AdGroup
from advertiser.forms import (CampaignForm, AdGroupForm, BaseCreativeForm,
                              TextCreativeForm, TextAndTileCreativeForm,
                              HtmlCreativeForm, ImageCreativeForm)
from budget.tzinfo import UTC
from common.utils.timezones import Pacific_tzinfo


"""
check creation of creatives
test network config changes
keywords > 500 characters causes exception
make sure bid is filled out (Lighthouse #836)
not be able to have campaign with no end, no budget, spread evenly
"""


class TestDirectSoldCampaignForm(unittest.TestCase):
    def setUp(self):
        self.data = [
            {
                'campaign_type': 'gtee',
                'gtee_priority': 'high',
                'name': 'Gtee High'
            },
            {
                'campaign_type': 'gtee',
                'gtee_priority': 'normal',
                'name': 'Gtee High'
            },
            {
                'campaign_type': 'gtee',
                'gtee_priority': 'low',
                'name': 'Gtee High'
            },
            {
                'campaign_type': 'promo',
                'promo_priority': 'normal',
                'name': 'Gtee High'
            },
            {
                'campaign_type': 'promo',
                'promo_priority': 'backfill',
                'name': 'Gtee High'
            },
        ]

    def test_default_start_datetime(self):
        """ start_datetime defaults to now """
        data = copy.deepcopy(self.data)
        for test_data in data:
            form = CampaignForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            campaign = form.save()
            self.assertTrue(datetime.datetime.now() - campaign.start_datetime < datetime.timedelta(seconds=1))

    def  test_start_datetime(self):
        """ start_datetime cannot be before today """
        data = copy.deepcopy(self.data)
        now = datetime.datetime.now(Pacific_tzinfo())
        yesterday = (now - datetime.timedelta(days=1))
        for test_data in data:
            test_data['start_datetime_0'] = yesterday.date().strftime('%m/%d/%Y')
            test_data['start_datetime_1'] = datetime.time().strftime('%I:%M %p')
            form = CampaignForm(test_data)
            self.assertFalse(form.is_valid(), "start_datetime was %s but the form validated" % test_data)
            test_data['start_datetime_0'] = now.date().strftime('%m/%d/%Y')
            form = CampaignForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            campaign = form.save()
            self.assertEqual(campaign.start_datetime, now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC()).replace(tzinfo=None))

    def test_datetime_timezones(self):
        pass


class TestNetworkAdgroupForm(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_blobstore_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_network_type_choices(self):
        deprecated_network_types = ['admob', 'millennial', 'greystripe']

        adgroup = AdGroup()

        form = AdGroupForm(instance=adgroup)
        # make sure deprecated ad network types are not in network type choices
        for deprecated_network_type in deprecated_network_types:
            self.assertFalse(deprecated_network_type in [choice[0] for choice in form.fields['network_type'].choices], form.fields['network_type'].choices)

        # make sure deprecated ad network types are in network type choices when
        # the user is staff
        form = AdGroupForm(instance=adgroup, is_staff=True)
        for deprecated_network_type in deprecated_network_types:
            self.assertTrue(deprecated_network_type in [choice[0] for choice in form.fields['network_type'].choices], form.fields['network_type'].choices)

        # deprecated network type should be shown if instance has that type
        for deprecated_network_type in deprecated_network_types:
            adgroup = AdGroup(network_type=deprecated_network_type)
            form = AdGroupForm(instance=adgroup)
            self.assertTrue(deprecated_network_type in [choice[0] for choice in form.fields['network_type'].choices], form.fields['network_type'].choices)
            # TODO: make sure the others aren't in here


class TestNetworkCampaignForm(unittest.TestCase):

    def test_datetimes_null(self):
        form = CampaignForm({
            'campaign_type': 'network',
            'name': 'Test Campaign'
        })
        self.assertTrue(form.is_valid(), form._errors.as_text())
        campaign = form.save()
        self.assertEqual(campaign.start_datetime, None, "A network campaign's start_datetime should be null")
        self.assertEqual(campaign.end_datetime, None, "A network campaign's end_datetime should be null")


class TestAdGroupForm(unittest.TestCase):
    def setUp(self):
        self.data = [
            {
                'name': 'Test AdGroup',
                'bid_strategy': 'cpm',
                'bid': 0.1,
            },
        ]

    def test_required_and_default(self):
        data = copy.deepcopy(self.data)
        for test_data in data:
            form = AdGroupForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            adgroup = form.save()
            self.assertEqual(adgroup.allocation_percentage, 100.0)
            for key in test_data:
                incomplete_data = copy.deepcopy(test_data)
                del incomplete_data[key]
                form = AdGroupForm(incomplete_data)
                self.assertFalse(form.is_valid(), "%s was missing but form validated" % key)


"""
class TestCampaignForm(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_blobstore_stub()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.default_data = {
            'campaign_type': 'network',
            'name': 'Testing Campaign',
            'budget_type': 'daily',
            'budget_strategy': 'evenly',
        }

    def tearDown(self):
        self.testbed.deactivate()

    def assertAllFieldsRequired(self, data):
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        for field in data:
            invalid_data = copy.deepcopy(data)
            del invalid_data[field]
            form = CampaignForm(invalid_data)
            self.assertFalse(form.is_valid(), '%s was missing but is_valid returned True.' % field)

    def test_gtee_campaign_type_mptest(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'gtee'
        for gtee_priority, campaign_type in (('high', 'gtee_high'),
                                             ('normal', 'gtee'),
                                             ('low', 'gtee_low')):
            data['gtee_priority'] = gtee_priority
            self.assertAllFieldsRequired(data)
            form = CampaignForm(data)
            self.assertTrue(form.is_valid(), form._errors)
            campaign = form.save()
            self.assertEqual(campaign.campaign_type, campaign_type)

    def test_promo_campaign_type_mptest(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'promo'
        for promo_priority, campaign_type in (('normal', 'promo'),
                                              ('backfill', 'backfill_promo')):
            data['promo_priority'] = promo_priority
            self.assertAllFieldsRequired(data)
            form = CampaignForm(data)
            self.assertTrue(form.is_valid(), form._errors)
            campaign = form.save()
            self.assertEqual(campaign.campaign_type, campaign_type)

    def test_network_campaign_type_mptest(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'network'
        self.assertAllFieldsRequired(data)

    def test_start_datetime_mptest(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'network'
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        campaign = form.save()
        # make sure start_datetime is set to the current time
        # use a margin of one second
        self.assertTrue(datetime.datetime.now(Pacific_tzinfo()) - campaign.start_datetime < datetime.timedelta(seconds=1))

    def test_budget_mptest(self):
        data = copy.deepcopy(self.default_data)
        data['budget_type'] = 'daily'
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        campaign = form.save()
        self.assertEqual(campaign.full_budget, None)
        data['budget_type'] = 'full_campaign'
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        campaign = form.save()
        self.assertEqual(campaign.budget, None)

    def start_date_mptest(self):


class TestAdGroupForm(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.default_data = {
            'bid_strategy': 'cpm',
            'bid': .1,
            'allocation_type': 'users',
            'device_targeting': '0',
            'region_targeting': 'all',
        }

    def tearDown(self):
        self.testbed.deactivate()

    def test_network_type_mptest(self):
        campaign = Campaign(campaign_type='network', name='Test Campaign')
        campaign.save()

        data = copy.deepcopy(self.default_data)
        data['campaign'] = campaign

        form = AdGroupForm(data)
        self.assertFalse(form.is_valid(), 'is_valid returned True on a network campaign with no network type.')

        data['network_type'] = 'admob'
        self.assertTrue(form.is_valid(), form._errors)

    def test_bid_mptest(self):
        pass

    def test_creative_mptest(self):
        pass

    def test_allocation_default_mptest(self):
        pass


class TestCreativeForm(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

    def tearDown(self):
        self.testbed.deactivate()

    def test_base_creative_mptest(self):
        form = BaseCreativeForm()
"""
