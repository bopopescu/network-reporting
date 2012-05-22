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
from common.utils.test.test_utils import dict_eq, time_almost_eq, confirm_db, decorate_all_test_methods

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
                             generate_adunit,
                             generate_account,
                             generate_marketplace_campaign)

from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)

from advertiser.forms import (OrderForm, LineItemForm, NewCreativeForm,
                              HtmlCreativeForm, ImageCreativeForm)
from advertiser.models import (Creative, TextAndTileCreative, 
                               HtmlCreative, ImageCreative, AdGroup, Campaign)
from account.models import Account
from advertiser.views.orders import get_targeted_apps
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
        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.app, self.account)
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


@decorate_all_test_methods(confirm_db())
class OrderIndexTestCase(OrderViewTestCase):
    """
    Tests the order index handler

    Author: Haydn Dufrene
    """
    def setUp(self):
        """
        Sets up the index url
        """
        super(OrderIndexTestCase, self).setUp()
        self.url = reverse('advertiser_order_index')

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)

    def mptest_gets_all_orders(self):
        """
        Checks to see that all orders of a given account are returned
        """
        expected_orders = CampaignQueryManager.get_order_campaigns(account=self.account)
        expected_orders = expected_orders.fetch(1000)

        response = self.client.get(self.url)
        actual_orders = response.context['orders'].fetch(1000)

        eq_(len(actual_orders), len(expected_orders))
        for actual_order, expected_order in zip(actual_orders, expected_orders):
            eq_(actual_order.key(), expected_order.key())


    def mptest_gets_all_line_items(self):
        """
        Checks to see that all line_items of an account are returned
        """
        expected_line_items = AdGroupQueryManager.get_adgroups(account=self.account)

        response = self.client.get(self.url)
        actual_line_items = response.context['line_items']

        eq_(len(actual_line_items), len(expected_line_items))
        for actual_line_item, expected_line_items in zip(actual_line_items, expected_line_items):
            eq_(actual_line_item.key(), expected_line_items.key())


    def mptest_account_owns_all_items(self):
        """
        We query for items by account in the previous two tests
        and therefore this test implicitly passes if they do.

        Author: Haydn Dufrene
        """
        pass

    def mptest_all_orders_returned_are_orders(self):
        response = self.client.get(self.url)
        orders = response.context['orders'].fetch(1000)
        for order in orders:
            ok_(order.is_order)

    def mptest_all_line_items_are_for_orders(self):
        mpx_campaign = generate_marketplace_campaign(self.account, None)
        mpx_adgroup = generate_adgroup(mpx_campaign, [], self.account, 'marketplace')
        response = self.client.get(self.url)
        line_items = response.context['line_items']
        for line_item in line_items:
            ok_(line_item.campaign.is_order)
    
        CampaignQueryManager.delete(mpx_campaign)
        AdGroupQueryManager.delete(mpx_adgroup)

