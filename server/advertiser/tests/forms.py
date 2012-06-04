import copy
import datetime
import os
import sys
import unittest
import base64

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from nose.tools import ok_, eq_

from django.core.files.uploadedfile import SimpleUploadedFile

from advertiser.models import Order, LineItem, Creative
from advertiser.forms import (OrderForm, LineItemForm,
                              NewCreativeForm, ImageCreativeForm,
                              TextAndTileCreativeForm, HtmlCreativeForm)
from common.utils.timezones import Pacific_tzinfo
from common.utils.date_magic import utc_to_pacific, pacific_to_utc, get_next_day
from common.utils.test.test_utils import time_almost_eq, model_eq

from google.appengine.api import images

from admin.randomgen import (generate_account, generate_marketplace_campaign,
                             generate_campaign, generate_adgroup)

class TestOrderForm(unittest.TestCase):
    def setUp(self):
        self.data = {
            'name': 'Test Order Name',
            'advertiser': 'Test Order Advertiser',
        }
        self.account = generate_account()

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

    def mptest_campaign_must_be_order(self):
        non_order_campaign = generate_marketplace_campaign(self.account)

        try:
            form = OrderForm(self.data, instance=non_order_campaign)
        except Exception, e:
            eq_(e.message, 'Campaign instance must be an order.')
        else:
            ok_(False, 'Proper exception not raised \
                        for non-order campaign instances')

    def mptest_correct_form_is_returned(self):
        order = generate_campaign(self.account)
        form = OrderForm(self.data, instance=order)

        ok_(form.is_valid())
        form_order = form.save()
        ok_(isinstance(form_order, Order))
        model_eq(order, form_order)


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
            _test_line_item_for_budget(test_data, 'cpm', 'full_campaign',
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

            test_data['end_datetime_0'] = _parse_datetime(datetime.datetime.now() + datetime.timedelta(days=1))
            test_data['end_datetime_1'] = _parse_hour_time(datetime.time())
            form = LineItemForm(test_data)
            ok_(form.is_valid(), form._errors.as_text())
            form.save()

    def mptest_init_budgets(self):
        # high/low
        # daily/non
        # no budget/cpm
        pass

    def mptest_fail_without_priority(self):
        for test_data in self.data:
            del test_data['gtee_priority']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['gtee_priority'].errors, ['This field is required'])

    def mptest_clean_priority(self):
        gtee_types = ['gtee_high', 'gtee', 'gtee_low']
        for test_data, adgroup_type in zip(self.data, gtee_types):
            form = LineItemForm(test_data)
            form.is_valid()
            eq_(form.cleaned_data['adgroup_type'], adgroup_type)

    def mptest_clean_non_budget(self):
        for test_data in self.data:
            del test_data['budget']
            form = LineItemForm(test_data)
            form.is_valid()
            ok_(not form.cleaned_data['daily_budget'])
            ok_(not form.cleaned_data['full_budget'])

    def mptest_fail_with_missing_budget_field(self):
        for test_data in copy.deepcopy(self.data):
            del test_data['bid_strategy']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['bid_strategy'].errors, ['This field is required'])

        for test_data in copy.deepcopy(self.data):
            del test_data['bid']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['bid'].errors, ['This field is required'])

        for test_data in copy.deepcopy(self.data):
            del test_data['budget_type']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['budget_type'].errors, ['This field is required'])

        for test_data in copy.deepcopy(self.data):
            del test_data['budget_strategy']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['budget_strategy'].errors, ['This field is required'])


def _test_line_item_for_budget(data, bid_strategy=None, budget_type=None, expected=[None, None]):
    if bid_strategy:
        data['bid_strategy'] = bid_strategy
    if budget_type:
        data['budget_type'] = budget_type

    form = LineItemForm(data)
    ok_(form.is_valid(), form._errors.as_text())
    line_item = form.save()

    eq_(line_item.daily_budget, expected[0])
    eq_(line_item.full_budget, expected[1])

    eq_(line_item.bid_strategy, data.get('bid_strategy'))
    eq_(line_item.budget_type, data.get('budget_type'))


PROMOTIONAL_LINE_ITEM_DATA = [
    {
        'adgroup_type': 'promo',
        'promo_priority': 'normal',
        'name': 'Promotional Line Item',
        'bid_strategy': 'cpc',
    },
    {
        'adgroup_type': 'promo',
        'promo_priority': 'backfill',
        'name': 'Backfill Promotional Line Item',
        'bid_strategy': 'cpc',
    },
]


class TestPromotionalLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(PROMOTIONAL_LINE_ITEM_DATA)

    def mptest_defaults(self):
        for test_data in self.data:
            _test_line_item_for_budget(test_data, expected=[None, None])

    def mptest_required_fields(self):
        for test_data in self.data:
            form = LineItemForm(test_data)
            ok_(form.is_valid(),
                "LineItemForm(%s): %s" % (test_data, form._errors.as_text()))

            for key in test_data:
                incomplete_data = copy.deepcopy(test_data)
                del incomplete_data[key]
                form = LineItemForm(incomplete_data)
                ok_(not form.is_valid(),
                    "LineItemForm(%s): %s was missing but form validated." % \
                    (incomplete_data, key))

    def mptest_fail_without_priority(self):
        for test_data in self.data:
            del test_data['promo_priority']
            form = LineItemForm(test_data)
            ok_(not form.is_valid())
            eq_(form['promo_priority'].errors, ['This field is required'])

    def mptest_clean_priority(self):
        gtee_types = ['promo', 'backfill_promo']
        for test_data, adgroup_type in zip(self.data, gtee_types):
            form = LineItemForm(test_data)
            form.is_valid()
            eq_(form.cleaned_data['adgroup_type'], adgroup_type)

    def mptest_clean_budget(self):
        for test_data in self.data:
            form = LineItemForm(test_data)
            form.is_valid()
            ok_(not form.cleaned_data['daily_budget'])
            ok_(not form.cleaned_data['full_budget'])
            ok_(not form.cleaned_data['budget_type'])
            ok_(not form.cleaned_data['budget_strategy'])

