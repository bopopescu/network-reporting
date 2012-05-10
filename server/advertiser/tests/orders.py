# don't remove, necessary to set up the test env
import sys, os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from common.utils.test.views import BaseViewTestCase

import logging
import unittest
import simplejson as json

from django.core.urlresolvers import reverse
from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_

from admin.randomgen import generate_campaign, generate_adgroup, generate_creative
from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)

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
    def mptest_http_response_code(self):
        url = reverse('advertiser_order_and_line_item_form_new')
        response = self.client.get(url)
        ok_(response.status_code in [200, 302])


class NewLineItemTestCase(OrderViewTestCase):
    def mptest_http_response_code(self):
        url = reverse('advertiser_line_item_form_new', kwargs={'order_key': unicode(self.order.key())})
        response = self.client.get(url)
        ok_(response.status_code in [200, 302])


class EditLineItemTestCase(OrderViewTestCase):
    def mptest_http_response_code(self):
        url = reverse('advertiser_line_item_form_edit', kwargs={'line_item_key': unicode(self.line_item.key())})
        response = self.client.get(url)
        ok_(response.status_code in [200, 302])


class AdSourceChangeTestCase(OrderViewTestCase):

    def setUp(self):
        super(AdSourceChangeTestCase, self).setUp()
        self.url = reverse('advertiser_ad_source_status_change')
    
    def mptest_http_response_code(self):
        response = self.client.post(self.url)
        ok_(response.status_code in [200, 302])


    def mptest_creative_run(self):
        self.creative.active = False
        CreativeQueryManager.put(self.creative)
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.creative.key()),
                                               'status': 'run'})
        self.creative = CreativeQueryManager.get(self.creative.key())
        eq_(self.creative.active, True)

    def mptest_creative_pause(self):
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.creative.key()),
                                               'status': 'pause'})
        self.creative = CreativeQueryManager.get(self.creative.key())
        eq_(self.creative.active, False)

    def mptest_creative_delete(self):
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.creative.key()),
                                               'status': 'delete'})
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
        self.order.active = False
        CampaignQueryManager.put(self.order)
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.order.key()),
                                               'status': 'run'})
        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.active, True)
        
        eq_(self.line_item.active, True)

    def mptest_order_pause(self):
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.order.key()),
                                               'status': 'pause'})
        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.active, False)

        eq_(self.line_item.active, True)

    def mptest_order_archive(self):
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.order.key()),
                                               'status': 'archive'})
        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.archived, True)

        eq_(self.line_item.archived, False)

    def mptest_order_delete(self):      
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url, data={'ad_sources[]': unicode(self.order.key()),
                                               'status': 'delete'})
        self.order = CampaignQueryManager.get(self.order.key())
        eq_(self.order.deleted, True)
        eq_(self.order.active, False)

        eq_(self.line_item.deleted, False)
        eq_(self.line_item.active, True)

    def mptest_mixed_run(self):
        pass
    def mptest_mixed_pause(self):
        pass
    def mptest_mixed_archive(self):
        pass
    def mptest_mixed_delete(self):
        pass