@decorate_all_test_methods(confirm_db())
class OrderDetailHandlerTestCase(OrderViewTestCase):
    def setUp(self):
        super(OrderDetailHandlerTestCase, self).setUp()
        self.url = reverse('advertiser_order_detail', 
                           kwargs={
                                'order_key': unicode(self.order.key())
                           })

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)

    def mptest_fails_on_unowned_order(self):
        self.login_secondary_account()
        response = self.client.get(self.url)
        eq_(response.status_code, 404)

    def mptest_returns_all_targeted_adunits_apps_and_keys(self):
        # Formatted lists properly so they match the view
        flatten = lambda l: [item for sublist in l for item in sublist]
        expected_adunits = set(flatten([AdUnitQueryManager.get(line_item.site_keys) \
                               for line_item in self.order.adgroups]))

        response = self.client.get(self.url)
        actual_adunits = response.context['targeted_adunits']

        eq_(len(actual_adunits), len(expected_adunits))
        for actual_adunit, expected_adunit in zip(actual_adunits, expected_adunits):
            eq_(actual_adunit.key(), expected_adunit.key())

    def mptest_returns_all_targeted_apps_and_keys(self):
        # Formatted lists properly so they match the view
        flatten = lambda l: [item for sublist in l for item in sublist]
        expected_adunits = set(flatten([AdUnitQueryManager.get(line_item.site_keys) \
                               for line_item in self.order.adgroups]))
        expected_apps = get_targeted_apps(expected_adunits)
        expected_app_keys = expected_apps.keys()

        response = self.client.get(self.url)
        actual_adunits = response.context['targeted_adunits']
        actual_apps = response.context['targeted_apps']
        actual_app_keys = response.context['targeted_app_keys']

        eq_(len(actual_adunits), len(expected_adunits))
        for actual_adunit, expected_adunit in zip(actual_adunits, expected_adunits):
            eq_(actual_adunit.key(), expected_adunit.key())

        eq_(len(actual_apps), len(expected_apps))
        for actual_app, expected_app in zip(actual_apps, expected_apps):
            eq_(actual_app.key(), expected_app.key())

        eq_(actual_app_keys, expected_app_keys)

    def mptest_returns_proper_order_form(self):
        expected_order_form = OrderForm(instance=self.order)

        response = self.client.get(self.url)
        actual_order_form = response.context['order_form']

        eq_(expected_order_form.instance.key(), 
            actual_order_form.instance.key())

    def mptest_returns_proper_order(self):
        expected_order = self.order

        response = self.client.get(self.url)
        actual_order = response.context['order']

        eq_(expected_order.key(), actual_order.key())


@decorate_all_test_methods(confirm_db())
class LineItemDetailHandler(OrderViewTestCase):
    def setUp(self):
        super(LineItemDetailHandler, self).setUp()
        self.url = reverse('advertiser_line_item_detail',
                           kwargs={'line_item_key': self.line_item.key()})

    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.get(self.url)
        eq_(response.status_code, 200)

    def mptest_fails_on_unowned_line_item(self):
        self.login_secondary_account()
        response = self.client.get(self.url)
        eq_(response.status_code, 404)

    def mptest_returns_all_targeted_adunits(self):
        expected_adunits = AdUnitQueryManager.get(self.line_item.site_keys)

        response = self.client.get(self.url)
        actual_adunits = response.context['targeted_adunits']

        eq_(len(actual_adunits), len(expected_adunits))
        for actual_adunit, expected_adunit in zip(actual_adunits, expected_adunits):
            eq_(actual_adunit.key(), expected_adunit.key())


    def mptest_returns_all_targeted_apps_and_keys(self):
        expected_adunits = AdUnitQueryManager.get(self.line_item.site_keys)
        expected_apps = get_targeted_apps(expected_adunits)
        expected_app_keys = expected_apps.keys()

        response = self.client.get(self.url)
        actual_apps = response.context['targeted_apps']
        actual_app_keys = response.context['targeted_app_keys']

        eq_(len(actual_apps), len(expected_apps))
        for actual_app, expected_app in zip(actual_apps, expected_apps):
            eq_(actual_app.key(), expected_app.key())

        eq_(actual_app_keys, expected_app_keys)

    def mptest_returns_new_creative_form(self):
        response = self.client.get(self.url)
        creative_form = response.context['creative_form']
        ok_(isinstance(creative_form, NewCreativeForm))
        ok_(creative_form.instance is None)

    def mptest_returns_proper_line_item(self):
        expected_line_item = self.line_item

        response = self.client.get(self.url)
        actual_line_item = response.context['line_item']

        eq_(expected_line_item.key(),
            actual_line_item.key())

    def mptest_returns_order_which_owns_line_item(self):
        expected_order = self.order

        response = self.client.get(self.url)
        actual_line_item = response.context['line_item']
        actual_order = response.context['order']

        eq_(actual_line_item.campaign.key(), actual_order.key())
        eq_(actual_order.key(), expected_order.key())