class TestLineItemForm(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(GUARANTEED_LINE_ITEM_DATA + PROMOTIONAL_LINE_ITEM_DATA)
        self.account = generate_account()

    def mptest_valid_form(self):
        data = PROMOTIONAL_LINE_ITEM_DATA[0]
        form = LineItemForm(data)
        ok_(form.is_valid(),
            "LineItemForm(%s): %s" % (data, form._errors.as_text()))

    def mptest_save_clears_adunit_cache(self):
        # figure out how to stub call to adunitquerycontextmanager
        pass

    def mptest_save_returns_proper_line_items(self):
        order = generate_campaign(self.account)
        for line_item_data in self.data:
            line_item = generate_adgroup(order, site_keys=[], account=self.account,
                                         adgroup_type=line_item_data['adgroup_type'])
            form = LineItemForm(line_item_data, instance=line_item)

            ok_(form.is_valid())
            form_line_item = form.save()
            ok_(isinstance(form_line_item, LineItem))
            model_eq(line_item, form_line_item)

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
                    pac_start_datetime = utc_to_pacific(line_item.start_datetime)
                    time_almost_eq(pac_start_datetime, output_start_datetime,
                                   message=should_have_been_message % ('start_datetime',
                                                                       output_start_datetime, pac_start_datetime,
                                                                       start_datetime, end_datetime))
                else:
                    ok_(not line_item.start_datetime, datetime_none_message % \
                        (start_datetime, end_datetime, 'start_datetime', line_item.start_datetime))

                if output_end_datetime:
                    pac_end_datetime = utc_to_pacific(line_item.end_datetime)
                    time_almost_eq(pac_end_datetime, output_end_datetime,
                                   message=should_have_been_message % ('end_datetime',
                                                                       output_start_datetime, pac_end_datetime,
                                                                       start_datetime, end_datetime))
                else:
                    ok_(not line_item.end_datetime, datetime_none_message % \
                        (start_datetime, end_datetime, 'end_datetime', line_item.end_datetime))


def _parse_hour_time(date):
    return date.strftime('%I:%M %p') if isinstance(date, datetime.time) \
                                     or isinstance(date, datetime.datetime) else ''


def _parse_datetime(date):
    return date.date().strftime('%m/%d/%Y') if isinstance(date, datetime.datetime) else ''


class LineItemCleanMethodsTestCase(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(PROMOTIONAL_LINE_ITEM_DATA[0])
        self.now = datetime.datetime.now()
        self.yesterday = self.now - datetime.timedelta(days=1)
        self.tomorrow = self.now + datetime.timedelta(days=1)

    def mptest_clean_start_datetime(self):
        self.data['start_datetime_0'] = _parse_datetime(self.tomorrow)
        self.data['start_datetime_1'] = _parse_hour_time(self.tomorrow)

        form = LineItemForm(self.data)
        form.is_valid()
        eq_(form.cleaned_data['start_datetime'],
            pacific_to_utc(self.tomorrow).replace(second=0, microsecond=0))

    def mptest_clean_new_start_datetime(self):
        self.data['start_datetime_0'] = _parse_datetime(self.yesterday)
        self.data['start_datetime_1'] = _parse_hour_time(self.yesterday)

        form = LineItemForm(self.data)
        ok_(not form.is_valid())
        eq_(form['start_datetime'].errors, ['Start time must be in the future'])

    def mptest_clean_end_datetime(self):
        self.data['end_datetime_0'] = _parse_datetime(self.tomorrow)
        self.data['end_datetime_1'] = _parse_hour_time(self.tomorrow)

        form = LineItemForm(self.data)
        form.is_valid()
        eq_(form.cleaned_data['end_datetime'],
            pacific_to_utc(self.tomorrow).replace(second=0, microsecond=0))

    def mptest_cannot_change_end_datetime_after_completion(self):
        # TODO: fix the forms to make this change
        account = generate_account()
        order = generate_campaign(account)
        line_item = generate_adgroup(order, site_keys=[], account=account,
                                     adgroup_type=self.data['adgroup_type'])

        line_item.end_datetime = self.yesterday

        form = LineItemForm(self.data, instance=line_item)
        ok_(not form.is_valid())
        eq_(form['end_datetime'].errors, ['End datetime cannot be changed after line item completion'])

    def mptest_end_before_start(self):
        self.data['start_datetime_0'] = _parse_datetime(self.tomorrow)
        self.data['start_datetime_1'] = _parse_hour_time(self.tomorrow)
        self.data['end_datetime_0'] = _parse_datetime(self.now)
        self.data['end_datetime_1'] = _parse_hour_time(self.now)

        form = LineItemForm(self.data)
        ok_(not form.is_valid())
        eq_(form['end_datetime'].errors, ['End datetime must be after start datetime'])

    def mptest_clean_allocation_percentage(self):
        # this fails because the form does not validate because the field is a floatfield
        # the clean method we have is unecessary, commenting out for now
        self.data['allocation_percentage'] = 'not float or int'

        form = LineItemForm(self.data)
        form.is_valid()
        eq_(form.cleaned_data['allocation_percentage'], 100)

    def mptest_clean_site_keys(self):
        pass

    def mptest_clean_geo_predicates(self):
        pass

    def mptest_clean_keywords(self):
        # 501 character long string
        long_keywords = base64.urlsafe_b64encode(os.urandom(501))
        self.data['keywords'] = long_keywords

        form = LineItemForm(self.data)
        form.is_valid()
        eq_(form['keywords'].errors, ['Maximum 500 characters for keywords'])

    def mptest_clean_targeted_cities(self):
        # we may want to keep this long
        self.data['region_targeting'] = 'all'

        form = LineItemForm(self.data)
        form.is_valid()
        eq_(form.cleaned_data['cities'], [])

SHARED_CREATIVE_DATA = {
    'format': '320x50',
    'ad_type': 'html',
    'name': 'Test Creative',
}

IMAGE_CREATIVE_DATA = {
    'ad_type': 'image',
}

TEXT_TILE_CREATIVE_DATA = {
    'ad_type': 'text_icon',
}

HTML_CREATIVE_DATA = {
    'ad_type': 'html',
    'html_data': '',
    'ormma_html': False,
}

class TestCreativeForm(unittest.TestCase):
    def setUp(self):
        self.image_data = copy.deepcopy(dict(SHARED_CREATIVE_DATA,
                                             **IMAGE_CREATIVE_DATA))
        pwd = os.path.dirname(os.path.abspath(__file__))
        test_banner_path = os.path.join(pwd, 'test_banner.gif')
        print test_banner_path
        upload_file = file(test_banner_path, 'rb')
        self.files = dict(image_file=SimpleUploadedFile(upload_file.name, upload_file.read()))

        self.text_tile_data = copy.deepcopy(dict(SHARED_CREATIVE_DATA,
                                                 **TEXT_TILE_CREATIVE_DATA))
        self.html_data = copy.deepcopy(dict(SHARED_CREATIVE_DATA,
                                            **HTML_CREATIVE_DATA))

    def mptest_save_itunes_id(self):
        self.html_data['url'] = 'http://itunes.apple.com/il/app/imosaic-project/id335853048?mt=8'
        form = HtmlCreativeForm(self.html_data)
        form.is_valid()
        creative = form.save()
        eq_(creative.conv_appid, '335853048')

    def mptest_save_phobos_id(self):
        self.html_data['url'] = 'http://phobos.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=386584429&mt=8'
        form = HtmlCreativeForm(self.html_data)
        form.is_valid()
        creative = form.save()
        eq_(creative.conv_appid, '386584429')

    def mptest_save_android_id(self):
        self.html_data['url'] = 'market://details?id=com.example.admob.lunarlander'
        form = HtmlCreativeForm(self.html_data)
        form.is_valid()
        creative = form.save()
        eq_(creative.conv_appid, 'com.example.admob.lunarlander')

    def mptest_save_none_for_invalid_id(self):
        self.html_data['url'] = 'http://invalid-id.com'
        form = HtmlCreativeForm(self.html_data)
        form.is_valid()
        creative = form.save()
        ok_(not creative.conv_appid)

    def mptest_save_image_file(self):
        img_data = self.files['image_file'].read()
        img = images.Image(img_data)

        form = ImageCreativeForm(self.image_data, self.files)
        form.is_valid()
        creative = form.save()
        eq_(creative.image_width, img.width)
        eq_(creative.image_height, img.height)
        # maybe should check the blob store

    def mptest_clean_name(self):
        name = ' Creative with white space   '
        self.html_data['name'] = name
        form = HtmlCreativeForm(self.html_data)
        form.is_valid()
        eq_(form.cleaned_data['name'], name.strip())

    def mptest_clean_url(self):
        # clean method is unecessary again
        pass

    def sk(self):
        pass
