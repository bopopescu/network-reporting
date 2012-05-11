# don't remove, necessary to set up the test env
import sys
import os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from common.utils.test.views import BaseViewTestCase

import logging
import simplejson as json
from django.core.urlresolvers import reverse
from django.test.utils import setup_test_environment
from django.http import Http404
from nose.tools import eq_, ok_, assert_raises

from admin.randomgen import (generate_campaign, generate_adgroup, \
                             generate_creative, generate_app, \
                             generate_account, generate_marketplace_campaign)

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)
from advertiser.forms import OrderForm, LineItemForm
from publisher.query_managers import AppQueryManager

setup_test_environment()


class OrderViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(OrderViewTestCase, self).setUp()
        self.order = generate_campaign(self.account)
        self.line_item = generate_adgroup(self.order,
                                          [],
                                          self.account,
                                          'gtee')
        self.creative = generate_creative(self.account, self.line_item)


class OrderAndLineItemCreate(OrderViewTestCase):
    def setUp(self):
        super(OrderAndLineItemCreate, self).setUp()
        self.url = reverse('advertiser_order_and_line_item_form_new')

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        response = self.client.get(self.url)
        ok_(response.status_code in [200, 302])

    def mptest_get_correct_forms_with_no_keys(self):
        order = None
        line_item = None
        order_form = OrderForm(instance=order, prefix='order')
        line_item_form = LineItemForm(instance=line_item)

        no_key_url = reverse('advertiser_order_and_line_item_form_new')
        response = self.client.get(no_key_url)
        eq_(response.context['order_form'].instance, None)
        eq_(response.context['line_item_form'].instance, None)


class NewOrEditLineItemGetTestCase(OrderViewTestCase):
    def setUp(self):
        super(NewOrEditLineItemGetTestCase, self).setUp()
        self.new_url = reverse('advertiser_line_item_form_new', kwargs={
            'order_key': unicode(self.order.key())
        })
        self.edit_url = reverse('advertiser_line_item_form_edit', kwargs={
            'line_item_key': unicode(self.line_item.key())
        })

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        new_response = self.client.get(self.new_url)
        edit_response = self.client.get(self.edit_url)
        ok_(new_response.status_code in [200, 302])
        ok_(edit_response.status_code in [200, 302])

    def mptest_get_correct_forms_with_order(self):
        line_item = None
        order_form = OrderForm(instance=self.order, prefix='order')
        line_item_form = OrderForm(instance=line_item)

        response = self.client.get(self.new_url)
        eq_(response.context['order_form'].instance.key(),
            order_form.instance.key())
        eq_(response.context['line_item_form'].instance, None)

    def mptest_get_correct_forms_with_line_item(self):
        order_form = OrderForm(instance=self.order, prefix='order')
        line_item_form = LineItemForm(instance=self.line_item)

        response = self.client.get(self.edit_url)
        eq_(response.context['order_form'].instance.key(),
            order_form.instance.key())
        eq_(response.context['line_item_form'].instance.key(),
            line_item_form.instance.key())

    def mptest_order_owns_line_item(self):
        response = self.client.get(self.edit_url)
        eq_(response.context['order'],
            response.context['line_item'].campaign)

    # don't know if these will be necessary
    # we should just test that all models dont change state
    def mptest_user_owns_order(self):
        ok_(False)

    def mptest_user_owns_line_item(self):
        ok_(False)

    def mptest_fail_on_unowned_order(self):
        diff_acct = generate_account(username='diff')
        diff_order = generate_campaign(account=diff_acct)
        diff_url = reverse('advertiser_line_item_form_new',
                           kwargs={'order_key':
                                   unicode(diff_order.key())})
        # Test passes if we receive the proper exception
        # else the exception will fail loudly and the test will fail
        try:
            self.client.get(diff_url)
        except Http404:
            pass
        else:
            ok_(False)

    def mptest_fail_on_unowned_line_item(self):
        diff_acct = generate_account(username='diff')
        diff_order = generate_campaign(account=diff_acct)
        diff_line_item = generate_adgroup(diff_order,
                                          [],
                                          diff_acct,
                                          'gtee')
        diff_url = reverse('advertiser_line_item_form_edit',
                           kwargs={'line_item_key':
                                   unicode(diff_line_item.key())})
        try:
            self.client.get(diff_url)
        except Http404:
            pass
        else:
            ok_(False)

    def mptest_gets_correct_apps(self):
        app1 = generate_app(self.account)
        app2 = generate_app(self.account)
        response = self.client.get(self.edit_url)

        expected_apps = AppQueryManager.get_apps(account=self.account,
                                        alphabetize=True)
        actual_apps = response.context['apps']
        for actual_app, expected_app in zip(actual_apps, expected_apps):
            eq_(actual_app.key(), expected_app.key())


