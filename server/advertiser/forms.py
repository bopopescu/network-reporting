from __future__ import with_statement
from datetime import datetime
import re

from django import forms
from django.forms.util import ErrorList
from google.appengine.api import images, files
from google.appengine.ext.db import Key

from advertiser.models import (Order, LineItem, Creative, TextCreative,
                               TextAndTileCreative, HtmlCreative, ImageCreative)
from common.constants import (IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES,
                              CITY_GEO, REGION_GEO, COUNTRY_GEO)
from common.utils import helpers
from common.utils.timezones import Pacific_tzinfo
from common.utils.tzinfo import UTC
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

from advertiser.widgets import CustomizableSplitDateTimeWidget


#THIS ORDER IS VERY IMPORTANT DO NOT CHANGE IT (thanks!)
GEO_LIST = (COUNTRY_GEO, REGION_GEO, CITY_GEO)


def get_filetype_extension(filename):
    if not type(filename) == str:
        filename = str(filename)
    if filename.find('.') >= 0:
        return filename.split('.')[-1]
    return None


class OrderForm(forms.ModelForm):
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Order Name'}))
    advertiser = forms.CharField(label='Advertiser:',
                                 widget=forms.TextInput(attrs={'class': 'required',
                                                               'placeholder': 'Order Advertiser'}))
    description = forms.CharField(label='Description:', required=False,
                                  widget=forms.Textarea(attrs={'cols': 50,
                                                               'rows': 3,
                                                               'placeholder': 'Order for My New App'}))

    class Meta:
        model = Order
        fields = ('name',
                  'advertiser',
                  'description',)


