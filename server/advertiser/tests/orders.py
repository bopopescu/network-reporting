# don't remove, necessary to set up the test env
import sys
import os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from common.utils.test.views import BaseViewTestCase
from common.utils.test.test_utils import dict_eq

import logging
import simplejson as json
import time
from datetime import datetime
from django.core.urlresolvers import reverse

from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_
import uuid

from admin.randomgen import (generate_campaign, generate_adgroup, \
                             generate_creative, generate_app, \
                             generate_account, generate_marketplace_campaign)

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)
from advertiser.forms import OrderForm, LineItemForm
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from publisher.models import to_dict

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


class OrderAndLineItemCreateGetTestCase(OrderViewTestCase):
    def setUp(self):
        super(OrderAndLineItemCreateGetTestCase, self).setUp()
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
        ok_(response.context['order_form'].instance is None)
        ok_(response.context['line_item_form'].instance is None)


class OrderAndLineItemCreatePostTestCase(OrderViewTestCase):
    """
    Tests the post for creating a new order and line item
    Author: Haydn Dufrene
    """
    def setUp(self):
        """
        Set up the URL, post_body and creates mock models
        to compare to the models put in the DB by the view
        """
        super(OrderAndLineItemCreatePostTestCase, self).setUp()
        self.url = reverse('advertiser_order_and_line_item_form_new')
        self.order_body = {
                          # common form parameters
                          u'ajax': u'true',
                          # order form parameters
                          u'order-advertiser': u'Testingco',
                          u'order-description': u'',
                          u'order-name': u'Test Order'
                          }
        self.line_item_body = {
                          # common form parameters
                          u'ajax': u'true',
                          # line item form parameters
                          u'adgroup_type': u'gtee',
                          u'allocation_percentage': u'100.0',
                          u'android_version_max': u'999',
                          u'android_version_min': u'1.5',
                          u'bid': u'0.05',
                          u'bid_strategy': u'cpm',
                          u'budget': u'',
                          u'budget_strategy': u'allatonce',
                          u'budget_type': u'daily',
                          u'daily_frequency_cap': u'0',
                          u'device_targeting': u'0',
                          u'end_datetime_0': u'05/31/2012',
                          u'end_datetime_1': u'11:59 PM',
                          u'geo_predicates': [u'US'],
                          u'gtee_priority': u'normal',
                          u'hourly_frequency_cap': u'0',
                          u'ios_version_max': u'999',
                          u'ios_version_min': u'2.0',
                          u'keywords': u'',
                          u'name': u'Test Line Item',
                          u'promo_priority': u'normal',
                          u'region_targeting': u'all',
                          u'start_datetime_0': u'05/30/2012',
                          u'start_datetime_1': u'12:00 AM',
                          u'target_android': u'on',
                          u'target_ipad': u'on',
                          u'target_iphone': u'on',
                          u'target_ipod': u'on',
                          u'target_other': u'on'
        }
        self.post_body = dict(self.order_body, **self.line_item_body)
        mock_order_form = OrderForm(self.post_body, instance=None, prefix='order')
        self.mock_order = mock_order_form.save()
        self.mock_order.account = self.account
        self.mock_order.save()

        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        site_keys = [(unicode(adunit.key()), '') for adunit in adunits]


        line_item_form = LineItemForm(self.post_body, 
                                      instance=None, site_keys=site_keys)
        self.mock_line_item = line_item_form.save()
        self.mock_line_item.account = self.account
        self.mock_line_item.campaign = self.mock_order

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        response = self.client.post(self.url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(response.status_code in [200, 302])

    def mptest_graceful_fail_without_data(self):
        """
        Posting to the form handler should fail if there's no post body.
        """
        response = self.client.post(self.url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.
        """
        response = self.client.post(self.url)
        eq_(response.status_code, 404)

    def mptest_puts_new_valid_order_and_line_item(self):
        """
        Catches the redirect for create order and line item post.
        Then we use the line item key to retrieve the line item and 
        order created. We check to see if the line_item was created
        and edited within the last minute. We then compare the models
        to the mocks created in the class setup.
        """
        response = self.client.post(self.url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        redirect = response_json['redirect']
        # /advertise/line_items/<LINE_ITEM_KEY>/
        url_split = redirect.split('/')
        eq_(url_split[1:3], ['advertise', 'line_items'])

        line_item_key = url_split[3]
        line_item = AdGroupQueryManager.get(line_item_key)

        # Tests to see that this line_item was created and modified
        # within the last minute
        line_item_dict = to_dict(line_item)
        minute_ago = time.mktime(datetime.now().timetuple())
        ok_(line_item_dict['created'] > minute_ago)
        ok_(line_item_dict['t'] > minute_ago)

        dict_eq(to_dict(line_item, ignore=['id', 'campaign', 'created', 't']),
                 to_dict(self.mock_line_item, ignore=['id', 'campaign', 'created', 't']))

        order = line_item.campaign
        dict_eq(to_dict(order, ignore=['id']),
                 to_dict(self.mock_order, ignore=['id']))

    def mptest_order_owns_line_item(self):
        """
        Because we must retrieve the order by line item key in the 
        redirect, this test is implicitly covered in 
        mptest_puts_new_valid_order_and_line_item
        """
        pass

    def mptest_account_owns_order_and_line_item(self):
        """
        The mock which the returned order and line items are 
        compared against contain self.account, this test is 
        implicitly covered in mptest_puts_new_valid_order_and_line_item
        """
        pass


class NewOrEditLineItemGetTestCase(OrderViewTestCase):
    """
    Tests for the new/edit line item POST method.
    Author: Haydn Dufrene
    """

    def setUp(self):
        """
        Sets up the new and edit urls.
        """
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
        """
        new_response = self.client.get(self.new_url)
        edit_response = self.client.get(self.edit_url)
        ok_(new_response.status_code in [200, 302])
        ok_(edit_response.status_code in [200, 302])

    def mptest_get_correct_forms_with_order(self):
        """
        The proper order form is returned with an empty line_item
        form for creating new line_items with an order
        """
        line_item = None
        order_form = OrderForm(instance=self.order, prefix='order')

        response = self.client.get(self.new_url)
        eq_(response.context['order_form'].instance.key(),
            order_form.instance.key())
        ok_(response.context['line_item_form'].instance is None)

    def mptest_get_correct_forms_with_line_item(self):
        """
        The proper order and line_item forms are returned
        when editing
        """
        order_form = OrderForm(instance=self.order, prefix='order')
        line_item_form = LineItemForm(instance=self.line_item)

        response = self.client.get(self.edit_url)
        eq_(response.context['order_form'].instance.key(),
            order_form.instance.key())
        eq_(response.context['line_item_form'].instance.key(),
            line_item_form.instance.key())

    def mptest_order_owns_line_item(self):
        """
        The order returned must own the line_item returned
        """
        response = self.client.get(self.edit_url)
        eq_(response.context['order'],
            response.context['line_item'].campaign)

    def mptest_models_do_not_change(self):
        """
        GETs should never change the state of models
        """
        response = self.client.get(self.edit_url)
        actual_order = response.context['order']
        actual_line_item = response.context['line_item']
        dict_eq(to_dict(self.order), to_dict(actual_order))
        dict_eq(to_dict(self.line_item), to_dict(actual_line_item))

    def mptest_fail_on_unowned_order(self):
        """
        Trying to access an unowned order returns a 404
        """
        diff_acct = generate_account(username='diff')
        diff_order = generate_campaign(account=diff_acct)
        diff_url = reverse('advertiser_line_item_form_new',
                           kwargs={'order_key':
                                   unicode(diff_order.key())})

        response = self.client.get(diff_url)
        eq_(response.status_code, 404)

    def mptest_fail_on_unowned_line_item(self):
        """
        Trying to access an unowned line_item returns a 404
        """
        diff_acct = generate_account(username='diff')
        diff_order = generate_campaign(account=diff_acct)
        diff_line_item = generate_adgroup(diff_order,
                                          [],
                                          diff_acct,
                                          'gtee')
        diff_url = reverse('advertiser_line_item_form_edit',
                           kwargs={'line_item_key':
                                   unicode(diff_line_item.key())})

        response = self.client.get(diff_url)
        eq_(response.status_code, 404)

    def mptest_gets_correct_apps(self):
        """
        All apps for the given account should be returned
        """
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
        order = generate_campaign(self.account)
        #line_item = generate_adgroup(order, [], diff_account, 'gtee')
        url = reverse('advertiser_line_item_form_new', kwargs = {
            'order_key': unicode(order.key())
        })

        new_line_item_name = u'New really awesome lineitem' + unicode(uuid.uuid4())
        post_body = {

            # common form parameters
            u'ajax': [u'true'],

            # order form parameters
            u'order-advertiser': [order.advertiser],
            u'order-description': [order.description],
            u'order-name': [order.name],

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
            u'name': [new_line_item_name],
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

        # Get the response from the post
        response = self.client.post(url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        # Assert that the form post was a success
        ok_(response_json['success'])

        # Assert that we got a redirect link
        ok_(response_json['redirect'])

        # Get the new line item
        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

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
        ok_(not response_json['success'])

        # test without the ad_sources param
        response = self.client.post(self.url, {
            'status': 'boomslam'
        })
        response_json = json.loads(response.content)
        ok_(not response_json['success'])

        # test without the status param
        response = self.client.post(self.url, {
            'ad_sources[]': ['abcd']
        })
        response_json = json.loads(response.content)
        ok_(not response_json['success'])

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
        ok_(self.creative.active)

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
        ok_(not self.creative.active)

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
        ok_(self.creative.deleted)
        ok_(not self.creative.active)

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
        ok_(not actual_line_item.archived)
        ok_(not actual_line_item.deleted)

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
        ok_(not actual_line_item.active)
        ok_(not actual_line_item.archived)
        ok_(not actual_line_item.deleted)

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
        ok_(not actual_line_item.active)
        ok_(actual_line_item.archived)
        ok_(not actual_line_item.deleted)

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
        ok_(not actual_line_item.active)
        ok_(not actual_line_item.archived)
        ok_(actual_line_item.deleted)

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
        ok_(self.order.active)

        ok_(self.line_item.active)

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
        ok_(not self.order.active)

        ok_(self.line_item.active)

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
        ok_(self.order.archived)

        ok_(not self.line_item.archived)

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
        ok_(self.order.deleted)
        ok_(not self.order.active)

        ok_(not self.line_item.deleted)
        ok_(self.line_item.active)

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
        ok_(actual_line_item.active)
        ok_(not actual_line_item.archived)
        ok_(not actual_line_item.deleted)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        ok_(actual_creative.active)
        ok_(not actual_creative.deleted)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        ok_(actual_order.active)
        ok_(not actual_order.archived)
        ok_(not actual_order.deleted)

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
        ok_(not actual_line_item.active)
        ok_(not actual_line_item.archived)
        ok_(not actual_line_item.deleted)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        ok_(not actual_creative.active)
        ok_(not actual_creative.deleted)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        ok_(not actual_order.active)
        ok_(not actual_order.archived)
        ok_(not actual_order.deleted)

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
        ok_(not actual_line_item.active)
        ok_(actual_line_item.archived)
        ok_(not actual_line_item.deleted)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        ok_(not actual_creative.active)
        ok_(not actual_creative.deleted)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        ok_(not actual_order.active)
        ok_(actual_order.archived)
        ok_(not actual_order.deleted)

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
        ok_(not actual_line_item.active)
        ok_(not actual_line_item.archived)
        ok_(actual_line_item.deleted)

        # Test the creative status
        actual_creative = CreativeQueryManager.get(self.creative.key())
        ok_(not actual_creative.active)
        ok_(actual_creative.deleted)

        # Test the order status
        actual_order = CampaignQueryManager.get(self.order.key())
        ok_(not actual_order.active)
        ok_(not actual_order.archived)
        ok_(actual_order.deleted)


def get_line_item_key_from_redirect_url(redirect_url):
    return redirect_url.replace('/advertise/line_items/', '').rstrip('/')
