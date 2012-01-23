# TODO: remove
import logging

import copy
import datetime
import unittest

from common.utils.timezones import Pacific_tzinfo
from forms import CampaignForm, AdGroupForm

class TestCampaignForm(unittest.TestCase):

    def setUp(self):
        self.default_data = {
            'name': 'Testing Campaign',
            'budget_type': 'daily',
            'budget_strategy': 'evenly',
        }

    def assertAllFieldsRequired(self, data):
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        for field in data:
            invalid_data = copy.deepcopy(data)
            del invalid_data[field]
            form = CampaignForm(invalid_data)
            self.assertFalse(form.is_valid(), '%s was missing but is_valid returned True.' % field)

    def test_gtee_campaign_type(self):
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

    def test_promo_campaign_type(self):
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

    def test_network_campaign_type(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'network'
        self.assertAllFieldsRequired(data)

    def test_start_datetime(self):
        data = copy.deepcopy(self.default_data)
        data['campaign_type'] = 'network'
        form = CampaignForm(data)
        self.assertTrue(form.is_valid(), form._errors)
        campaign = form.save()
        # make sure start_datetime is set to the current time
        # use a margin of one second
        self.assertTrue(datetime.datetime.now(Pacific_tzinfo()) - campaign.start_datetime < datetime.timedelta(seconds=1))