class LineItemForm(forms.ModelForm):
    adgroup_type = forms.ChoiceField(choices=(('gtee', 'Guaranteed'),
                                               ('promo', 'Promotional')),
                                      label='Line Item Type:')
    gtee_priority = forms.ChoiceField(choices=(('high', 'High'),
                                               ('normal', 'Normal'),
                                               ('low', 'Low')),
                                      initial='normal', label='Priority:',
                                      required=False)
    promo_priority = forms.ChoiceField(choices=(('normal', 'Normal'),
                                                ('backfill', 'Backfill')),
                                       initial='normal', label='Priority:',
                                       required=False)
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Line Item Name'}))
    start_datetime = forms.DateTimeField(input_formats=('%m/%d/%Y %I:%M %p',),
                                         label='Start Time:', required=False,
                                         widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                            'placeholder': 'MM/DD/YYYY'},
                                                                                time_attrs={'class': 'time',
                                                                                            'placeholder': 'HH:MM'},
                                                                                date_format='%m/%d/%Y',
                                                                                time_format='%I:%M %p'))
    end_datetime = forms.DateTimeField(input_formats=('%m/%d/%Y %I:%M %p',),
                                       label='Stop Time:', required=False,
                                       widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                          'placeholder': 'MM/DD/YYYY'},
                                                                              time_attrs={'class': 'time',
                                                                                          'placeholder': 'HH:MM'},
                                                                              date_format='%m/%d/%Y',
                                                                              time_format='%I:%M %p'))
    bid_strategy = forms.ChoiceField(choices=(('cpm', 'CPM'), ('cpc', 'CPC')),
                                     label='Rate:', initial='cpc')
    bid = forms.FloatField(initial=0.05,
                           widget=forms.TextInput(attrs={'class': 'float'}))
    daily_budget = forms.FloatField(required=False)
    full_budget = forms.FloatField(required=False)
    budget = forms.FloatField(required=False)
    budget_type = forms.ChoiceField(choices=(('daily', 'USD/day'),
                                             ('full_campaign', 'total USD')),
                                    initial='daily', required=False)
    budget_strategy = forms.ChoiceField(choices=(('evenly', 'Spread Evenly'),
                                                 ('allatonce', 'All at once')),
                                        label='Delivery Speed:',
                                        initial='allatonce', required=False,
                                        widget=forms.RadioSelect)
    # site_keys defined in __init__
    allocation_percentage = forms.FloatField(initial=100.0, label='Allocation:',
                                             required=False,
                                             widget=forms.TextInput(attrs={'class': 'float'}))
    daily_frequency_cap = forms.IntegerField(initial=0, label='Frequency Caps:',
                                             required=False,
                                             widget=forms.TextInput(attrs={'class': 'float'}))
    hourly_frequency_cap = forms.IntegerField(initial=0, required=False,
                                              widget=forms.TextInput(attrs={'class': 'float'}))
    device_targeting = forms.TypedChoiceField(choices=(('0', 'All'),
                                                       ('1', 'Filter by device and OS')),
                                              coerce=lambda x: bool(int(x)),
                                              initial=False,
                                              label='Device Targeting:',
                                              required=False,
                                              widget=forms.RadioSelect)
    target_iphone = forms.BooleanField(initial=True, label='iPhone',
                                       required=False)
    target_ipod = forms.BooleanField(initial=True, label='iPod', required=False)
    target_ipad = forms.BooleanField(initial=True, label='iPad', required=False)
    ios_version_min = forms.ChoiceField(choices=IOS_VERSION_CHOICES[1:],
                                        label='Min:', required=False)
    ios_version_max = forms.ChoiceField(choices=IOS_VERSION_CHOICES,
                                        label='Max:', required=False)
    target_android = forms.BooleanField(initial=True, label='Android',
                                        required=False)
    android_version_min = forms.ChoiceField(choices=ANDROID_VERSION_CHOICES[1:],
                                            label='Min:', required=False)
    android_version_max = forms.ChoiceField(choices=ANDROID_VERSION_CHOICES,
                                            label='Max:', required=False)
    target_other = forms.BooleanField(initial=True, label='Other',
                                      required=False)
    geo_predicates = forms.Field(required=False, widget=forms.SelectMultiple)
    region_targeting = forms.ChoiceField(choices=(('all', 'Everywhere'),
                                                  ('city', 'City')),
                                         initial='all',
                                         label='Region Targeting:',
                                         required=False,
                                         widget=forms.RadioSelect)
    cities = forms.Field(required=False, widget=forms.SelectMultiple)
    keywords = forms.CharField(required=False,
                               widget=forms.Textarea(attrs={'cols': 50,
                                                            'rows': 3}))

    def __init__(self, *args, **kwargs):
        # initial
        if len(args) > 5:
            initial = args[5]
        else:
            if 'initial' not in kwargs or not kwargs['initial']:
                kwargs['initial'] = {}
            initial = kwargs['initial']

        # instance
        instance = args[9] if len(args) > 9 else kwargs.get('instance', None)

        if instance:
            # gtee
            if 'gtee' in instance.adgroup_type:
                if 'high' in instance.adgroup_type:
                    initial['gtee_priority'] = 'high'
                elif 'low' in instance.adgroup_type:
                    initial['gtee_priority'] = 'low'
                initial['adgroup_type'] = 'gtee'

                if instance.budget_type == 'daily':
                    initial['budget'] = instance.daily_budget
                else:
                    initial['budget'] = instance.full_budget

                if instance.bid_strategy == 'cpm':
                    initial['budget'] = int(1000.0 * initial['budget'] / instance.bid)
            # promo
            elif instance.adgroup_type == 'backfill_promo':
                initial['adgroup_type'] = 'promo'
                initial['promo_priority'] = 'backfill'

            # convert datetimes from offset-naive UTC to Pacific
            if instance.start_datetime:
                initial['start_datetime'] = instance.start_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo())
            if instance.end_datetime:
                initial['end_datetime'] = instance.end_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo())

            # TODO: can't change the start date after a campaign has started.
            # TODO: not change the end date after a campaign has completed

            geo_predicates = []
            for geo_predicate in instance.geo_predicates:
                preds = geo_predicate.split(',')
                geo_predicates.append(','.join([str(pred.split('=')[1]) for pred in preds]))
            initial['geo_predicates'] = geo_predicates

            # TODO: seems like we don't need this?
            """
            if len(geo_predicates) == 1 and len(instance.cities):
                initial['region_targeting'] = 'city'
                initial.update(cities=instance.cities)
            """

        # allows us to set choices on instantiation
        site_keys = kwargs.pop('site_keys', [])

        super(forms.ModelForm, self).__init__(*args, **kwargs)

        # set choices based on the users adunits
        # TODO: can we do this a nicer way so we can declare this field with the other fields?
        self.fields['site_keys'] = forms.MultipleChoiceField(choices=site_keys, required=False)

    def _calculate_budget(self, budget):
        if self.data.get('bid_strategy', 'cpm') == 'cpm':
            return float(budget) / 1000.0 * float(self.data.get('bid', 0.0))
        else:
            return budget

    def clean_start_datetime(self):
        # TODO: if it is an existing campaign, you shouldn't be able to move the start date to the past
        # TODO: can't change the start date after a campaign has started.
        start_datetime = self.cleaned_data.get('start_datetime', None)
        if start_datetime:
            # if this is a new campaign, it must start in the future
            if not self.instance and start_datetime.date() < datetime.now(tz=Pacific_tzinfo()).date():
                raise forms.ValidationError("Start time must be in the future")
            # start_datetime is entered in Pacific Time
            start_datetime = start_datetime.replace(tzinfo=Pacific_tzinfo()).astimezone(UTC()).replace(tzinfo=None)
        return start_datetime

    def clean_end_datetime(self):
        # TODO: not change the end date after a campaign has completed
        end_datetime = self.cleaned_data.get('end_datetime', None)
        if end_datetime:
            # end_datetime is entered in Pacific Time
            end_datetime = end_datetime.replace(tzinfo=Pacific_tzinfo()).astimezone(UTC()).replace(tzinfo=None)
        return end_datetime

    def clean_allocation_percentage(self):
        allocation_percentage = self.cleaned_data.get('allocation_percentage', None)
        if (not isinstance(allocation_percentage, int) and
            not isinstance(allocation_percentage, float)):
            allocation_percentage = 100
        return allocation_percentage

    def clean_site_keys(self):
        return [Key(site_key) for site_key in self.cleaned_data.get('site_keys', [])]

    def clean_geo_predicates(self):
        geo_predicates = []
        for geo_predicate in self.cleaned_data.get('geo_predicates', []) or []:
            geo_predicate = tuple(geo_predicate.split(','))
            #Make the geo_list such that the one that needs 3 entries corresponds ot idx 2, 2 entires idx 1, 1 entry idx 0
            geo_predicates.append(GEO_LIST[len(geo_predicate) - 1] % geo_predicate)
        return geo_predicates

    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords', None)
        if keywords:
            if len(keywords) > 500:
                raise forms.ValidationError('Maximum 500 characters for keywords.')
        return keywords

    def clean(self):
        cleaned_data = super(LineItemForm, self).clean()

        # start and end datetimes
        # if start_datetime is None, use the current time
        if not cleaned_data.get('start_datetime', None):
            cleaned_data['start_datetime'] = datetime.now()
        start_datetime = cleaned_data['start_datetime']
        end_datetime = cleaned_data.get('end_datetime', None)
        # end_datetime must be after start_datetime
        if end_datetime and end_datetime <= start_datetime:
            if 'end_datetime' not in self._errors:
                self._errors['end_datetime'] = ErrorList()
            self._errors['end_datetime'].append("Stop time must be after start time")

        # gtee
        if cleaned_data['adgroup_type'] == 'gtee':
            # adgroup_type
            if not cleaned_data.get('gtee_priority', None):
                if 'gtee_priority' not in self._errors:
                    self._errors['gtee_priority'] = ErrorList()
                self._errors['gtee_priority'].append('This field is required')
            elif cleaned_data['gtee_priority'] in ('low', 'high'):
                cleaned_data['adgroup_type'] = 'gtee_%s' % cleaned_data['gtee_priority']

            # budget
            if not cleaned_data.get('budget', None):
                cleaned_data['daily_budget'] = None
                cleaned_data['full_budget'] = None
            else:
                has_required = True
                for field in ('bid_strategy', 'bid', 'budget_type', 'budget_strategy'):
                    if not cleaned_data.get(field, None):
                        if field not in self._errors:
                            self._errors[field] = ErrorList()
                        self._errors[field].append("This field is required")
                        has_required = False
                if has_required:
                    # BEWARE HACKS
                    # if the campaign is a cpm campaign, we need to calculate what the budget
                    # will be, since budgets are stored in dollar amounts.
                    if cleaned_data['budget_type'] == 'daily':
                        cleaned_data['daily_budget'] = self._calculate_budget(cleaned_data['budget'])
                        cleaned_data['full_budget'] = None
                    else:
                        if not cleaned_data['end_datetime'] and cleaned_data['budget_strategy'] != 'allatonce':
                            if 'budget_strategy' not in self._errors:
                                self._errors['budget_strategy'] = ErrorList()
                            self._errors['budget_strategy'].append("Delivery speed must be all at once for total budget with no stop time")
                        cleaned_data['full_budget'] = self._calculate_budget(cleaned_data['budget'])
                        cleaned_data['daily_budget'] = None

        # promo
        elif cleaned_data['adgroup_type'] == 'promo':
            # priority
            if not cleaned_data.get('promo_priority', None):
                if 'promo_priority' not in self._errors:
                    self._errors['promo_priority'] = ErrorList()
                self._errors['promo_priority'].append('This field is required')
            elif cleaned_data['promo_priority'] == 'backfill':
                cleaned_data['adgroup_type'] = 'backfill_promo'
            # promo campaigns have no budget
            cleaned_data['daily_budget'] = None
            cleaned_data['full_budget'] = None
            cleaned_data['budget_type'] = None
            cleaned_data['budget_strategy'] = None

        # don't store targeted cities unless region targeting for cities is selected
        if cleaned_data.get('region_targeting', None) != 'city':
            cleaned_data['cities'] = []

        return cleaned_data

    def save(self, *args, **kwargs):
        if self.instance and self.instance.site_keys:
            adunits = AdUnitQueryManager.get(self.instance.site_keys)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        line_item = super(forms.ModelForm, self).save(*args, **kwargs)

        if line_item.site_keys:
            adunits = AdUnitQueryManager.get(line_item.site_keys)
            AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

        return line_item

    class Meta:
        model = LineItem
        fields = ('adgroup_type',
                  'gtee_priority',
                  'promo_priority',
                  'name',
                  'start_datetime',
                  'end_datetime',
                  'bid_strategy',
                  'bid',
                  'daily_budget',
                  'full_budget',
                  'budget',
                  'budget_type',
                  'budget_strategy',
                  'site_keys',
                  'allocation_percentage',
                  'daily_frequency_cap',
                  'hourly_frequency_cap',
                  'device_targeting',
                  'target_iphone',
                  'target_ipod',
                  'target_ipad',
                  'ios_version_min',
                  'ios_version_max',
                  'target_android',
                  'android_version_min',
                  'android_version_max',
                  'target_other',
                  'geo_predicates',
                  'region_targeting',
                  'cities',
                  'keywords')


