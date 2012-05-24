import copy
import os
import re
import sys
import unittest

sys.path.append(os.environ['PWD'])

import common.utils.test.setup


from common.utils.helpers import get_url_for_blob
from django.core.files.uploadedfile import SimpleUploadedFile
from nose.tools import ok_, eq_

from common.utils.test.fixtures import generate_app, generate_adunit
from common.utils.test.test_utils import model_eq
from publisher.forms import AppForm, AdUnitForm


IMAGE_DATA = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc````\x00\x00\x00\x05\x00\x01\xa5\xf6E@\x00\x00\x00\x00IEND\xaeB`\x82'
RESIZED_IMAGE_DATA = '\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00<\x00\x00\x00<\x08\x06\x00\x00\x00:\xfc\xd9r\x00\x00\x00$IDATx\x9c\xed\xc11\x01\x00\x00\x00\xc2\xa0\xf5O\xedi\t\xa0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00n8|\x00\x01N\x81\x9e\x1b\x00\x00\x00\x00IEND\xaeB`\x82'


class AppFormTestCase(unittest.TestCase):

    # TODO: is_edit_form?

    DEFAULT_DATA = {
        'name': 'Test App',
        'app_type': 'iphone',
        'primary_category': 'books',
    }

    DEFAULT_FILES = {
        'img_file': SimpleUploadedFile('icon.png', IMAGE_DATA, content_type='image/png')
    }

    def mptest_create_with_required_fields(self):
        app_form = AppForm(self.DEFAULT_DATA)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        expected_app = generate_app(None, **self.DEFAULT_DATA)

        model_eq(app, expected_app, check_primary_key=False)

    def mptest_create_with_required_field_missing(self):
        for key in self.DEFAULT_DATA.keys():
            incomplete_data = copy.copy(self.DEFAULT_DATA)
            del incomplete_data[key]

            app_form = AppForm(incomplete_data)

            ok_(not app_form.is_valid(),
                "%s was missing, but the AppForm validated." % key)

            eq_(app_form._errors.keys(), [key])

    def mptest_create_with_img_file(self):
        app_form = AppForm(self.DEFAULT_DATA, self.DEFAULT_FILES)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        data = copy.copy(self.DEFAULT_DATA)
        expected_app = generate_app(None, **data)

        model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

        image_data = app.icon_blob.open().read()
        eq_(image_data, RESIZED_IMAGE_DATA)

        ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))

    def mptest_create_with_img_url(self):
        pass  # TODO

    def mptest_edit_with_required_fields(self):
        app = generate_app(None)

        app_form = AppForm(self.DEFAULT_DATA, instance=app)

        ok_(app_form.is_valid(),
            "The AppForm was passed valid data but failed to validate:\n%s" %
                app_form._errors.as_text())

        app = app_form.save()

        expected_app = generate_app(None, **self.DEFAULT_DATA)

        model_eq(app, expected_app, check_primary_key=False)

    def mptest_edit_with_required_field_missing(self):
        app = generate_app(None)

        for key in self.DEFAULT_DATA.keys():
            incomplete_data = copy.copy(self.DEFAULT_DATA)
            del incomplete_data[key]

            app_form = AppForm(incomplete_data, instance=app)

            ok_(not app_form.is_valid(),
                "%s was missing, but the AppForm validated." % key)

            eq_(app_form._errors.keys(), [key])

    # def mptest_edit_with_img_file(self):
    #     app = generate_app(None)

    #     app_form = AppForm(self.DEFAULT_DATA, self.DEFAULT_FILES, instance=app)

    #     ok_(app_form.is_valid(),
    #         "The AppForm was passed valid data but failed to validate:\n%s" %
    #             app_form._errors.as_text())

    #     app = app_form.save()

    #     data = copy.copy(self.DEFAULT_DATA)
    #     expected_app = generate_app(None, **data)

    #     model_eq(app, expected_app, exclude=['t', 'icon_blob', 'image_serve_url'], check_primary_key=False)

    #     image_data = app.icon_blob.open().read()
    #     eq_(image_data, RESIZED_IMAGE_DATA)

    #     ok_(app.image_serve_url, get_url_for_blob(app.icon_blob))

    def mptest_edit_with_img_url(self):
        pass  # TODO


class AdUnitFormTestCase(unittest.TestCase):

    # TODO:
    #   initial = { 'app_key': generate_app() }
    #   instance = generate_adunit()

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

            eq_(adunit_form._errors.keys(), [key])

    def mptest_refresh_interval(self):
        invalid_data = copy.copy(self.DEFAULT_DATA)
        invalid_data['refresh_interval'] = -1

        adunit_form = AdUnitForm(invalid_data)

        ok_(not adunit_form.is_valid(),
            "refresh_interval was missing, but the AdUnitForm validated.")
