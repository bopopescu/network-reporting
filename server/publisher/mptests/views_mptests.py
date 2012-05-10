import datetime
import os
import simplejson
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from account.models import NetworkConfig
from admin.randomgen import generate_app, generate_adunit
from common.utils.test.views import BaseViewTestCase
from publisher.query_managers import PublisherQueryManager


class AppIndexViewTestCase(BaseViewTestCase):
    def mptest_http_response_code(self):
        url = reverse('app_index')
        response = self.client.get(url)
        self.assertTrue(response.status_code in [200, 302])


class CreateAppViewTestCase(BaseViewTestCase):
    def setUp(self):
        super(CreateAppViewTestCase, self).setUp()

        self.app1 = generate_app(self.account)
        self.app2 = generate_app(self.account)
        self.app3 = generate_app(self.account)
        self.adunit1 = generate_adunit(self.app1, self.account)

    def mptest_create_app(self):
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        self.assertEqual(len(apps_dict), 3)

        url = reverse('publisher_create_app')
        data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u'\r\n'],
            u'adunit-custom_height': [u''],
            u'app_type': [u'iphone'],
            u'name': [u'Angry Birds'],
            u'package': [u''],
            u'url': [u'', u''],
            u'img_file': [u''],
            u'secondary_category': [u''],
            u'adunit-custom_width': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-app_key': [u''],
            u'adunit-device_format': [u'phone'],
            u'img_url': [u''],
            u'primary_category': [u'books'],
            u'adunit-refresh_interval': [u'0'],
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        self.assertEqual(len(apps_dict), 4)

class CreateAdUnitTestCase(BaseViewTestCase):
    def setUp(self):
        super(CreateAdUnitTestCase, self).setUp()

        self.app = generate_app(self.account)

    def mptest_create_adunit(self):
        url = reverse('publisher_adunit_update_ajax')

        data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u'AdUnit Description'],
            u'adunit-custom_width': [u''],
            u'adunit-custom_height':[u''],
            u'adunit-format': [u'320x50'],
            u'adunit-app_key': [unicode(self.app.key())],
            u'adunit-device_format': [u'phone'],
            u'adunit-refresh_interval': [u'0'],
            # We have absolutely no idea why ajax is included in this dictionary.
            u'ajax': ['true'],
        }

        response = self.client.post(url, data)
        eq_(response.status_code, 200)

        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]

        # Validate that the DB has been updated accurately.
        eq_(adunit.name, u'Banner Ad')
        eq_(adunit.description, u'AdUnit Description')
        eq_(adunit.custom_width, None)
        eq_(adunit.custom_height, None)
        eq_(adunit.format, u'320x50')
        eq_(adunit.app_key.key(), self.app.key())
        eq_(adunit.device_format, u'phone')
        eq_(adunit.refresh_interval, 0)

        eq_(adunit.account.key(), self.account.key())

        # Make sure we don't modify any existing parameters
        eq_(adunit.adsense_channel_id, None)
        eq_(adunit.url, None)
        eq_(adunit.resizable, False)
        eq_(adunit.landscape, False)
        eq_(adunit.deleted, False)
        eq_(adunit.jumptap_site_id, None)
        eq_(adunit.millennial_site_id, None)
        eq_(adunit.keywords, None)

        eq_(adunit.animation_type, u'0')
        eq_(adunit.color_border, u'336699')
        eq_(adunit.color_bg, u'FFFFFF')
        eq_(adunit.color_link, u'0000FF')
        eq_(adunit.color_text, u'000000')
        eq_(adunit.color_url, u'008000')

        utcnow = datetime.datetime.utcnow()
        ok_(adunit.t > utcnow - datetime.timedelta(minutes=1) and
            adunit.t < utcnow + datetime.timedelta(minutes=1))

        eq_(adunit.network_config, None)
