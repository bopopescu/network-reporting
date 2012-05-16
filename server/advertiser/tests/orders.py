__doc__="""
Tests for the order and line item views.

Author: Haydn Dufrene and John Pena
"""

# don't remove, necessary to set up the test env
import sys
import os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from common.utils.test.views import BaseViewTestCase
from common.utils.test.test_utils import dict_eq, time_almost_eq

from google.appengine.ext import db

import logging
import simplejson as json
from datetime import datetime, timedelta
from django.core.urlresolvers import reverse

from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_
import uuid

from admin.randomgen import (generate_campaign,
                             generate_adgroup,
                             generate_creative,
                             generate_app,
                             generate_account,
                             generate_marketplace_campaign)

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)

from advertiser.forms import OrderForm, LineItemForm, HtmlCreativeForm
from advertiser.models import (TextAndTileCreative, HtmlCreative,
                               ImageCreative)
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from publisher.models import to_dict
from account.query_managers import AccountQueryManager

setup_test_environment()


class OrderViewTestCase(BaseViewTestCase):
    """
    Base test class for all of our order views.
    """
    def setUp(self):
        super(OrderViewTestCase, self).setUp()

        # Set up some basic items. These can be used for
        # initial objects and for resolving urls.
        self.order = generate_campaign(self.account)
        self.line_item = generate_adgroup(self.order,[],self.account,'gtee')
        # HTML Creative
        self.creative = generate_creative(self.account, self.line_item)

        # A post body for an order form, used for testing
        # form submits that need an order.
        self.order_body = {
            u'ajax': u'true', # common form parameter
            u'order-advertiser': u'Testingco',
            u'order-description': u'',
            u'order-name': u'Test Order'
        }

        # A post body for a line item form, used for testing
        # form submits that need a line item
        self.line_item_body = {
            u'ajax': u'true', # common form parameters
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

        # Combined form post body
        self.post_body = dict(self.order_body, **self.line_item_body)

        # Mock order used for testing forms
        mock_order_form = OrderForm(self.post_body, instance=None, prefix='order')
        self.mock_order = mock_order_form.save()
        self.mock_order.account = self.account

        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        site_keys = [(unicode(adunit.key()), '') for adunit in adunits]


        # Mock line item used for testing forms
        line_item_form = LineItemForm(self.post_body,
                                      instance=None,
                                      site_keys=site_keys)
        self.mock_line_item = line_item_form.save()
        self.mock_line_item.account = self.account
        self.mock_line_item.campaign = self.mock_order


class OrderAndLineItemCreateGetTestCase(OrderViewTestCase):
    """
    Tests for the order and line item create view's GET method.

    Author: Haydn Dufrene
    """
    def setUp(self):
        super(OrderAndLineItemCreateGetTestCase, self).setUp()
        self.url = reverse('advertiser_order_and_line_item_form_new')

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.get(self.url)
        ok_(response.status_code in [200, 302])

    def mptest_get_correct_forms_with_no_keys(self):
        """
        A valid get should return valid form objects when no
        order or line item key is passed to the url.

        Author: Haydn Dufrene
        """
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

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.post(self.url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(response.status_code in [200, 302])

    def mptest_graceful_fail_without_data(self):
        """
        Posting to the form handler should fail if there's no post body.

        Author: John Pena
        """
        response = self.client.post(self.url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        response = self.client.post(self.url)
        eq_(response.status_code, 404)

    def mptest_puts_new_valid_order_and_line_item(self):
        """
        A valid POST with valid order and line item data should
        create new order and line item objects. The line item
        should have a valid budget and valid targeting.

        Catches the redirect for create order and line item post.
        Then we use the line item key to retrieve the line item and
        order created. We check to see if the line_item was created
        and edited within the last minute. We then compare the models
        to the mocks created in the class setup.

        Author: Haydn Dufrene
        """
        response = self.client.post(self.url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        # Get the line item key out of the redirect url and fetch the new
        # line item with the key.
        redirect_url = response_json['redirect']
        line_item_key = get_line_item_key_from_redirect_url(redirect_url)
        line_item = AdGroupQueryManager.get(line_item_key)

        # Tests to see that this line_item was created and modified
        # within the last minute

        time_almost_eq(line_item.t,
                       datetime.utcnow(),
                       timedelta(minutes=1))
        time_almost_eq(line_item.created,
                       datetime.utcnow(),
                       timedelta(minutes=1))

        dict_eq(to_dict(line_item, ignore=['id', 'campaign', 'created', 't']),
                 to_dict(self.mock_line_item, ignore=['id', 'campaign', 'created', 't']))

        order = line_item.campaign
        time_almost_eq(order.created,
                       datetime.utcnow(),
                       timedelta(minutes=1))

        dict_eq(to_dict(order, ignore=['id', 'created']),
                 to_dict(self.mock_order, ignore=['id', 'created']))

    def mptest_order_owns_line_item(self):
        """
        Because we must retrieve the order by line item key in the 
        redirect, this test is implicitly covered in 
        mptest_puts_new_valid_order_and_line_item.

        Author: Haydn Dufrene
        """
        pass

    def mptest_account_owns_order_and_line_item(self):
        """
        The mock which the returned order and line items are 
        compared against contain self.account, this test is 
        implicitly covered in mptest_puts_new_valid_order_and_line_item

        Author: Haydn Dufrene
        """
        pass


class NewOrEditLineItemGetTestCase(OrderViewTestCase):
    """
    Tests for the new/edit line item POST method.
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

        Author: John Pena
        """
        new_response = self.client.get(self.new_url)
        edit_response = self.client.get(self.edit_url)
        ok_(new_response.status_code in [200, 302])
        ok_(edit_response.status_code in [200, 302])

    def mptest_get_correct_forms_with_order(self):
        """
        The proper order form is returned with an empty line_item
        form for creating new line_items with an order

        Author: Haydn Dufrene
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

        Author: Haydn Dufrene
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

        Author: Haydn Dufrene
        """
        response = self.client.get(self.edit_url)
        eq_(response.context['order'],
            response.context['line_item'].campaign)

    def mptest_models_do_not_change(self):
        """
        GETs should never change the state of models

        Author: Haydn Dufrene
        """
        response = self.client.get(self.edit_url)
        actual_order = response.context['order']
        actual_line_item = response.context['line_item']
        dict_eq(to_dict(self.order), to_dict(actual_order))
        dict_eq(to_dict(self.line_item), to_dict(actual_line_item))

    def mptest_fail_on_unowned_order(self):
        """
        Trying to access an unowned order returns a 404

        Author: John Pena
        """
        diff_acct = generate_account(username='slamboomington@c.com')
        diff_order = generate_campaign(account=diff_acct)
        diff_url = reverse('advertiser_line_item_form_new', kwargs={
            'order_key':unicode(diff_order.key())
        })

        response = self.client.get(diff_url)
        eq_(response.status_code, 404)

    def mptest_fail_on_editing_unowned_line_item(self):
        """
        Trying to access and access an unowned line_item returns a 404

        Author: John Pena
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
        All apps for the given account should be returned.
        This test will fail if actual apps are not alphabetized in the view.

        Author: Haydn Dufrene
        """
        app1 = generate_app(self.account)
        app2 = generate_app(self.account)
        response = self.client.get(self.edit_url)

        expected_apps = AppQueryManager.get_apps(account=self.account,
                                        alphabetize=True)
        actual_apps = response.context['apps']

        eq_(len(actual_apps), len(expected_apps))
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

        Author: John Pena
        """
        response = self.client.post(self.new_url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

        response = self.client.post(self.edit_url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)


    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        response = self.client.post(self.new_url)
        eq_(response.status_code, 404)

        response = self.client.post(self.edit_url)
        eq_(response.status_code, 404)


    def mptest_graceful_fail_for_non_order(self):
        """
        Posting to the edit form handler with a non-order campaign (marketplace
        or network) should fail gracefully.

        Author: John Pena
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

        Author: John Pena
        """
        diff_account = generate_account(username='diff')
        order = generate_campaign(diff_account)
        line_item = generate_adgroup(order, [], diff_account, 'gtee')
        url = reverse('advertiser_line_item_form_edit', kwargs = {
            'line_item_key': unicode(line_item.key())
        })

        response = self.client.post(url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(response.status_code, 404)


    def mptest_puts_new_valid_line_item(self):
        """
        Posting valid line item data should result in a new line item being
        created on the order that was referenced in the URL.

        Author: John Pena
        """
        order = generate_campaign(self.account)
        url = reverse('advertiser_line_item_form_new', kwargs = {
            'order_key': unicode(order.key())
        })

        new_line_item_name = u'New really awesome lineitem' + unicode(uuid.uuid4())

        post_body = self.post_body
        post_body['name'] = new_line_item_name

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

        expected_line_item_dict = to_dict(self.mock_line_item,
                                          ignore=['id', 'campaign', 'created', 't'])
        actual_line_item_dict = to_dict(line_item,
                                        ignore=['id', 'campaign', 'created', 't'])

        expected_line_item_dict['name'] = new_line_item_name
        dict_eq(expected_line_item_dict, actual_line_item_dict)

    def mptest_puts_changed_valid_line_item(self):
        """
        Posting valid line item information should update the line item
        in the database.
        Author: John Pena
        """
        AdGroupQueryManager.put(self.mock_line_item)
        url = reverse('advertiser_line_item_form_edit', kwargs = {
            'line_item_key': unicode(self.mock_line_item.key())
        })

        # update the name for the post body
        new_name = 'new new name yeah'
        post_body = self.post_body
        post_body['name'] = new_name

        response = self.client.post(url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        line_item = AdGroupQueryManager.get(self.mock_line_item.key())

        eq_(line_item.name, new_name)

    def mptest_fails_gracefully_invalid_line_item(self):
        """
        Posting invalid line item information should not result
        in the line item being changed in the database.

        Author: John Pena
        """
        line_item = generate_adgroup(self.order,
                                     [],
                                     self.account,
                                     'gtee')
        url = reverse('advertiser_line_item_form_edit', kwargs = {
            'line_item_key': unicode(line_item.key())
        })

        post_body = self.post_body
        post_body['name'] = ''

        response = self.client.post(url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        ok_(not response_json['success'])


    def mptest_complete_onboarding_after_first_campaign(self):
        """
        Sets the accounts status to Step 4. If a campaign is 
        created while the account's 'status' == 'step4', 
        the onboarding is complete and status becomes ''.

        Author: Haydn Dufrene
        """
        self.account.status = 'step4'
        AccountQueryManager.put_accounts(self.account)

        response = self.client.post(self.new_url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        acct = AccountQueryManager.get(self.account.key())
        eq_(acct.status, '')

    # TODO
    def mptest_datetime_alias_for_jquery_on_fail(self):
        """
        There is a block at the end of the post (L:351-359)
        that is a hack for JQuery validation. Unsure what 
        it is doing and what to test for.

        Author: Haydn Dufrene
        """
        pass


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
        The ad source status change handler should return success: false
        if required parameters (ad_sources, status) are missing.
        
        Author: John Pena        
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

    # TODO
    def mptest_fail_on_unowned_objects(self):
        """
        Users should not be able to change the status of objects
        they don't own. The view should return a 404.

        Author: John Pena
        """
        pass

    def mptest_creative_run(self):
        """
        The ad source status change handler should set a creative as running
        when 'run' is passed as the status.

        Author: Haydn Dufrene
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
        The ad source status change handler should set a creative as paused
        when 'pause' is passed as the status.

        Author: Haydn Dufrene
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
        The ad source status change handler should set a creative as deleted
        when 'delete' is passed as the status.
        
        Author: Haydn Dufrene
        """
        response = self.client.post(self.url, data={
            "ad_sources[]": unicode(self.creative.key()),
            "status": "delete"
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.creative = CreativeQueryManager.get(self.creative.key())
        ok_(self.creative.deleted)
        ok_(not self.creative.active)

    def mptest_line_item_run(self):
        """
        The ad source status change handler should set a line item as running
        when 'run' is passed as the status.

        Author: John Pena
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
        The ad source status change handler should set a line item as paused
        when 'pause' is passed as the status.
        Author: John Pena
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
        The ad source status change handler should set a line item as deleted
        when 'delete' is passed as the status.
        Author: John Pena
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
        The ad source status change handler should set an order as running
        when 'run' is passed as the status. The order's line items should
        not be affected.
        
        Author: Haydn Dufrene
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

        self.line_item = AdGroupQueryManager.get(self.line_item.key())
        ok_(self.line_item.active)

    def mptest_order_pause(self):
        """
        The ad source status change handler should set an order as paused
        when 'pause' is passed as the status. The order's line items should
        not be affected.
        
        Author: Haydn Dufrene
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'pause'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        ok_(not self.order.active)

        self.line_item = AdGroupQueryManager.get(self.line_item.key())
        ok_(self.line_item.active)

    def mptest_order_archive(self):
        """
        The ad source status change handler should set an order as archived
        when 'archive' is passed as the status. The order's line items should
        not be affected.
        
        Author: Haydn Dufrene
        """
        response = self.client.post(self.url, data={
            'ad_sources[]': unicode(self.order.key()),
            'status': 'archive'
        })

        response_json = json.loads(response.content)
        ok_(response_json['success'])

        self.order = CampaignQueryManager.get(self.order.key())
        ok_(self.order.archived)

        self.line_item = AdGroupQueryManager.get(self.line_item.key())
        ok_(not self.line_item.archived)

    def mptest_order_delete(self):
        """
        The ad source status change handler should set an order as deleted
        when 'delete' is passed as the status. The order's line items should
        not be affected.
        
        Author: Haydn Dufrene
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

        self.line_item = AdGroupQueryManager.get(self.line_item.key())
        ok_(not self.line_item.deleted)
        ok_(self.line_item.active)

    def mptest_mixed_run(self):
        """
        The ad source status change handler changes multiple objects
        statuses to running when 'run' is passed as the status.
        
        Author: John Pena
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
        The ad source status change handler changes multiple objects
        statuses to paused when 'pause' is passed as the status.
        Author: John Pena
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
        The ad source status change handler changes multiple objects
        statuses to archived when 'archive' is passed as the status.
        Author: John Pena
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
        The ad source status change handler changes multiple objects
        statuses to deleted when 'delete' is passed as the status.
        Author: John Pena
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


class NewOrEditCreativeViewTestCase(OrderViewTestCase):

    def setUp(self):
        super(NewOrEditCreativeViewTestCase, self).setUp()
        self.new_url = reverse('advertiser_creative_form_new', kwargs={
            'line_item_key': unicode(self.line_item.key())
        })
        self.edit_url = reverse('advertiser_creative_form_edit', kwargs={
            'creative_key': unicode(self.creative.key())
        })

        self.default_creative_post_body = {
            u'action_icon': u'download_arrow4',
            u'ad_type': u'html',
            u'color': u'000000',
            u'conv_appid': u'',
            u'custom_height': u'',
            u'custom_width': u'',
            u'font_color': u'FFFFFF',
            u'format': u'320x50',
            u'gradient': u'on',
            u'html_data': u'',
            u'launchpage': u'',
            u'line1': u'',
            u'line2': u'',
            u'name': u'Creative',
            u'tracking_url': u'',
            u'url': u'',
        }

        # We need this to get the absolute path to image files
        # we'll use for testing uploads
        pwd = os.path.dirname(os.path.abspath(__file__))

        # Post bodies for the different types of creatives
        self.html_creative_post_body = self.default_creative_post_body
        self.image_creative_post_body = self.default_creative_post_body
        self.text_tile_creative_post_body = self.default_creative_post_body

        self.html_creative_post_body.update({
            u'ad_type': u'html',
            u'html_data': u'<div> An Ad </div>',
            u'name': u'HTML Creative',
        })

        test_banner_path = os.path.join(pwd, 'test_banner.gif')
        self.image_creative_post_body.update({
            u'ad_type': u'image',
            u'name': u'Image Creative',
            'image_file': open(test_banner_path, 'rb')
        })

        test_tile_path = os.path.join(pwd, 'test_tile.png')
        self.text_tile_creative_post_body.update({
            'image_file': open(test_tile_path, 'rb')
        })

        mock_creative_form = HtmlCreativeForm(self.html_creative_post_body,
                                              instance=None)
        self.mock_creative = mock_creative_form.save()
        self.mock_creative.account = self.account
        self.mock_creative.ad_group = self.line_item

    def mptest_http_response_code(self):
        """
        A valid post should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        new_response = self.client.post(self.new_url, self.creative_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(new_response.status_code in [200, 302])

        edit_response = self.client.post(self.edit_url, self.creative_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(edit_response.status_code in [200, 302])


    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        self.creative_body.pop('ajax')

        new_response = self.client.post(self.new_url, self.creative_body)
        eq_(new_response.status_code, 404)

        edit_response = self.client.post(self.edit_url, self.creative_body)
        eq_(edit_response.status_code, 404)

    def mptest_ensure_proper_redirect(self):
        new_response = self.client.post(self.new_url, self.html_creative_post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        edit_response = self.client.post(self.edit_url, self.html_creative_post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        new_response_json = json.loads(new_response.content)
        edit_response_json = json.loads(edit_response.content)

        ok_(new_response_json['success'])
        ok_(edit_response_json['success'])

        new_redirect_url = new_response_json['redirect']
        edit_redirect_url = edit_response_json['redirect']

        new_redirect_split = new_redirect_url.split('/')
        edit_redirect_split = edit_redirect_url.split('/')

        eq_(new_redirect_split[1], 'advertise')
        eq_(edit_redirect_split[1], 'advertise')

        eq_(new_redirect_split[2], 'line_items')
        eq_(edit_redirect_split[2], 'line_items')

        # These will fail loudly if a valid key is not returned
        db.Key(new_redirect_split[3])
        db.Key(edit_redirect_split[3])

    def mptest_puts_valid_new_creative(self):
        response = self.client.post(self.new_url, self.creative_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives

        # There is also a randomly generated creative attached
        # to self.line_item in module setUp
        eq_(creatives.count(), 2)

        creative = creatives.filter('name =', 'Test Creative').fetch(1)[0]
        dict_eq(to_dict(creative), 
                to_dict(self.mock_creative), exclude=['id'])

    def mptest_puts_valid_edited_creative(self):
        response = self.client.post(self.edit_url, self.creative_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives

        # self.creative
        eq_(creatives.count(), 1)

        creative = creatives[0]

        updated_creative_form = HtmlCreativeForm(self.creative_body,
                                                 instance=self.creative)
        updated_creative = updated_creative_form.save()

        dict_eq(to_dict(creative), 
                to_dict(updated_creative), exclude=['id'])

    def mptest_uses_correct_form_for_image(self):
        response = self.client.post(self.edit_url, 
                                    self.image_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives
        creative = creatives[0]
        ok_(isinstance(creative, ImageCreative))

    def mptest_uses_correct_form_for_text_icon(self):
        response = self.client.post(self.edit_url, 
                                    self.text_tile_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives
        creative = creatives[0]
        ok_(isinstance(creative, TextAndTileCreative))


    def mptest_uses_correct_form_for_html(self):
        response = self.client.post(self.edit_url, 
                                    self.html_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives
        creative = creatives[0]
        ok_(isinstance(creative, HtmlCreative))


    def mptest_fails_with_unsupported_ad_type(self):
        pass

#^ haydn
##############################
#v pena

    def mptest_line_item_owns_creative(self):
        past_creatives = CreativeQueryManager.get_creatives(adgroup=self.line_item)
        self.client.post(self.new_url, self.html_creative_post_body)
        current_creatives = CreativeQueryManager.get_creatives(adgroup=self.line_item)
        eq_(len(current_creatives), (len(past_creatives) + 1))

    def mptest_account_owns_creative(self):
        pass

    def mptest_fails_gracefully_with_form_errors(self):
        pass

    def mptest_fails_when_creative_is_unowned(self):
        pass

    def mptest_fails_when_line_item_is_unowned(self):
        pass


def get_line_item_key_from_redirect_url(redirect_url):
    """
    Helper method for getting a line item key from the redirect
    url that's passed back in many post views.
    """
    return redirect_url.replace('/advertise/line_items/', '').rstrip('/')

def get_image_upload_body(file_path):
    f = open(file_path, 'rb')
    return {'image_file': f}
