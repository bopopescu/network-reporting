import copy
import os
import sys
import unittest

sys.path.append(os.environ['PWD'])

import common.utils.test.setup


from nose.tools import ok_

from common.utils.test.fixtures import generate_app, generate_adunit
from common.utils.test.test_utils import model_eq
from publisher.forms import AppForm, AdUnitForm


class AppFormTestCase(unittest.TestCase):

    DEFAULT_DATA = {
        'name': 'Test App',
        'app_type': 'iphone',
        'primary_category': 'books',
    }

    def mptest_required_fields(self):
        app_form = AppForm(self.DEFAULT_DATA)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        expected_app = generate_app(None, **self.DEFAULT_DATA)

        model_eq(app, expected_app, check_primary_key=False)

    def mptest_required_field_missing(self):
        for key in self.DEFAULT_DATA.keys():
            incomplete_data = copy.copy(self.DEFAULT_DATA)
            del incomplete_data[key]

            app_form = AppForm(incomplete_data)

            ok_(not app_form.is_valid(),
                "%s was missing, but the AppForm validated." % key)

            ok_(key in app_form._errors)


class AdUnitFormTestCase(unittest.TestCase):

    DEFAULT_DATA = {
        'name': 'Test AdUnit',
        'device_format': 'phone',
        'format': 'full',
        # This field is not marked as required in the model or form, but is
        # effectively made required by AdUnitForm.clean_refresh_interval.
        'refresh_interval': 0,
    }

    def mptest_required_fields(self):
        adunit_form = AdUnitForm(self.DEFAULT_DATA)

        ok_(adunit_form.is_valid(),
            "The AdUnitForm was passed valid data but failed to validate:\n%s" %
                adunit_form._errors.as_text())

        adunit = adunit_form.save()

        expected_adunit = generate_adunit(None, None, **self.DEFAULT_DATA)

        model_eq(adunit, expected_adunit, check_primary_key=False)

    def mptest_required_field_missing(self):
        for key in self.DEFAULT_DATA.keys():
            incomplete_data = copy.copy(self.DEFAULT_DATA)
            del incomplete_data[key]

            adunit_form = AdUnitForm(incomplete_data)

            ok_(not adunit_form.is_valid(),
                "%s was missing, but the AdUnitForm validated." % key)

            ok_(key in adunit_form._errors)
