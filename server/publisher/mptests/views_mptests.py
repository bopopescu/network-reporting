import datetime
import os
import simplejson
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

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
        """
        Generate a dict of POST parameters that would be generated by the
        create app view page. This should correspond to _generate_app,
        _generate_adunit, _default_app_dict, and _default_adunit_dict functions
        below. Optionally pass in keywords to modify the default key/value
        pairs.
        """
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

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are not bound.
        ok_(isinstance(get_response.context['app_form'], AppForm))
        ok_(not get_response.context['app_form'].is_bound)
        ok_(isinstance(get_response.context['adunit_form'], AdUnitForm))
        ok_(not get_response.context['adunit_form'].is_bound)

    def mptest_create_app_and_adunit(self):
        """
        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app/adunit were created as expected.
        """

        post_data = self._generate_post_data()

        # We're expecting a statuc code 302 because this view, on successful
        # creation, redirects to the app detail page.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 302)

        # Make sure there are exactly one app and one adunit for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the created app/adunit and convert their models to dicts.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of expected app/adunit properties and compare them to
        # the actual state of the db.
        expected_app_dict = _default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = _default_adunit_dict(self.account, app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        # Make sure the app/adunit were created within the last minute.
        time_almost_eq(app.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))
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
        post_data = self._generate_post_data(name=[u''])

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are bound. Additionally, confirm that the AppForm did not
        # validate, whereas the AdUnitForm did.
        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(not post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})

    def mptest_create_app_and_adunit_adunit_validation(self):
        """
        Confirm that create_app returns the appropriate validation errors when
        no adunit name is supplied and that the database state does not change.
        """

        # Submit an invalid POST by not supplying the required adunit name.
        # We need to supply kwargs as an expanded dict because 'adunit-name'
        # has a hyphen-minus in its name.
        data = self._generate_post_data(**{'adunit-name': [u'']})

        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are bound. Additionally, confirm that the AdUnitForm did not
        # validate, whereas the AppForm did.
        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(not post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})


class AppUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppUpdateAJAXViewTestCase, self).setUp()

        self.app = _generate_app(self.account)
        self.adunit = _generate_adunit(self.account, self.app)

        self.url = reverse(
            'publisher_app_update_ajax',
            args=[str(self.app.key())])

    @staticmethod
    def _generate_post_data(**kwargs):
        """
        Generate a dict of POST parameters that would change the name and
        primary category of the app generated by _generate_app. Optionally
        pass in keywords to modify the default key/value pairs.
        """
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

    def mptest_update_app(self):
        """
        Confirm that app editing works by submitting known good parameters and
        confirming the app was modified as expected. Children adunits should
        not be changed.
        """

        post_data = self._generate_post_data()

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(simplejson.loads(post_response.content), {
            'success': True,
            'errors': [],
        })

        # After updating the app, the account should still own one app and one
        # adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the updated app/adunit and convert them to dicts. Exclude 't'
        # because the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of expected app/adunit properties and compare them to the
        # actual state of the db. Based on our POST data, we expect app name and
        # primary_category to have changed. AdUnit properties should not change.
        expected_app_dict = _default_app_dict(
            self.account,
            name=u'Business App',
            primary_category=u'business')
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_validation(self):
        """
        Confirm that posting invalid parameters (i.e. empty app name) will
        result in validation errors and no change to the db state.
        """

        # Remove name from the post parameters to generate a validation error.
        post_data = self._generate_post_data(name=[u''])

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(simplejson.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one app and one adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the app/adunit and convert them to dicts. Exclude 't' because
        # the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of the expected app/adunit properties and compare them to
        # actual state of the db, which should not have changed.
        expected_app_dict = _default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_authorization(self):
        """
        Attempt to update an app using an unauthorized account. Confirm that the
        correct error is returned and that the db state has not changed.
        """

        self.login_secondary_account()

        post_data = self._generate_post_data()

        # We expect a 404 HTTP response code because the secondary account is
        # not authorized to update this app.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 404)

        # The account should still own exactly one app and one adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the app/adunit and convert them to dicts. Exclude 't' because
        # the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of the expected app/adunit properties and compare them to
        # actual state of the db, which should not have changed.
        expected_app_dict = _default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
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
        """
        Generate a dict of POST parameters that would be generated by the
        app detail or adunit detail pages. This should correspond to the
        _generate_adunit and _default_adunit_dict functions below. Optionally
        pass in keywords to modify the default key/value pairs.
        """
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
        and confirming the adunit was created as expected by checking db state.
        """

        post_data = self._generate_post_data()

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(simplejson.loads(post_response.content), {
            'success': True,
            'errors': [],
        })

        # This account should now have two adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 2)

        # TODO: .
        # adunits = adunits_dict.values()
        # new_adunits = adunits.filter(lambda a: a.key != self.adunit.key())
        # new_adunit = new_adunits[0]

        # Obtain the created adunit (the one that is not self.adunit) and
        # convert it to a dict. Exclude 't' because the exact creation time is
        # unknown.
        adunit = adunits_dict.values()[0]
        if adunit.key() == self.adunit.key():
            adunit = adunits_dict.values()[1]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db.
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
        post_data = self._generate_post_data(**{'adunit-name': [u'']})

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(simplejson.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one app and one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

    def mptest_update_adunit(self):
        """
        Confirm that adunit updating works by submitting known good parameters,
        checking for the appropriate response, and confirming db state.
        """

        # Change the name of an existing adunit by submitting a valid POST. We
        # need to supply kwargs as an expanded dict because 'adunit-name' has a
        # hyphen-minus in its name.
        post_data = self._generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        response = self.client.post(self.url, post_data)
        eq_(response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(simplejson.loads(response.content), {
            'success': True,
            'errors': [],
        })

        # There should still be exactly one adunit for this account.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the updated adunit and convert it to a dict. Exclude 't'
        # because the exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db.
        expected_adunit_dict = _default_adunit_dict(
            self.account,
            self.app,
            name=u'Updated Banner Ad')
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_validation(self):
        """
        Confirm that editing an adunit returns the appropriate validation errors
        when no adunit name is supplied and that the database state does not
        change.
        """

        # We POST invalid data by not supplying the required name.
        post_data = self._generate_post_data(**{
            'adunit-name': [u''],
            'adunit_key': [unicode(self.adunit.key())]})

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(simplejson.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the adunit and convert it to a dict. Exclude 't' because the
        # exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db, which should not have changed.
        expected_adunit_dict = _default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_authorization(self):
        """
        Attempt to update an adunit using an unauthorized account. Confirm that
        the correct error is returned and that the db state has not changed.
        """

        self.login_secondary_account

        post_data = self._generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        # We expect a 404 HTTP response code because the secondary account is
        # not authorized to update this adunit.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 404)

        # The account should still own exactly one one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the adunit and convert it to a dict. Exclude 't' because the
        # exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db, which should not have changed.
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
