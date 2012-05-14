import datetime
import os
import simplejson
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from admin.randomgen import generate_app, generate_adunit
from common.utils.test.test_utils import dict_eq, model_to_dict
from common.utils.test.views import BaseViewTestCase
from publisher.forms import AppForm, AdUnitForm
from publisher.query_managers import PublisherQueryManager


class AppIndexViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def mptest_http_response_code(self):
        """
        Confirm that app_index returns an appropriate HTTP status code.
        """
        url = reverse('app_index')
        response = self.client.get(url)
        ok_(response.status_code in [200, 302])


class CreateAppViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(CreateAppViewTestCase, self).setUp()

        self.url = reverse('publisher_create_app')

    def _check_status_and_context(self, expected_status_codes, expected_context):

        get_response = self.client.get(self.url)
        ok_(get_response.status_code in expected_status_codes)

        for key, value in expected_context.iteritems():
            eq_(get_response.context[key], value)

    # def _get_response_and_check_status(self, expected_status_codes):
    #     get_response = self.client.get(self.url)
    #     ok_(get_response.status_code in expected_status_codes)
    #     return get_response

    # def _post_response_and_check_status(self, expected_status_codes, data):
    #     post_response = self.client.post(self.url, data)
    #     ok_(post_response.status_code in expected_status_codes)
    #     return post_response

    def mptest_get(self):
        """
        Confirm that the create_app view returns the correct response to a GET
        request by checking the status_code and context.
        """

        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of hte appropriate
        # type and do not have a previous instance.
        ok_(isinstance(get_response.context['app_form'], AppForm))
        ok_(not get_response.context['app_form'].is_bound)
        ok_(isinstance(get_response.context['adunit_form'], AdUnitForm))
        ok_(not get_response.context['adunit_form'].is_bound)

    def mptest_create_app_success(self):
        """
        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app and adunit were created as expected.
        """

        # Build a dictionary to submit as a POST that contains valid default
        # parameters.
        data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u'AdUnit Description'],
            u'adunit-custom_height': [u''],
            u'app_type': [u'iphone'],
            u'name': [u'Book App'],
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

        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 302)

        # Make sure there is exactly one app for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(len(apps_dict), 1)

        app = apps_dict.values()[0]

        # Excluded fields with funky equalsing.
        # app.t
        app_dict = model_to_dict(app, exclude=['t'])

        # Other fields.
        expected_app_dict = {
            'account': self.account,
            'deleted': False,
            'name': u'Book App',
            'global_id': None,
            'adsense_app_name': None,
            'adsense_app_id': None,
            'admob_bgcolor': None,
            'admob_textcolor': None,
            'app_type': u'iphone',
            'description': None,
            'url': None,
            'package': None,
            'categories': [],
            'icon_blob': None,
            'image_serve_url': None,
            'jumptap_app_id': None,
            'millennial_app_id': None,
            'exchange_creative': None,
            'experimental_fraction': 0.0,
            'network_config': None,
            'primary_category': u'books',
            'secondary_category': None,
            'use_proxy_bids': True,
            'force_marketplace': True,
        }

        dict_eq(app_dict, expected_app_dict, exclude=['t'])

        # Make sure the app was created within the last minute.
        utcnow = datetime.datetime.utcnow()
        ok_(app.t > utcnow - datetime.timedelta(minutes=1) and
            app.t < utcnow)

        # Creating an app automatically creates a child adunit. Ensure that
        # there is exactly one adunit for this account.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Validate that the DB has been updated accurately.
        expected_adunit_dict = {
            'name': u'Banner Ad',
            'description': u'AdUnit Description',
            'custom_width': None,
            'custom_height': None,
            'format': u'320x50',
            'app_key': app,
            'device_format': u'phone',
            'refresh_interval': 0,
            'account': self.account,
            'adsense_channel_id': None,
            'url': None,
            'resizable': False,
            'landscape': False,
            'deleted': False,
            'jumptap_site_id': None,
            'millennial_site_id': None,
            'keywords': None,
            'animation_type': u'0',
            'color_border': u'336699',
            'color_bg': u'FFFFFF'
            'color_link': u'000000FF',
            'color_text': u'000000',
            'color_url': u'008000',
            # Will this work since network config is a refproperty?
            'network_config': None,
        }

        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        ok_(adunit.t > utcnow - datetime.timedelta(minutes=1) and
            adunit.t < utcnow)

    # This test is broken because of an existing bug in both AppForm (name isn't
    # required) and CreateAppHandler.post (attempts to put None app when form
    # validation fails).
    # def mptest_create_app_failure(self):
    #     """
    #     Confirm that create_app returns the appropriate validation errors when
    #     no app name is supplied and that the database state does not change.
    #     """

    #     # Submit an invalid POST by not supplying the required app name.
    #     data = {
    #         u'adunit-name': [u'Banner Ad'],
    #         u'adunit-description': [u'AdUnit Description'],
    #         u'adunit-custom_height': [u''],
    #         u'app_type': [u'iphone'],
    #         u'name': [u''],
    #         u'package': [u''],
    #         u'url': [u'', u''],
    #         u'img_file': [u''],
    #         u'secondary_category': [u''],
    #         u'adunit-custom_width': [u''],
    #         u'adunit-format': [u'320x50'],
    #         u'adunit-app_key': [u''],
    #         u'adunit-device_format': [u'phone'],
    #         u'img_url': [u''],
    #         u'primary_category': [u'books'],
    #         u'adunit-refresh_interval': [u'0'],
    #     }

    #     post_response = self.client.post(self.url, data)
    #     eq_(post_response.status_code, 200)

    #     # Make sure the response content reflects the validation errors.
    #     eq_(simplejson.loads(post_response.content), {
    #         'success': False,
    #         'errors': [[u'name', u'This field is required.']],
    #     })

    #     # Make sure that the state of the database has not changed, and that
    #     # there are still no apps nor adunits associated with this account.
    #     apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
    #     ok_(not apps_dict)
    #     adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
    #     ok_(not adunits_dict)


class AppUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppUpdateAJAXViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.app, self.account)

        self.url = reverse('publisher_app_update_ajax', args=(str(self.app.key()),))

    # def mptest_update_app_success(self):
    #     data = {}

    #     response = self.client.post(self.url, data)
    #     eq_(response.status_code, 200)

    #     eq_(simplejson.loads(response.content), {
    #         'success': True,
    #         'errors': [],
    #     })

    #     apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
    #     eq_(len(apps_dict), 1)
    #     adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
    #     eq_(len(adunits_dict), 1)

    #     app = apps_dict.values()[0]
    #     adunit = adunits_dict.values()[0]

    #     # Make sure all of the app's fields are appropriately set or remain at
    #     # default values.
    #     eq_(app.account.key(), self.account.key())
    #     eq_(app.name, u'Book App')
    #     ok_(app.global_id is None)
    #     ok_(app.adsense_app_name is None)
    #     ok_(app.adsense_app_id is None)
    #     ok_(app.admob_bgcolor is None)
    #     ok_(app.admob_textcolor is None)
    #     eq_(app.app_type, u'iphone')
    #     ok_(app.description is None)
    #     ok_(app.url is None)
    #     ok_(app.package is None)
    #     eq_(app.categories, [])
    #     ok_(app.icon_blob is None)
    #     ok_(app.image_serve_url is None)
    #     ok_(app.jumptap_app_id is None)
    #     ok_(app.millennial_app_id is None)

    #     # Make sure the app was created within the last minute.
    #     utcnow = datetime.datetime.utcnow()
    #     ok_(app.t > utcnow - datetime.timedelta(minutes=1) and
    #         app.t < utcnow)

    #     ok_(app.exchange_creative is None)
    #     eq_(app.experimental_fraction, 0.0)
    #     ok_(app.network_config is None)
    #     eq_(app.primary_category, u'books')
    #     ok_(app.secondary_category is None)
    #     ok_(app.use_proxy_bids)
    #     ok_(app.force_marketplace)

    #     # Creating an app automatically creates a child adunit. Ensure that
    #     # there is exactly one adunit for this account.
    #     adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
    #     eq_(len(adunits_dict), 1)

    #     adunit = adunits_dict.values()[0]

    #     # Validate that the DB has been updated accurately.
    #     eq_(adunit.name, u'Banner Ad')
    #     eq_(adunit.description, u'AdUnit Description')
    #     ok_(adunit.custom_width is None)
    #     ok_(adunit.custom_height is None)
    #     eq_(adunit.format, u'320x50')
    #     eq_(adunit.app_key.key(), app.key())
    #     eq_(adunit.device_format, u'phone')
    #     eq_(adunit.refresh_interval, 0)

    #     eq_(adunit.account.key(), self.account.key())

    #     # Make sure we don't modify any existing parameters
    #     ok_(adunit.adsense_channel_id is None)
    #     ok_(adunit.url is None)
    #     ok_(not adunit.resizable)
    #     ok_(not adunit.landscape)
    #     ok_(not adunit.deleted)
    #     ok_(adunit.jumptap_site_id is None)
    #     ok_(adunit.millennial_site_id is None)
    #     ok_(adunit.keywords is None)

    #     eq_(adunit.animation_type, u'0')
    #     eq_(adunit.color_border, u'336699')
    #     eq_(adunit.color_bg, u'FFFFFF')
    #     eq_(adunit.color_link, u'0000FF')
    #     eq_(adunit.color_text, u'000000')
    #     eq_(adunit.color_url, u'008000')

    #     ok_(adunit.t > utcnow - datetime.timedelta(minutes=1) and
    #         adunit.t < utcnow)

    #     ok_(adunit.network_config is None)

    def mptest_update_app_failure(self):
        pass


class AdUnitUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitUpdateAJAXViewTestCase, self).setUp()

        # We need to create an app for the tested adunit to which the adunit
        # will belong.
        self.app = generate_app(self.account)

        self.url = reverse('publisher_adunit_update_ajax')

    def mptest_create_adunit_success(self):
        """
        Confirm that adunit creation works by submitting known good parameters,
        and confirming the adunit was created as expected.
        """
        import logging
        logging.error(self.account)

        # Build a dictionary to submit as a POST that contains valid default
        # parameters.
        data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u'AdUnit Description'],
            u'adunit-custom_width': [u''],
            u'adunit-custom_height': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-app_key': [unicode(self.app.key())],
            u'adunit-device_format': [u'phone'],
            u'adunit-refresh_interval': [u'0'],
            # We have absolutely no idea why ajax is included in this dictionary.
            u'ajax': ['true'],
        }

        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        # Confirm that the response content is exactly as we expect.
        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        from account.models import Account
        from publisher.models import AdUnit
        accounts = Account.all().fetch(limit=2)
        logging.error(accounts)
        logging.error(len(accounts))
        eq_(self.account.key(), accounts[0].key())

        #adunit_key = AdUnit.get_value_for_datastore(self.account)
        #logging.error(adunit_key)

        adunits = AdUnit.all().fetch(limit=2)
        logging.error(adunits)
        logging.error(self.account.key())
        logging.error(adunits[0].account)
        logging.error(adunits[0].account.key())

        # Ensure that this account has only one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]

        # Validate that the DB has been updated accurately.
        eq_(adunit.name, u'Banner Ad')
        eq_(adunit.description, u'AdUnit Description')
        ok_(adunit.custom_width is None)
        ok_(adunit.custom_height is None)
        eq_(adunit.format, u'320x50')
        eq_(adunit.app_key.key(), self.app.key())
        eq_(adunit.device_format, u'phone')
        eq_(adunit.refresh_interval, 0)

        eq_(adunit.account.key(), self.account.key())

        # Make sure we don't modify any existing parameters
        ok_(adunit.adsense_channel_id is None)
        ok_(adunit.url is None)
        ok_(not adunit.resizable)
        ok_(not adunit.landscape)
        ok_(not adunit.deleted)
        ok_(adunit.jumptap_site_id is None)
        ok_(adunit.millennial_site_id is None)
        ok_(adunit.keywords is None)

        eq_(adunit.animation_type, u'0')
        eq_(adunit.color_border, u'336699')
        eq_(adunit.color_bg, u'FFFFFF')
        eq_(adunit.color_link, u'0000FF')
        eq_(adunit.color_text, u'000000')
        eq_(adunit.color_url, u'008000')

        # Make sure the app was created within the last minute.
        utcnow = datetime.datetime.utcnow()
        ok_(adunit.t > utcnow - datetime.timedelta(minutes=1) and
            adunit.t < utcnow)

        ok_(adunit.network_config is None)

    def mptest_create_adunit_failure(self):
        """
        Confirm that create_adunit returns the appropriate validation errors
        when no adunit name is supplied and that the database state does not
        change.
        """

        # We POST invalid data by not supplying the required name.
        data = {
            u'adunit-name': [u''],
            u'adunit-description': [u'AdUnit Description'],
            u'adunit-custom_width': [u''],
            u'adunit-custom_height': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-app_key': [unicode(self.app.key())],
            u'adunit-device_format': [u'phone'],
            u'adunit-refresh_interval': [u'0'],
            # We have absolutely no idea why ajax is included in this dictionary.
            u'ajax': ['true'],
        }

        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        # Confirm that the response content fails with an appropriate validation
        # error.
        eq_(simplejson.loads(response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # Ensure that the database has not been modified, and that there are
        # still no adunits associated with this account.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        ok_(not adunits_dict)
