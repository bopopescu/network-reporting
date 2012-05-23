import copy
import datetime
import os
import sys
import unittest

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from nose.tools import ok_, eq_

from google.appengine.ext import testbed

from advertiser.models import Order, LineItem
from advertiser.forms import (OrderForm, LineItemForm, ImageCreativeForm,
                              TextAndTileCreativeForm, HtmlCreativeForm)
from common.utils.timezones import Pacific_tzinfo
from common.utils.tzinfo import UTC
from common.utils.test.test_utils import time_almost_eq


class TestOrderForm(unittest.TestCase):
    def setUp(self):
        self.data = {
            'name': 'Test Order Name',
            'advertiser': 'Test Order Advertiser',
        }

    def mptest_required(self):
        form = OrderForm(self.data)
        ok_(form.is_valid(), 
            "OrderForm(%s): %s" % (self.data, form._errors.as_text()))

        for key in self.data:
            incomplete_data = copy.deepcopy(self.data)
            del incomplete_data[key]
            form = OrderForm(incomplete_data)
            ok_(not form.is_valid(), 
                "OrderForm(%s): %s was missing but form validated." % \
                (incomplete_data, key))


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

    def mptest_new_line_item_datetimes(self):
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
                test_data['start_datetime_0'] = _parse_datetime(start_datetime)
                test_data['start_datetime_1'] = _parse_hour_time(start_datetime)
                test_data['end_datetime_0'] = _parse_datetime(end_datetime)
                test_data['end_datetime_1'] = _parse_hour_time(end_datetime)
                form = LineItemForm(test_data)
                ok_(not form.is_valid(), 
                    "Form validated with invalid datetimes: start_datetime=%s end_datetime=%s" % \
                    (start_datetime, end_datetime))

            for start_datetime, end_datetime, output_start_datetime, output_end_datetime in valid_datetimes:
                test_data['start_datetime_0'] = _parse_datetime(start_datetime)
                test_data['start_datetime_1'] = _parse_hour_time(start_datetime)
                test_data['end_datetime_0'] = _parse_datetime(end_datetime)
                test_data['end_datetime_1'] = _parse_hour_time(end_datetime)

                form = LineItemForm(test_data)
                self.assertTrue(form.is_valid(), form._errors.as_text())
                line_item = form.save()

                should_have_been_message = "%s should have been %s, was %s \
                                            (start_datetime: %s, end_datetime: %s)."
                datetime_none_message = "Input: start_datetime=%s end_datetime=%s. %s was %s"

                if output_start_datetime:
                    pac_start_datetime = _as_pacific_time(line_item.start_datetime)
                    time_almost_eq(pac_start_datetime, output_start_datetime,
                                   should_have_been_message % ('start_datetime', 
                                                               output_start_datetime, pac_start_datetime, 
                                                               start_datetime, end_datetime))
                else:
                    ok_(not line_item.start_datetime, datetime_none_message % \
                        (start_datetime, end_datetime, 'start_datetime', line_item.start_datetime))

                if output_end_datetime:
                    pac_end_datetime = _as_pacific_time(line_item.end_datetime)
                    time_almost_eq(pac_end_datetime, output_end_datetime,
                                   should_have_been_message % ('end_datetime', 
                                                               output_start_datetime, pac_end_datetime, 
                                                               start_datetime, end_datetime))
                else:
                    ok_(not line_item.end_datetime, datetime_none_message % \
                        (start_datetime, end_datetime, 'end_datetime', line_item.end_datetime))

    # TODO: keywords > 500 characters causes exception

def _parse_hour_time(date):
    return date.time().strftime('%I:%M %p') if date else ''


def _parse_datetime(date):
    return date.date().strftime('%m/%d/%Y') if date else ''


def _as_pacific_time(date):
    return date.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo())


class TestGuaranteedLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(GUARANTEED_LINE_ITEM_DATA)

    def mptest_cpc_daily_budget(self):
        for test_data in self.data:
            _test_line_item_for_budget(test_data, 'cpc', 'daily', 
                                       [test_data['budget'], None])

    def mptest_cpc_full_budget(self):
        for test_data in self.data:
            _test_line_item_for_budget(test_data, 'cpc', 'full_campaign', 
                                       [None, test_data['budget']])
    def mptest_cpm_daily_budget(self):
        for test_data in self.data:
            cpm_budget = test_data['budget'] * test_data['bid'] / 1000
            _test_line_item_for_budget(test_data, 'cpm', 'daily', 
                                       [cpm_budget, None])
    def mptest_cpm_full_budget(self):
        for test_data in self.data:
            cpm_budget = test_data['budget'] * test_data['bid'] / 1000
            _test_line_item_for_budget(t8est_data, 'cpc', 'full_campaign', 
                                       [None, cpm_budget])
    def mptest_unlimited_budget(self):
        for test_data in self.data:
            test_data['budget'] = ''
            _test_line_item_for_budget(test_data, 'cpc', 'daily', 
                                       [None, None])

    def mptest_invalid_budget(self):
        for test_data in self.data:
            test_data['budget_type'] = 'full_campaign'
            test_data['budget_strategy'] = 'evenly'
            form = LineItemForm(test_data)
            ok_(not form.is_valid(), 
                "Form should not validate with full_campaign \
                spread evenly.")

            test_data['end_datetime_0'] = _parse_datetime(datetime.datetime.now().date() + datetime.timedelta(days=1))
            test_data['end_datetime_1'] = _parse_hour_time(datetime)
            form = LineItemForm(test_data)
            self.assertTrue(form.is_valid(), form._errors.as_text())
            line_item = form.save()


def _test_line_item_for_budget(data, bid_strategy=None, budget_type=None, expected):
    if bid_strategy:
        data['bid_strategy'] = bid_strategy
    if budget_type:
        data['budget_type'] = budget_type

    form = LineItemForm(data)
    ok_(form.is_valid(), form._errors.as_text())

    eq_(line_item.daily_budget, expected[0])
    eq_(line_item.full_budget, expected[1])

    eq_(line_item.bid_strategy, data['bid_strategy'])
    eq_(line_item.budget_type, data['budget_type'])


class TestPromotionalLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(PROMOTIONAL_LINE_ITEM_DATA)

    def mptest_defaults(self):
        for test_data in self.data:
            line_item = _test_line_item_for_budget(test_data, expected=[None, None])


class TestCreativeForm(unittest.TestCase):
    pass