@decorate_all_test_methods(confirm_db())
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

    @confirm_db(modified=[AdGroup, Campaign])
    def mptest_http_response_code(self):
        """
        A valid get should return a valid (200, 302) response (regardless
        of params).
        """
        response = self.client.post(self.url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(response.status_code in [200, 302])

    @confirm_db()
    def mptest_graceful_fail_without_data(self):
        """
        Posting to the form handler should fail if there's no post body.

        Author: John Pena
        """
        response = self.client.post(self.url,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

    @confirm_db()
    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        response = self.client.post(self.url)
        eq_(response.status_code, 404)

    @confirm_db(modified=[AdGroup, Campaign])
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


@decorate_all_test_methods(confirm_db())
class NewOrEditLineItemGetTestCase(OrderViewTestCase):
    """
    Tests for the new/edit line item GET method.
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
        self.client.login_secondary_account()

        response = self.client.get(self.new_url)
        eq_(response.status_code, 404)


    def mptest_fail_on_editing_unowned_line_item(self):
        """
        Trying to access and access an unowned line_item returns a 404

        Author: John Pena
        """
        self.client.login_secondary_account()
        
        response = self.client.get(self.edit_url)
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

        AppQueryManager.delete(app1)
        AppQueryManager.delete(app2)


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

    @confirm_db()
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

    @confirm_db()
    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        response = self.client.post(self.new_url)
        eq_(response.status_code, 404)

        response = self.client.post(self.edit_url)
        eq_(response.status_code, 404)

    @confirm_db()
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

        CampaignQueryManager.delete(non_order_mpx)
        CampaignQueryManager.delete(non_order_network)

    @confirm_db()
    def mptest_fail_when_line_item_not_owned(self):
        """
        A line item should not be editable by accounts that don't
        own it.

        Author: John Pena
        """
        self.client.login_secondary_account()

        response = self.client.post(self.edit_url, self.post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        eq_(response.status_code, 404)

    @confirm_db(modified=[AdGroup])
    def mptest_puts_new_valid_line_item(self):
        """
        Posting valid line item data should result in a new line item being
        created on the order that was referenced in the URL.

        Author: John Pena
        """
        new_line_item_name = u'New really awesome lineitem' + unicode(uuid.uuid4())

        post_body = self.post_body
        post_body['name'] = new_line_item_name

        # Get the response from the post
        response = self.client.post(self.new_url, post_body,
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

    @confirm_db(modified=[AdGroup])
    def mptest_puts_changed_valid_line_item(self):
        """
        Posting valid line item information should update the line item
        in the database.
        
        Author: John Pena
        """
        # update the name for the post body
        new_name = 'new new name yeah'
        post_body = self.post_body
        post_body['name'] = new_name

        response = self.client.post(self.edit_url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        line_item = AdGroupQueryManager.get(self.line_item.key())

        eq_(line_item.name, new_name)

    @confirm_db()
    def mptest_fails_gracefully_invalid_line_item(self):
        """
        Posting invalid line item information should not result
        in the line item being changed in the database.

        Author: John Pena
        """
        post_body = self.post_body
        post_body['name'] = ''

        response = self.client.post(self.edit_url, post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        ok_(not response_json['success'])

    @confirm_db(modified=[Account, Campaign, AdGroup])
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
    @confirm_db()
    def mptest_datetime_alias_for_jquery_on_fail(self):
        """
        There is a block at the end of the post (L:351-359)
        that is a hack for JQuery validation. Unsure what 
        it is doing and what to test for.

        Author: Haydn Dufrene
        """
        pass

#TODO: Change this if confirm_db actually checks the models, rather than count
@decorate_all_test_methods(confirm_db())
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


@decorate_all_test_methods(confirm_db())
class DisplayCreativeHandlerTestCase(OrderViewTestCase):
    def setUp(self):
        super(DisplayCreativeHandlerTestCase, self).setUp()
        self.url = ''

    def mptest_http_response_code(self):
        pass

    def mptest_fails_on_unowned_creative(self):
        pass

    def mptest_returns_empty_for_mraid(self):
        pass

    def mptest_fails_with_non_creative_key(self):
        pass

    def mptest_returns_html_for_image_creative(self):
        pass

    def mptest_returns_html_for_text_tile(self):
        pass

    def mptest_returns_html_for_html(self):
        pass


@decorate_all_test_methods(confirm_db())
class CreativeImageHandlerTestCase(OrderViewTestCase):
    def setUp(self):
        super(CreativeImageHandlerTestCase, self).setUp()
        self.url = ''

    def mptest_http_response_code(self):
        pass

    def mptest_fails_on_unowned_creative(self):
        pass

    def mptest_fails_with_non_creative_key(self):
        pass

    def mptest_returns_proper_response(self):
        pass

    def mptest_raise_404_for_non_image_creatives(self):
        pass


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
            u'ajax': u'true',
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
        self.html_creative_post_body = self.default_creative_post_body.copy()
        self.image_creative_post_body = self.default_creative_post_body.copy()
        self.text_tile_creative_post_body = self.default_creative_post_body.copy()

        self.html_creative_post_body.update({
            u'html_data': u'<div> An Ad </div>',
            u'name': u'HTML Creative',
        })

        self.test_banner_path = os.path.join(pwd, 'test_banner.gif')
        self.image_creative_post_body.update({
            u'ad_type': u'image',
            u'name': u'Image Creative',
            u'image_file': open(self.test_banner_path, 'rb')
        })

        test_tile_path = os.path.join(pwd, 'test_tile.png')
        self.text_tile_creative_post_body.update({
            u'ad_type': u'text_icon',
            u'image_file': open(test_tile_path, 'rb')
        })

        mock_creative_form = HtmlCreativeForm(self.html_creative_post_body,
                                              instance=None)
        self.mock_creative = mock_creative_form.save()
        self.mock_creative.account = self.account
        self.mock_creative.ad_group = self.line_item

    @confirm_db(modified=[Creative])
    def mptest_http_response_code(self):
        """
        A valid post should return a valid (200, 302) response (regardless
        of params).

        Author: Haydn Dufrene
        """
        new_response = self.client.post(self.new_url, self.html_creative_post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(new_response.status_code in [200, 302])

        edit_response = self.client.post(self.edit_url, self.html_creative_post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        ok_(edit_response.status_code in [200, 302])

    @confirm_db()
    def mptest_graceful_fail_without_ajax(self):
        """
        Non-AJAX (i.e. non-XHR's) POST requests should fail gracefully.

        Author: John Pena
        """
        self.html_creative_post_body.pop('ajax')

        new_response = self.client.post(self.new_url, self.html_creative_post_body)
        eq_(new_response.status_code, 404)

        edit_response = self.client.post(self.edit_url, self.html_creative_post_body)
        eq_(edit_response.status_code, 404)

    @confirm_db(modified=[Creative])
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

    @confirm_db(modified=[Creative])
    def mptest_puts_valid_new_creative(self):
        response = self.client.post(self.new_url, self.html_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives

        # There is also a randomly generated creative attached
        # to self.line_item in module setUp
        eq_(creatives.count(), 2)

        creative = creatives.filter('name =', self.html_creative_post_body['name']).fetch(1)[0]
        dict_eq(to_dict(creative), 
                to_dict(self.mock_creative), exclude=['id'])

    @confirm_db(modified=[Creative])
    def mptest_puts_valid_edited_creative(self):
        response = self.client.post(self.edit_url, self.html_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        response_json = json.loads(response.content)

        line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
        line_item = AdGroupQueryManager.get(line_item_key)

        creatives = line_item.creatives

        # self.creative
        eq_(creatives.count(), 1)

        creative = creatives[0]

        updated_creative_form = HtmlCreativeForm(self.html_creative_post_body,
                                                 instance=self.creative)
        updated_creative = updated_creative_form.save()

        dict_eq(to_dict(creative), 
                to_dict(updated_creative), exclude=['id'])

    @confirm_db(modified=[Creative])
    def mptest_uses_correct_form_for_html(self):
        ad_type_dict = {
                        'html': self.html_creative_post_body,
                        'image': self.image_creative_post_body,
                        'text_icon': self.text_tile_creative_post_body
                        }
        for ad_type, post_body in ad_type_dict.iteritems():
            response = self.client.post(self.new_url, post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
            response_json = json.loads(response.content)

            line_item_key = get_line_item_key_from_redirect_url(response_json['redirect'])
            line_item = AdGroupQueryManager.get(line_item_key)

            creatives = line_item.creatives.filter('name =', post_body['name']).fetch(1)
            creative = creatives[0]
            eq_(creative.ad_type, ad_type)

    # TODO: Make a mopub exception to catch, so we dont have to hardcode
    #       error messages into tests?
    @confirm_db()
    def mptest_fails_with_unsupported_ad_type(self):
        self.html_creative_post_body.update({u'ad_type': u'fake_ad_type'})
        try:
            response = self.client.post(self.new_url,
                                        self.html_creative_post_body,
                                        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        except Exception, e:
            eq_(e.message, 'Unsupported creative type fake_ad_type.')

    @confirm_db(modified=[Creative])
    def mptest_line_item_owns_creative(self):
        """
        Check that when a new creative is made, it's owned by the line
        item we referenced in the post url.

        Author: John Pena
        """
        # look at the past creatives for this line item. after we post,
        # the length of this list should be +1
        past_creatives = CreativeQueryManager.get_creatives(adgroup=self.line_item)
        self.client.post(self.new_url, self.html_creative_post_body,
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        current_creatives = CreativeQueryManager.get_creatives(adgroup=self.line_item)
        eq_(len(current_creatives), (len(past_creatives) + 1))

    @confirm_db(modified=[Creative])
    def mptest_account_owns_creative(self):
        """
        Check that when a new creative is made, it's owned by the
        account that's logged in.

        Author: John Pena
        """
        # make a super unique name and update the post body with the name
        new_name = 'my super awesome creative ' + unicode(uuid.uuid4())
        new_creative_body = self.html_creative_post_body
        new_creative_body['name'] = new_name

        # post the new creative
        self.client.post(self.new_url, new_creative_body,
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # find the new creative based on its super unique name.
        # make sure there's only one.
        new_creatives = Creative.all().filter("name = ", new_name).fetch(1000)
        eq_(len(new_creatives), 1)
        new_creative = new_creatives[0]

        # make sure its owned by the current account
        eq_(unicode(new_creative.account.key()), unicode(self.account.key()))

    @confirm_db()
    def mptest_fails_gracefully_with_form_errors(self):
        """
        Check that when invalid form data is posted, a valid (status
        200) JSON response is returned, which includes success=False and
        a list of errors.

        Author: John Pena
        """
        # make some invalid data
        invalid_creative_body = self.image_creative_post_body
        invalid_creative_body['image_file'] = None

        # post the new creative and make sure the response is valid
        response = self.client.post(self.new_url, invalid_creative_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 200)

        # look at the response data and make sure its listed as having failed
        # and includes errors
        response_json = json.loads(response.content)
        ok_(not response_json['success'])
        dict_eq(response_json['errors'],
                {u'image_file': 
                 u'You must upload an image file for a creative of this type.'})
    
    @confirm_db()
    def mptest_fails_when_creative_is_unowned(self):
        self.login_secondary_account()
        response = self.client.post(self.edit_url, self.html_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)

    @confirm_db()
    def mptest_fails_when_line_item_is_unowned(self):
        self.login_secondary_account()
        response = self.client.post(self.new_url, self.html_creative_post_body,
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        eq_(response.status_code, 404)


def get_line_item_key_from_redirect_url(redirect_url):
    """
    Helper method for getting a line item key from the redirect
    url that's passed back in many post views.
    """
    return redirect_url.replace('/advertise/line_items/', '').rstrip('/')