class NewOrEditLineItemPostTestCase(OrderViewTestCase):
    """
    Tests for the new/edit line item POST method.
    Author: John Pena
    """
    def setUp(self):
        """
        Sets up the new and edit urls.
        """
        super(NewOrEditLineItemPostTestCase, self).setUp()
        self.new_url = reverse('advertiser_line_item_form_new', kwargs={
            'order_key': unicode(self.order.key())
        })
        self.edit_url = reverse('advertiser_line_item_form_edit', kwargs={
            'line_item_key': unicode(self.line_item.key())
        })


    def mptest_graceful_fail_without_data(self):
        """
        Posting to the form handler should fail if there's no post body.
        """
        response = self.client.post(self.new_url,HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

        response = self.client.post(self.edit_url,HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)


    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.
        """
        response = self.client.post(self.new_url)
        eq_(response.status_code, 404)

        response = self.client.post(self.edit_url)
        eq_(response.status_code, 404)


    def mptest_graceful_fail_for_non_order(self):
        """
        Posting to the edit form handler with a non-order campaign (marketplace
        or network) should fail gracefully.
        """
        non_order_mpx = generate_marketplace_campaign(self.account, None)
        url = reverse('advertiser_line_item_form_new', kwargs = {
            'order_key': unicode(non_order_mpx.key())
        })
        response = self.client.post(url)
        eq_(response.status_code, 404)

        non_order_network = generate_marketplace_campaign(self.account, None)
        url = reverse('advertiser_line_item_form_new', kwargs = {
            'order_key': unicode(non_order_network.key())
        })
        response = self.client.post(url)
        eq_(response.status_code, 404)


    def mptest_fail_when_line_item_not_owned(self):
        """
        A line item should not be editable by accounts that don't
        own it.
        """
        diff_account = generate_account(username='diff')
        order = generate_campaign(diff_account)
        line_item = generate_adgroup(order, [], diff_account, 'gtee')
        url = reverse('advertiser_line_item_form_edit', kwargs = {
            'line_item_key': unicode(line_item.key())
        })

        post_body = {

            # common form parameters
            u'ajax': [u'true'],

            # order form parameters
            u'order-advertiser': [u'Testingco'],
            u'order-description': [u''],
            u'order-name': [u'Test Order'],

            # line item form parameters
            u'adgroup_type': [u'gtee'],
            u'allocation_percentage': [u'100.0'],
            u'android_version_max': [u'999'],
            u'android_version_min': [u'1.5'],
            u'bid': [u'0.05'],
            u'bid_strategy': [u'cpm'],
            u'budget': [u''],
            u'budget_strategy': [u'allatonce'],
            u'budget_type': [u'daily'],
            u'daily_frequency_cap': [u'0'],
            u'device_targeting': [u'0'],
            u'end_datetime_0': [u'05/31/2012'],
            u'end_datetime_1': [u'11:59 PM'],
            u'gtee_priority': [u'normal'],
            u'hourly_frequency_cap': [u'0'],
            u'ios_version_max': [u'999'],
            u'ios_version_min': [u'2.0'],
            u'keywords': [u''],
            u'name': [u'Test Line Item'],
            u'promo_priority': [u'normal'],
            u'region_targeting': [u'all'],
            u'start_datetime_0': [u'05/30/2012'],
            u'start_datetime_1': [u'12:00 AM'],
            u'target_android': [u'on'],
            u'target_ipad': [u'on'],
            u'target_iphone': [u'on'],
            u'target_ipod': [u'on'],
            u'target_other': [u'on']
        }

        response = self.client.post(url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(response.status_code, 404)


    def mptest_puts_new_valid_line_item(self):
        """
        """
        ok_(False)


    def mptest_puts_changed_valid_line_item(self):
        """
        """
        ok_(False)


    def mptest_fails_gracefully_invalid_line_item(self):
        """
        """
        ok_(False)


    def mptest_complete_onboarding_after_first_campaign(self):
        """
        """
        ok_(False)


    def mptest_redirects_properly_after_success(self):
        """
        """
        ok_(False)


    def mptest_datetime_alias_for_jquery_on_fail(self):
        """
        """
        ok_(False)


class AdSourceChangeTestCase(OrderViewTestCase):
    def setUp(self):
        super(AdSourceChangeTestCase, self).setUp()
        self.url = reverse('advertiser_ad_source_status_change')

    def mptest_http_response_code(self):
        """
        A valid post should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        response = self.client.post(self.url)
        ok_(response.status_code in [200, 302])

    def mptest_fails_on_missing_params(self):
        """
        Author: John Pena
        The ad source status change handler should return success: false
        if required parameters (ad_sources, status) are missing.
        """
        # test without params
        response = self.client.post(self.url)
        response_json = json.loads(response.content)
        eq_(response_json['success'], False)

        # test without the ad_sources param
        response = self.client.post(self.url, {
            'status': 'boomslam'
        })
        response_json = json.loads(response.content)
        eq_(response_json['success'], False)

        # test without the status param
        response = self.client.post(self.url, {
            'ad_sources[]': ['abcd']
        })
        response_json = json.loads(response.content)
        eq_(response_json['success'], False)

    def mptest_fail_on_unowned_objects(self):
        """
        Author: John Pena
        Users should not be able to change the status of objects
        they don't own. The view should return a 404.
        """
        ok_(False)

    def mptest_creative_run(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set a creative as running
        when 'run' is passed as the status.
        """
        self.creative.active = False
        CreativeQueryManager.put(self.creative)
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.creative.key()),
            'status': 'run'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.creative = CreativeQueryManager.get(self.creative.key())
        eq_(self.creative.active, True)

    def mptest_creative_pause(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set a creative as paused
        when 'pause' is passed as the status.
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.creative.key()),
            'status': 'pause'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.creative = CreativeQueryManager.get(self.creative.key())
        eq_(self.creative.active, False)

    def mptest_creative_delete(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set a creative as deleted
        when 'delete' is passed as the status.
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.creative.key()),
            'status': 'delete'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.creative = CreativeQueryManager.get(self.creative.key())
        eq_(self.creative.deleted, True)
        eq_(self.creative.active, False)

    def mptest_line_item_run(self):
        """
        Author: John Pena
        The ad source status change handler should set a line item as running
        when 'run' is passed as the status.
        """
        # Set the line item as paused
        self.line_item.active = False
        self.line_item.archived = False
        self.line_item.deleted = False

        AdGroupQueryManager.put(self.line_item)
        response = self.client.post(self.url, {
            'ad_sources[]': [unicode(self.line_item.key())],
            'status': 'run'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        ok_(actual_line_item.active)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, False)

    def mptest_line_item_pause(self):
        """
        Author: John Pena
        The ad source status change handler should set a line item as paused
        when 'pause' is passed as the status.
        """
        AdGroupQueryManager.put(self.line_item)
        response = self.client.post(self.url, {
            'ad_sources[]': [unicode(self.line_item.key())],
            'status': 'pause'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, False)

    def mptest_line_item_archive(self):
        """
        Author: John Pena
        The ad source status change handler should set a line item as archived
        when 'archive' is passed as the status.
        """
        AdGroupQueryManager.put(self.line_item)
        response = self.client.post(self.url, {
            'ad_sources[]': [unicode(self.line_item.key())],
            'status': 'archive'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, True)
        eq_(actual_line_item.deleted, False)

    def mptest_line_item_delete(self):
        """
        Author: John Pena
        The ad source status change handler should set a line item as deleted
        when 'delete' is passed as the status.
        """
        AdGroupQueryManager.put(self.line_item)
        response = self.client.post(self.url, {
            'ad_sources[]': [unicode(self.line_item.key())],
            'status': 'delete'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, True)

    def mp_test_order_run(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set an order as running
        when 'run' is passed as the status. The order's line items should
        not be affected.
        """
        self.order.active = False
        CampaignQueryManager.put(self.order)

        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'run'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.active, True)

        eq_(self.line_item.active, True)

    def mptest_order_pause(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set an order as paused
        when 'pause' is passed as the status. The order's line items should
        not be affected.
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'pause'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.active, False)

        eq_(self.line_item.active, True)

    def mptest_order_archive(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set an order as archived
        when 'archive' is passed as the status. The order's line items should
        not be affected.
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'archive'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.archived, True)

        eq_(self.line_item.archived, False)

    def mptest_order_delete(self):
        """
        Author: Haydn Dufrene
        The ad source status change handler should set an order as deleted
        when 'delete' is passed as the status. The order's line items should
        not be affected.
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'delete'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.deleted, True)
        eq_(self.order.active, False)

        eq_(self.line_item.deleted, False)
        eq_(self.line_item.active, True)

    def mptest_mixed_run(self):
        """
        Author: John Pena
        The ad source status change handler changes multiple objects
        statuses to running when 'run' is passed as the status.
        """
        # Set the line item as paused and put it in the db
        self.line_item.active = False
        self.line_item.archived = False
        self.line_item.deleted = False
        AdGroupQueryManager.put(self.line_item)

        # set the order as paused and put it in the db
        self.order.active = False
        self.order.archived = False
        self.order.deleted = False
        CampaignQueryManager.put(self.order)

        # set the creative as paused and put it in the db
        self.creative.active = False
        self.creative.deleted = False
        CreativeQueryManager.put(self.creative)

        response = self.client.post(self.url, {
            'ad_sources[]': [
                unicode(self.line_item.key()),
                unicode(self.order.key()),
                unicode(self.creative.key()),
            ],
            'status': 'run'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        # Test the line item status
        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, True)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, False)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        eq_(actual_creative.active, True)
        eq_(actual_creative.deleted, False)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        eq_(actual_order.active, True)
        eq_(actual_order.archived, False)
        eq_(actual_order.deleted, False)

    def mptest_mixed_pause(self):
        """
        Author: John Pena
        The ad source status change handler changes multiple objects
        statuses to paused when 'pause' is passed as the status.
        """

        AdGroupQueryManager.put(self.line_item)
        CampaignQueryManager.put(self.order)
        CreativeQueryManager.put(self.creative)

        response = self.client.post(self.url, {
            'ad_sources[]': [
                unicode(self.line_item.key()),
                unicode(self.order.key()),
                unicode(self.creative.key()),
            ],
            'status': 'pause'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        # Test the line item status
        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, False)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        eq_(actual_creative.active, False)
        eq_(actual_creative.deleted, False)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        eq_(actual_order.active, False)
        eq_(actual_order.archived, False)
        eq_(actual_order.deleted, False)

    def mptest_mixed_archive(self):
        """
        Author: John Pena
        The ad source status change handler changes multiple objects
        statuses to archived when 'archive' is passed as the status.
        """
        AdGroupQueryManager.put(self.line_item)
        CampaignQueryManager.put(self.order)
        CreativeQueryManager.put(self.creative)

        response = self.client.post(self.url, {
            'ad_sources[]': [
                unicode(self.line_item.key()),
                unicode(self.order.key()),
                unicode(self.creative.key()),
            ],
            'status': 'archive'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        # Test the line item status
        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, True)
        eq_(actual_line_item.deleted, False)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        eq_(actual_creative.active, False)
        eq_(actual_creative.deleted, False)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        eq_(actual_order.active, False)
        eq_(actual_order.archived, True)
        eq_(actual_order.deleted, False)

    def mptest_mixed_delete(self):
        """
        Author: John Pena
        The ad source status change handler changes multiple objects
        statuses to deleted when 'delete' is passed as the status.
        """
        AdGroupQueryManager.put(self.line_item)
        CampaignQueryManager.put(self.order)
        CreativeQueryManager.put(self.creative)

        response = self.client.post(self.url, {
            'ad_sources[]': [
                unicode(self.line_item.key()),
                unicode(self.order.key()),
                unicode(self.creative.key()),
            ],
            'status': 'delete'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        # Test the line item status
        actual_line_item = AdGroupQueryManager.get(self.line_item.key())
        eq_(actual_line_item.active, False)
        eq_(actual_line_item.archived, False)
        eq_(actual_line_item.deleted, True)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        eq_(actual_creative.active, False)
        eq_(actual_creative.deleted, True)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        eq_(actual_order.active, False)
        eq_(actual_order.archived, False)
        eq_(actual_order.deleted, True)