class AbstractCreativeForm(forms.ModelForm):

    def save(self, commit=True):
        obj = super(AbstractCreativeForm, self).save(commit=False)
        if not obj.conv_appid and obj.url:
            obj.conv_appid = self._get_appid(obj.url)

        if commit:
            obj.put()
        return obj

    def _get_appid(self, url):
        # extracts the itunes appid from the url
        # http://itunes.apple.com/il/app/imosaic-project/id335853048?mt=8
        # in this case: 335853048
        itunes_pattern = re.compile("http://itunes\.apple\.com.*id(\d+)")
        itunes_match = itunes_pattern.search(url)
        if itunes_match:
            itunes_id = itunes_match.group(1)
            return itunes_id

        # extracts the itunes appid from the url old phobos urls
        # http://phobos.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=386584429&mt=8
        # in this case: 386584429
        itunes_pattern = re.compile("http://phobos\.apple\.com.*id=(\d+)")
        itunes_match = itunes_pattern.search(url)
        if itunes_match:
            itunes_id = itunes_match.group(1)
            return itunes_id

        # extracts the package from the url
        # market://details?id=com.example.admob.lunarlander
        # in this case: com.example.admob.lunarlander
        # NOTE: there not be any other characters after the id
        android_pattern = re.compile("market://.*id\=(.+)$")
        android_match = android_pattern.search(url)
        if android_match:
            android_package_name = android_match.group(1)
            return android_package_name

        # return None if nothing was found
        return None


class BaseCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/base_creative_form.html'

    name = forms.CharField(initial="Creative",
                           widget=forms.TextInput(attrs={
                               'class': 'input-text required'
                           }))

    class Meta:
        model = Creative
        fields = ('ad_type', 'name', 'tracking_url', 'url', 'display_url',
                  'format', 'custom_height', 'custom_width', 'landscape',
                  'conv_appid', 'launchpage')

    def clean_name(self):
        data = self.cleaned_data.get('name', None).strip()
        if not data:
            raise forms.ValidationError('You must give your creative a name.')
        return data

    def clean_url(self):
        url = self.cleaned_data.get('url', None)
        if url:
            if url.find("://") == -1:
                raise forms.ValidationError("You need to specify a protocol (like http://) at the beginning of your url")
        return url


class TextCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/text_creative_form.html'

    class Meta:
        model = TextCreative
        fields = ('headline', 'line1', 'line2') + \
                 ('ad_type', 'name', 'tracking_url', 'url', 'display_url',
                  'format', 'custom_height', 'custom_width', 'landscape',
                  'conv_appid', 'launchpage')


class TextAndTileCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/text_tile_creative_form.html'

    image_url = forms.URLField(verify_exists=False, required=False)
    image_file = forms.FileField(required=False)

    class Meta:
        model = TextAndTileCreative
        fields = ('action_icon', 'color', 'font_color', 'gradient') + \
                 ('line1', 'line2', 'ad_type', 'name', 'tracking_url', 'url',
                  'format', 'custom_height', 'custom_width', 'landscape',
                  'conv_appid', 'launchpage')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', None)

        if instance:
            if instance.image_blob:
                image_url = helpers.get_url_for_blob(instance.image_blob)  # reverse('advertiser_creative_image',kwargs={'creative_key':str(instance.key())})
            else:
                image_url = ''
            if not initial:
                initial = {}
            initial.update(image_url=image_url)
            kwargs.update(initial=initial)
        super(TextAndTileCreativeForm, self).__init__(*args, **kwargs)

    def clean_image_file(self):
        data = self.cleaned_data.get('image_file', None)

        # Check the image file type. We only support png, jpg, jpeg, and gif.
        if data:
            img = self.files.get('image_file', None)
            is_valid_image_type = any([str(img).lower().endswith(ftype) for ftype in ['.png', '.jpeg', '.jpg', '.gif']])
            if not (img and is_valid_image_type):
                extension = get_filetype_extension(img)
                if extension:
                    raise forms.ValidationError('Filetype (.%s) not supported.' % extension)
                else:
                    raise forms.ValidationError('Filetype not supported.')

        # Check to make sure an image file or url was provided.
        # We only need to check this if it's a new form being submitted

        if not self.instance:
            if not (self.cleaned_data.get('image_file', None) or self.cleaned_data.get('image_url', None)):
                raise forms.ValidationError('You must upload an image file for a creative of this type.')

        return data

    def save(self, commit=True):
        obj = super(TextAndTileCreativeForm, self).save(commit=False)
        if self.files.get('image_file', None):
            image_data = self.files.get('image_file').read()
            img = images.Image(image_data)
            fname = files.blobstore.create(mime_type='image/png')
            with files.open(fname, 'a') as f:
                f.write(image_data)
            files.finalize(fname)
            blob_key = files.blobstore.get_blob_key(fname)
            obj.image_blob = blob_key
            obj.image_serve_url = helpers.get_url_for_blob(obj.image_blob)

        if commit:
            obj.put()
        return obj


class HtmlCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/html_creative_form.html'

    class Meta:
        model = HtmlCreative
        fields = ('html_data', 'ormma_html') + \
                 ('ad_type', 'name', 'tracking_url', 'url', 'display_url',
                  'format', 'custom_height', 'custom_width', 'landscape',
                  'conv_appid', 'launchpage')


class ImageCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/image_creative_form.html'

    image_url = forms.URLField(verify_exists=False, required=False)
    image_file = forms.FileField(required=False)

    class Meta:
        model = ImageCreative
        fields = ('ad_type', 'name', 'tracking_url', 'url', 'display_url',
                  'format', 'custom_height', 'custom_width', 'landscape',
                  'conv_appid', 'launchpage')

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', None)

        if instance:
            if instance.image_blob:
                try:
                    image_url = instance.image_serve_url
                except:
                    image_url = None
            else:
                image_url = None
            if not initial:
                initial = {}
            initial.update(image_url=image_url)
            kwargs.update(initial=initial)
        super(ImageCreativeForm, self).__init__(*args, **kwargs)

    def clean_image_file(self):
        data = self.cleaned_data.get('image_file', None)

        # Check the image file type. We only support png, jpg, jpeg, and gif.
        if data:
            img = self.files.get('image_file', None)
            is_valid_image_type = any([str(img).endswith(ftype) for ftype in ['.png', '.jpeg', '.jpg', '.gif']])
            if not (img and is_valid_image_type):
                extension = get_filetype_extension(img)
                if extension:
                    raise forms.ValidationError('Filetype (.%s) not supported.' % extension)
                else:
                    raise forms.ValidationError('Filetype not supported.')

        # Check to make sure an image file or url was provided.
        # We only need to check this if it's a new form being submitted

        if not self.instance:
            if not (self.cleaned_data.get('image_file', None) or self.cleaned_data.get('image_url', None)):
                raise forms.ValidationError('You must upload an image file for a creative of this type.')

        return data

    def save(self, commit=True):
        obj = super(ImageCreativeForm, self).save(commit=False)
        if self.files.get('image_file', None):
            image_data = self.files.get('image_file').read()
            img = images.Image(image_data)
            obj.image_width = img.width
            obj.image_height = img.height

            fname = files.blobstore.create(mime_type='image/png')
            with files.open(fname, 'a') as f:
                f.write(image_data)
            files.finalize(fname)
            blob_key = files.blobstore.get_blob_key(fname)
            obj.image_blob = blob_key
            obj.image_serve_url = helpers.get_url_for_blob(obj.image_blob)
        else:
            commit = False

        if commit:
            obj.put()
        return obj


# Marketplace
LEVELS = (
    ('a', 'Strict - Only allow ads appropriate for family audiences'),
    ('b', 'Moderate - Allow ads for general audiences'),
    ('c', 'Low - Allow ads for mature audiences, including alcohol and dating ads'),
    ('d', 'No filtering - Allow ads including those with provocative or suggestive imagery. MoPub always blocks illegal, pornographic and deceptive ads.'),
    )


class ContentFilterForm(forms.Form):
    level = forms.ChoiceField(choices=LEVELS, widget=forms.RadioSelect)
