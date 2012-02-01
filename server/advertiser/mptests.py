import copy
import datetime
import logging # TODO: remove
import os
import sys
import unittest

from google.appengine.api import memcache
from google.appengine.ext import testbed

sys.path.append(os.environ['PWD'])

import common.utils.test.setup
from common.utils.timezones import Pacific_tzinfo
from advertiser.models import Campaign, AdGroup
from advertiser.forms import (CampaignForm, AdGroupForm, BaseCreativeForm,
                              TextCreativeForm, TextAndTileCreativeForm,
                              HtmlCreativeForm, ImageCreativeForm)


class TestCampaignForm(unittest.TestCase):

    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
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
