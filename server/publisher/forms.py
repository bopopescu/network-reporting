from __future__ import with_statement
import urllib2 as urllib
from google.appengine.api import images, files
from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from publisher.models import Site, App

import logging
from common.utils import helpers


CATEGORY_CHOICES = (
        (u'', '-----------------'),
        (u'books', 'Books'),
        (u'business', 'Business'),
        (u'education', 'Education'),
        (u'entertainment', 'Entertainment'),
        (u'finance', 'Finance'),
        (u'games', 'Games'),
        (u'healthcare_and_fitness', 'Healthcare & Fitness'),
        (u'lifestyle', 'Lifestyle'),
        (u'medical', 'Medical'),
        (u'music', 'Music'),
        (u'navigation', 'Navigation'),
        (u'news', 'News'),
        (u'photography', 'Photography'),
        (u'productivity', 'Productivity'),
        (u'reference', 'Reference'),
        (u'social_networking', 'Social Networking'),
        (u'sports', 'Sports'),
        (u'travel', 'Travel'),
        (u'utilities', 'Utilities'),
        (u'weather', 'Weather'),
)


class AppForm(mpforms.MPModelForm):
    TEMPLATE = 'publisher/forms/app_form.html'

    img_url = forms.URLField(verify_exists=False,required=False)
    img_file = forms.FileField(required=False)
    is_edit_form = forms.BooleanField(required=False)

    primary_category = mpfields.MPChoiceField(choices=CATEGORY_CHOICES,
                                              widget=mpwidgets.MPSelectWidget,
                                              required=True)
    secondary_category = mpfields.MPChoiceField(choices=CATEGORY_CHOICES,
                                                widget=mpwidgets.MPSelectWidget,
                                                required=False)

    def __init__(self, *args,**kwargs):
        instance = kwargs.get('instance',None)
        initial = kwargs.get('initial',None)
        is_edit_form = kwargs.pop('is_edit_form', None)

        if instance:
            img_url = instance.icon_url
            if not initial:
                initial = {}
            initial.update(img_url=img_url)
            initial.update(is_edit_form=is_edit_form)
            kwargs.update(initial=initial)
        super(AppForm,self).__init__(*args,**kwargs)

    class Meta:
        model = App
        fields = ('name',
                  'app_type',
                  'url',
                  'package',
                  'description',
                  'adsense_app_name',
                  'primary_category',
                  'secondary_category')

    def save(self, commit=True):
        obj = super(AppForm, self).save(commit=False)

        # Save the image url if they specified that
        if self.cleaned_data['img_url']:
            # TODO: add error handling
            # If there's a new image
            if not self.cleaned_data['img_url'] == self.initial.get('img_url'):
                response = urllib.urlopen(self.cleaned_data['img_url'])
                img = response.read()
                # Why don't we resize the app icon to be the proper size?
                # TODO This would be a good place to do it.
                obj.icon_blob = self.store_icon(img)
                obj.image_serve_url = helpers.get_url_for_blob(obj.icon_blob, ssl=False)

        # Save the file if they uploaded one
        elif self.cleaned_data['img_file']:
            # TODO: add error handling
            img = self.cleaned_data['img_file'].read()
            icon = images.resize(img, 60, 60)
            obj.icon_blob = self.store_icon(icon)
            obj.image_serve_url = helpers.get_url_for_blob(obj.icon_blob, ssl=False)
        if commit:
            obj.put()
        return obj

    def clean_name(self):
        data = self.cleaned_data['name']
        if not data:
            raise forms.ValidationError('Please provide a name for your app.')
        return data

    # def clean_secondary_category(self):
    #     secondary_category = self.cleaned_data['secondary_category']
    #     primary_category = self.cleaned_data['primary_category']
    #     if secondary_category == primary_category:
    #         message = """Please choose a secondary category
    #         that's different from your primary category."""
    #         raise forms.ValidationError(message)
    #     return secondary_category

    def store_icon(self, icon):
        # add the icon it to the blob store
        fname = files.blobstore.create(mime_type='image/png')
        with files.open(fname, 'a') as f:
            f.write(icon)
        files.finalize(fname)
        return files.blobstore.get_blob_key(fname)


ANIMATION_CHOICES = (
        (u'0', 'No Animation'),
        (u'1', 'Random'),
        (u'2', 'Flip from left'),
        (u'3', 'Flip from right'),
        (u'4', 'Curl up'),
        (u'5', 'Curl down'),
        (u'6', 'Fade'),
)


DEVICE_FORMAT_CHOICES = (
        (u'phone', 'Phone'),
        (u'tablet', 'Tablet'),
)


class AdUnitForm(mpforms.MPModelForm):
    TEMPLATE = 'publisher/forms/adunit_form.html'
    format = mpfields.MPTextField(required=True,
                                  widget = mpwidgets.MPFormatWidget)
    device_format = mpfields.MPChoiceField(required=True,
                                           widget=mpwidgets.MPRadioWidget(attrs={'class': 'btn'}),
                                           choices=DEVICE_FORMAT_CHOICES)

    def clean_refresh_interval(self):
        refresh_interval = self.cleaned_data['refresh_interval']
        if refresh_interval < 0:
            raise forms.ValidationError('Refresh interval should be a positive integer.')
        return refresh_interval

    class Meta:
        model = Site
        fields = ('name',
                  'description',
                  'app_key',
                  'ad_type',
                  'backfill',
                  'keywords',
                  'custom_width',
                  'custom_height',
                  'device_format',
                  'format',
                  'adsense_channel_id',
                  'refresh_interval',
                  'landscape')
