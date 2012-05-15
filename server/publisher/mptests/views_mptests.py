import datetime
import os
import simplejson
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from admin.randomgen import generate_account
from common.utils.test.test_utils import dict_eq, model_to_dict, time_almost_eq
from common.utils.test.views import BaseViewTestCase
from publisher.forms import AppForm, AdUnitForm
from publisher.models import App, AdUnit
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

    @staticmethod
    def _generate_post_data(**kwargs):
        post_data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u''],
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
        post_data.update(kwargs)
        return post_data

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

    def mptest_create_app_and_adunit(self):
        """
        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app and adunit were created as expected.
        """

        # Build a dictionary to submit as a POST that contains valid default
        # parameters.
        data = self._generate_post_data()

        # TODO: add files
        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 302)

        # Make sure there is exactly one app for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(len(apps_dict), 1)

        app = apps_dict.values()[0]

        app_dict = model_to_dict(app, exclude=['t'])

        expected_app_dict = _default_app_dict(self.account)

        dict_eq(app_dict, expected_app_dict, exclude=['t'])

        # Make sure the app was created within the last minute.
        time_almost_eq(app.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

        # Creating an app automatically creates a child adunit. Ensure that
        # there is exactly one adunit for this account.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Validate that the DB has been updated accurately.
        expected_adunit_dict = _default_adunit_dict(self.account, app)

        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

    # This test is broken because of an existing bug in both AppForm (name isn't
    # required) and CreateAppHandler.post (attempts to put None app when form
    # validation fails).
    def mptest_create_app_and_adunit_app_validation(self):
        """
        Confirm that create_app returns the appropriate validation errors when
        no app name is supplied and that the database state does not change.
        """

        # Submit an invalid POST by not supplying the required adunit name.
        data = self._generate_post_data(name=[u''])

        #TODO: add files
        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 200)

        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(not post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(adunits_dict, {})

    def mptest_create_app_and_adunit_adunit_validation(self):
        """
        Confirm that create_app returns the appropriate validation errors when
        no adunit name is supplied and that the database state does not change.
        """

        # Submit an invalid POST by not supplying the required adunit name.
        data = self._generate_post_data(**{'adunit-name': [u'']})

        # TODO: add files
        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 200)

        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(not post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(adunits_dict, {})


class AppUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppUpdateAJAXViewTestCase, self).setUp()

        self.app = _generate_app(self.account)
        self.adunit = _generate_adunit(self.account, self.app)

        self.url = reverse('publisher_app_update_ajax', args=(str(self.app.key()),))

    @staticmethod
    def _generate_post_data(**kwargs):
        post_data = {
            u'app_type': [u'iphone'],
            u'name': [u'Business App'],
            u'package': [u''],
            u'url': [u'', u''],
            u'img_file': [u''],
            u'secondary_category': [u''],
            u'ajax': [u'true'],
            u'img_url': [u''],
            u'primary_category': [u'business']
        }
        post_data.update(kwargs)
        return post_data

    def mptest_update_app_success(self):
        # Generate default POST data, post to URL, and get response.
        data = self._generate_post_data()
        response = self.client.post(self.url, data)

        # Confirm successful status code and correct response content.
        eq_(response.status_code, 200)
        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        # After updating the app, the account should still own 1 app and 1
        # adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the updated app, and convert the model to a dict for eventual
        # comparison.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])

        # Build a dict of expected app properties and compare to the actual
        # state of the db.
        expected_app_dict = _default_app_dict(
            self.account,
            name=u'Business App',
            primary_category=u'business')
        dict_eq(app_dict, expected_app_dict, exclude=['t'])

        # Obtain the updated adunit and convert the model to a dict.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of expected adunit properties and compare to the actual
        # state of the db.
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_failure(self):
        data = self._generate_post_data(name=[u''])

        # TODO: add files
        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        eq_(simplejson.loads(response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        app = apps_dict.values()[0]

        app_dict = model_to_dict(app, exclude=['t'])

        expected_app_dict = _default_app_dict(self.account)

        dict_eq(app_dict, expected_app_dict, exclude=['t'])

        adunit = adunits_dict.values()[0]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Validate that the DB has been updated accurately.
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)

        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_authorization(self):
        self.login_secondary_account()

        data = self._generate_post_data()

        # TODO: add files
        response = self.client.post(self.url, data)
        eq_(response.status_code, 404)

        apps_dict = PublisherQueryManager.get_apps_dict_for_account(account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        app = apps_dict.values()[0]

        app_dict = model_to_dict(app, exclude=['t'])

        expected_app_dict = _default_app_dict(self.account)

        dict_eq(app_dict, expected_app_dict, exclude=['t'])

        adunit = adunits_dict.values()[0]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Validate that the DB has been updated accurately.
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)

        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])


class AdUnitUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitUpdateAJAXViewTestCase, self).setUp()

        self.app = _generate_app(self.account)
        self.adunit = _generate_adunit(self.account, self.app)

        self.url = reverse('publisher_adunit_update_ajax')

    def _generate_post_data(self, **kwargs):
        post_data = {
            u'adunit-app_key': [unicode(self.app.key())],
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u''],
            u'adunit-custom_width': [u''],
            u'adunit-custom_height': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-device_format': [u'phone'],
            u'adunit-refresh_interval': [u'0'],
            u'ajax': ['true'],
        }
        post_data.update(kwargs)
        return post_data

    def mptest_create_adunit(self):
        """
        Confirm that adunit creation works by submitting known good parameters,
        and confirming the adunit was created as expected.
        """

        # Build a dictionary to submit as a POST that contains valid default
        # parameters.
        data = self._generate_post_data()

        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        # Confirm that the response content is exactly as we expect.
        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        # Ensure that this account has only one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 2)

        # TODO: .
        # adunits = adunits_dict.values()
        # new_adunits = adunits.filter(lambda a: a.key != self.adunit.key())
        # new_adunit = new_adunits[0]

        adunit = adunits_dict.values()[0]
        if adunit.key() == self.adunit.key():
            adunit = adunits_dict.values()[1]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of expected adunit properties and compare to the actual
        # state of the db.
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        # Make sure the adunit was created within the last minute.
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

    def mptest_create_adunit_validation(self):
        """
        Confirm that create_adunit returns the appropriate validation errors
        when no adunit name is supplied and that the database state does not
        change.
        """

        # We POST invalid data by not supplying the required name.
        data = self._generate_post_data(**{'adunit-name': [u'']})

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
        eq_(len(adunits_dict), 1)

    def mptest_update_adunit(self):
        data = self._generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        expected_adunit_dict = _default_adunit_dict(
            self.account,
            self.app,
            name=u'Updated Banner Ad')
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_validation(self):

        # We POST invalid data by not supplying the required name.

        data = self._generate_post_data(**{
            'adunit-name': [u''],
            'adunit_key': [unicode(self.adunit.key())]})

        response = self.client.post(self.url, data)
        eq_(response.status_code, 200)

        eq_(simplejson.loads(response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_authorization(self):
        self.login_secondary_account

        data = self._generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        response = self.client.post(self.url, data)
        eq_(response.status_code, 404)

        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])


def _generate_app(account, **kwargs):
    app_dict = {
        'account': account,
        'name': 'Book App',
        'app_type': 'iphone',
        'primary_category': 'books',
    }
    app_dict.update(kwargs)
    app = App(**app_dict)
    app.put()
    return app


def _generate_adunit(account, app, **kwargs):
    adunit_dict = {
            'app_key': app,
            'account': account,
            'name': 'Banner Ad',
            'device_format': 'phone',
            'format': '320x50',
            'ad_type': None,
            'color_border': '336699',
            'color_bg': 'FFFFFF',
            'color_link': '0000FF',
            'color_text': '000000',
            'color_url': '008000',
    }
    adunit_dict.update(kwargs)
    adunit = AdUnit(**adunit_dict)
    adunit.put()
    return adunit


def _default_app_dict(account, **kwargs):
    app_dict = {
        'account': account,
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

    app_dict.update(kwargs)
    return app_dict


def _default_adunit_dict(account, app, **kwargs):
    adunit_dict = {
        'name': u'Banner Ad',
        'description': None,
        'ad_type': None,
        'custom_width': None,
        'custom_height': None,
        'format': u'320x50',
        'app_key': app,
        'device_format': u'phone',
        'refresh_interval': 0,
        'account': account,
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
        'color_bg': u'FFFFFF',
        'color_link': u'0000FF',
        'color_text': u'000000',
        'color_url': u'008000',
        'network_config': None,
    }

    adunit_dict.update(kwargs)
    return adunit_dict
