import copy
import datetime
import os
import sys
import unittest

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from google.appengine.ext import testbed

from advertiser.models import Order, LineItem
from advertiser.forms import (OrderForm, LineItemForm, BaseCreativeForm,
                              TextCreativeForm, TextAndTileCreativeForm,
                              HtmlCreativeForm, ImageCreativeForm)
from common.utils.timezones import Pacific_tzinfo
from common.utils.tzinfo import UTC


class TestOrderForm(unittest.TestCase):
    def setUp(self):
        self.data = {
            'name': 'Test Order Name',
            'advertiser': 'Test Order Advertiser',
        }

    def test_required(self):
        form = OrderForm(self.data)
        self.assertTrue(form.is_valid(), "OrderForm(%s): %s" % (self.data, form._errors.as_text()))
        for key in self.data:
            incomplete_data = copy.deepcopy(self.data)
            del incomplete_data[key]
            form = OrderForm(incomplete_data)
            self.assertFalse(form.is_valid(), "OrderForm(%s): %s was missing but form validated." % (incomplete_data, key))


GUARANTEED_LINE_ITEM_DATA = [
    {
        'adgroup_type': 'gtee',
        'gtee_priority': 'high',
        'name': 'Guaranteed High Line Item',
        'bid_strategy': 'cpc',
        'bid': 0.05,
        'budget': 10000,
        'budget_type': 'daily',
        'budget_strategy': 'allatonce',
    },
    {
        'adgroup_type': 'gtee',
        'gtee_priority': 'normal',
        'name': 'Guaranteed Normal Line Item',
        'bid_strategy': 'cpc',
        'bid': 0.05,
        'budget': 10000,
        'budget_type': 'daily',
        'budget_strategy': 'allatonce',
    },
    {
        'adgroup_type': 'gtee',
        'gtee_priority': 'low',
        'name': 'Guaranteed Low Line Item',
        'bid_strategy': 'cpc',
        'bid': 0.05,
        'budget': 10000,
        'budget_type': 'daily',
        'budget_strategy': 'allatonce',
    },
]

PROMOTIONAL_LINE_ITEM_DATA = [
    {
        'adgroup_type': 'promo',
        'promo_priority': 'normal',
        'name': 'Promotional Line Item',
        'bid_strategy': 'cpc',
        'bid': 0.05,
    },
    {
        'adgroup_type': 'promo',
        'promo_priority': 'backfill',
        'name': 'Backfill Promotional Line Item',
        'bid_strategy': 'cpc',
        'bid': 0.05,
    },
]


class TestLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = GUARANTEED_LINE_ITEM_DATA + PROMOTIONAL_LINE_ITEM_DATA

    def test_new_line_item_datetimes(self):
        now = datetime.datetime.now(Pacific_tzinfo())
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = now - datetime.timedelta(days=1)
        tomorrow = now + datetime.timedelta(days=1)

        invalid_datetimes = [
            (None, yesterday),
            (None, today),
            (None, now),
            (yesterday, None),
            (yesterday, yesterday),
            (yesterday, today),
            (yesterday, now),
            (yesterday, tomorrow),
            (today, yesterday),
            (today, today),
            (now, yesterday),
            (now, today),
            (now, now),
            (tomorrow, yesterday),
            (tomorrow, today),
            (tomorrow, now),
            (tomorrow, tomorrow),
        ]

        valid_datetimes = [
            (None, None, now, None),
            (None, tomorrow, now, tomorrow),
            (today, None, today, None),
            (today, now, today, now),
            (today, tomorrow, today, tomorrow),
            (now, None, now, None),
            (now, tomorrow, now, tomorrow),
            (tomorrow, None, tomorrow, None),
        ]

        data = copy.deepcopy(self.data)
        for test_data in data:
            for start_datetime, end_datetime in invalid_datetimes:
                test_data['start_datetime_0'] = start_datetime.date().strftime('%m/%d/%Y') if start_datetime else ''
                test_data['start_datetime_1'] = start_datetime.time().strftime('%I:%M %p') if start_datetime else ''
                test_data['end_datetime_0'] = end_datetime.date().strftime('%m/%d/%Y') if end_datetime else ''
                test_data['end_datetime_1'] = end_datetime.time().strftime('%I:%M %p') if end_datetime else ''
                form = LineItemForm(test_data)
                self.assertFalse(form.is_valid(), "Form validated with invalid datetimes: start_datetime=%s end_datetime=%s" % (start_datetime, end_datetime))
            for start_datetime, end_datetime, output_start_datetime, output_end_datetime in valid_datetimes:
                test_data['start_datetime_0'] = start_datetime.date().strftime('%m/%d/%Y') if start_datetime else ''
                test_data['start_datetime_1'] = start_datetime.time().strftime('%I:%M %p') if start_datetime else ''
                test_data['end_datetime_0'] = end_datetime.date().strftime('%m/%d/%Y') if end_datetime else ''
                test_data['end_datetime_1'] = end_datetime.time().strftime('%I:%M %p') if end_datetime else ''
                form = LineItemForm(test_data)
                self.assertTrue(form.is_valid(), form._errors.as_text())
                line_item = form.save()
                if output_start_datetime:
                    self.assertTrue(abs(line_item.start_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo()) - output_start_datetime) < datetime.timedelta(minutes=1),
                        "start_datetime should have been %s, was %s (start_datetime: %s, end_datetime: %s)." % (output_start_datetime, line_item.start_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo()), start_datetime, end_datetime))
                else:
                    self.assertEqual(line_item.start_datetime, None, "Input: start_datetime=%s end_datetime=%s. start_datetime was %s" % (start_datetime, end_datetime, line_item.start_datetime))
                if output_end_datetime:
                    self.assertTrue(abs(line_item.end_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo()) - output_end_datetime) < datetime.timedelta(minutes=1),
                        "end_datetime should have been %s, was %s (start_datetime: %s, end_datetime: %s)." % (output_end_datetime, line_item.end_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo()), start_datetime, end_datetime))
                else:
                    self.assertEqual(line_item.end_datetime, None, "Input: start_datetime=%s end_datetime=%s. end_datetime was %s" % (start_datetime, end_datetime, line_item.end_datetime))

    # TODO: keywords > 500 characters causes exception


class TestGuaranteedLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = GUARANTEED_LINE_ITEM_DATA

    def test_budget(self):
        data = copy.deepcopy(self.data)
        for test_data in data:
            # CPC Daily
            test_data['bid_strategy'] = 'cpc'
            test_data['budget_type'] = 'daily'
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            self.assertEqual(line_item.daily_budget, test_data['budget'], "budget was %s, should have been %s" % (line_item.daily_budget, test_data['budget']))
            self.assertEqual(line_item.full_budget, None, "full_budget was %s, should have been %s" % (line_item.full_budget, None))

            # CPC Full
            test_data['budget_type'] = 'full_campaign'
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            self.assertEqual(line_item.daily_budget, None, "budget was %s, should have been %s" % (line_item.daily_budget, None))
            self.assertEqual(line_item.full_budget, test_data['budget'], "full_budget was %s, should have been %s" % (line_item.full_budget, test_data['budget']))

            # CPM Daily
            test_data['bid_strategy'] = 'cpm'
            test_data['budget_type'] = 'daily'
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            budget = test_data['budget'] * test_data['bid'] / 1000
            self.assertEqual(line_item.daily_budget, budget, "budget was %s, should have been %s" % (line_item.daily_budget, budget))
            self.assertEqual(line_item.full_budget, None, "full_budget was %s, should have been %s" % (line_item.full_budget, None))

            # CPM Full
            test_data['budget_type'] = 'full_campaign'
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            full_budget = test_data['budget'] * test_data['bid'] / 1000
            self.assertEqual(line_item.daily_budget, None, "budget was %s, should have been %s" % (line_item.daily_budget, None))
            self.assertEqual(line_item.full_budget, full_budget, "full_budget was %s, should have been %s" % (line_item.full_budget, full_budget))

            # a line_item with no end_datetime and budget_type full_campaign
            # cannot have budget_strategy evenly
            test_data['budget_type'] = 'full_campaign'
            test_data['budget_strategy'] = 'evenly'
            form = LineItemForm(test_data)
            self.assertFalse(form.is_valid(), "budget_strategy was evenly with no end_datetime and full_campaign budget_type but the form validated.")

            test_data['end_datetime_0'] = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime('%m/%d/%Y')
            test_data['end_datetime_1'] = datetime.time().strftime('%I:%M %p')
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()

            # Unlimited
            test_data['budget'] = ''
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            self.assertEqual(line_item.daily_budget, None, "budget was %s, should have been %s" % (line_item.daily_budget, None))
            self.assertEqual(line_item.full_budget, None, "full_budget was %s, should have been %s" % (line_item.full_budget, None))


class TestPromotionalLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = PROMOTIONAL_LINE_ITEM_DATA

    def test_defaults(self):
        data = copy.deepcopy(self.data)
        for test_data in data:
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()
            self.assertEqual(line_item.daily_budget, None, "budget was %s, should have been %s" % (line_item.daily_budget, None))
            self.assertEqual(line_item.full_budget, None, "full_budget was %s, should have been %s" % (line_item.full_budget, None))
            self.assertEqual(line_item.budget_type, 'daily', "budget_type was %s, should have been %s" % (line_item.budget_type, 'daily'))
            self.assertEqual(line_item.budget_strategy, 'allatonce', "budget_strategy was %s, should have been %s" % (line_item.budget_strategy, 'allatonce'))


class TestCreativeForm(unittest.TestCase):
    pass
