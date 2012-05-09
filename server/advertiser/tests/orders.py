# don't remove, necessary to set up the test env
import sys, os
sys.path.append(os.environ['PWD'])
import common.utils.test.setup
from common.utils.test.views import BaseViewTestCase

import logging
import unittest
import random
import datetime

from google.appengine.ext import testbed
from google.appengine.api import memcache
from django.core.urlresolvers import reverse
from django.test import Client
from django.test.utils import setup_test_environment
from nose.tools import eq_, ok_

from admin.randomgen import generate_campaign, generate_adgroup, generate_creative
from advertiser.query_managers import AdvertiserQueryManager, CampaignQueryManager \
                                      AdGroupQueryManager, CreativeQueryManager

# setup_test_environment()

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
    def mptest_http_response_code(self):
        url = reverse('advertiser_ad_source_status_change')
        response = self.client.post(url)
        ok_(response.status_code in [200, 302])


    def mptest_creative_run(self):
        pass
    def mptest_creative_pause(self):
        pass
    def mptest_creative_archive(self):
        pass
    def mptest_creative_delete(self):
        pass


    def mp_test_line_item_run(self):
        pass
    def mptest_line_item_pause(self):
        pass
    def mptest_line_item_archive(self):
        pass
    def mptest_line_item_delete(self):
        pass


    def mp_test_order_run(self):
        pass
    def mptest_order_pause(self):
        pass
    def mptest_order_archive(self):
        pass
    def mptest_order_delete(self):      
        pass

    def mptest_mixed_run(self):
        pass
    def mptest_mixed_pause(self):
        pass
    def mptest_mixed_archive(self):
        pass
    def mptest_mixed_delete(self):
        pass
