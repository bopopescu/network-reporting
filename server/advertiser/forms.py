from __future__ import with_statement
from datetime import datetime
import re

from django import forms
from django.forms.util import ErrorList
from django.utils.safestring import SafeString
from google.appengine.api import images, files
from google.appengine.ext.db import Key

from advertiser.models import (Order, LineItem, Creative, TextAndTileCreative,
                               ImageCreative, HtmlCreative)
from common.constants import (IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES,
                              CITY_GEO, REGION_GEO, COUNTRY_GEO)

from common.utils import helpers
from common.utils.timezones import Pacific_tzinfo
from common.utils.date_magic import utc_to_pacific, pacific_to_utc
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

from advertiser.widgets import CustomizableSplitDateTimeWidget


class OrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # TODO: figure out if there is a less hacky way to get this
        instance = args[9] if len(args) > 9 else kwargs.get('instance', None)

        if instance and not instance.is_order:
            # TODO: figure out what type of exception this should really be, ValueError?
            raise Exception("Campaign instance must be an order.")

        super(forms.ModelForm, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        order = super(forms.ModelForm, self).save(*args, **kwargs)

        # TODO: this is dumb, do something else
        order.is_order = True
        order.save()

        return order

    class Meta:
        model = Order
        fields = ('name',
                  'advertiser',
                  'description')


class LineItemForm(forms.ModelForm):
    # TODO: include campaign and confirm campaign.is_order
    adgroup_type   = forms.ChoiceField(label='Line Item Type:',
                                       choices=(('gtee', 'Guaranteed'),
                                                ('promo', 'Promotional')))

    gtee_priority  = forms.ChoiceField(label='Priority:', initial='normal',
                                       choices=(('high', 'High'),
                                                ('normal', 'Normal'),
                                                ('low', 'Low')),
                                       required=False)

    promo_priority = forms.ChoiceField(label='Priority:', initial='normal',
                                       choices=(('normal', 'Normal'),
                                                ('backfill', 'Backfill')),
                                       required=False)

    start_datetime = forms.DateTimeField(label='Start Time:', required=False,
                                         input_formats=('%m/%d/%Y %I:%M %p', '%m/%d/%Y %H:%M'),
                                         widget=CustomizableSplitDateTimeWidget(date_attrs={
                                                                                             'class': 'date',
                                                                                             'placeholder': 'MM/DD/YYYY'
                                                                                            },
                                                                                time_attrs={
                                                                                             'class': 'time',
                                                                                             'placeholder': 'HH:MM'
                                                                                            },
                                                                                date_format='%m/%d/%Y',
                                                                                time_format='%I:%M %p'))
    end_datetime  = forms.DateTimeField(label='Stop Time:', required=False,
                                        input_formats=('%m/%d/%Y %I:%M %p', '%m/%d/%Y %H:%M'),
                                        widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                          'placeholder': 'MM/DD/YYYY'},
                                                                              time_attrs={'class': 'time',
                                                                                          'placeholder': 'HH:MM'},
                                                                              date_format='%m/%d/%Y',
                                                                              time_format='%I:%M %p'))


    bid_strategy    = forms.ChoiceField(label='Rate:',
                                        choices=(('cpm', 'CPM'),
                                                 ('cpc', 'CPC')))

    budget          = forms.FloatField(label='Budget:', required=False,
                                       widget=forms.TextInput(attrs={'class': 'float'}))

    budget_type     = forms.ChoiceField(initial='daily',
                                        choices=(('daily', 'USD/day'),
                                                 ('full_campaign', 'total USD')),
                                        required=False)

    budget_strategy = forms.ChoiceField(label='Delivery Speed:', initial='allatonce',
                                        choices=(('evenly', 'Spread Evenly'),
                                                 ('allatonce', 'All at once')),
                                        required=False,
                                        widget=forms.RadioSelect)

    # site_keys defined in __init__

    daily_frequency_cap   = forms.IntegerField(label='Frequency Caps:', initial=0,
                                               required=False,
                                               widget=forms.TextInput(attrs={'class': 'float'}))
    hourly_frequency_cap  = forms.IntegerField(initial=0, required=False,
                                               widget=forms.TextInput(attrs={'class': 'float'}))

    device_targeting = forms.TypedChoiceField(label='Device Targeting:', initial=False,
                                              choices=(('0', 'All'),
                                                       ('1', 'Filter by device and OS')),
                                              coerce=lambda x: bool(int(x)),
                                              required=False,
                                              widget=forms.RadioSelect)

    ios_version_min = forms.ChoiceField(label='Min', choices=IOS_VERSION_CHOICES[1:],
                                        required=False)
    ios_version_max = forms.ChoiceField(label='Max', choices=IOS_VERSION_CHOICES,
                                        required=False)

    android_version_min = forms.ChoiceField(label='Min', choices=ANDROID_VERSION_CHOICES[1:],
                                            required=False)
    android_version_max = forms.ChoiceField(label='Max', choices=ANDROID_VERSION_CHOICES,
                                            required=False)


    region_targeting = forms.ChoiceField(label='Region Targeting:', initial='all',
                                         choices=(('all', 'Everywhere'),
                                                  ('city', 'City')),
                                         required=False,
                                         widget=forms.RadioSelect)


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
            # TODO: make sure you cannot change adgroup_type except for priority
            # gtee
            if 'gtee' in instance.adgroup_type:
                self._init_gtee_line_item(instance, initial)

            elif instance.adgroup_type == 'backfill_promo':
                initial['adgroup_type'] = 'promo'
                initial['promo_priority'] = 'backfill'

            if instance.start_datetime:
                initial['start_datetime'] = utc_to_pacific(instance.start_datetime)
            if instance.end_datetime:
                initial['end_datetime'] = utc_to_pacific(instance.end_datetime)

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

    def _init_gtee_line_item(self, instance, initial):
        if 'high' in instance.adgroup_type:
            initial['gtee_priority'] = 'high'
        elif 'low' in instance.adgroup_type:
            initial['gtee_priority'] = 'low'
        initial['adgroup_type'] = 'gtee'

        if instance.budget_type == 'daily':
            initial['budget'] = instance.daily_budget
        else:
            initial['budget'] = instance.full_budget

        if initial['budget'] != None and instance.bid_strategy == 'cpm':
            initial['budget'] = int(1000.0 * initial['budget'] / instance.bid)

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
            start_datetime = pacific_to_utc(start_datetime)
        return start_datetime

    def clean_end_datetime(self):
        # TODO: not change the end date after a campaign has completed
        end_datetime = self.cleaned_data.get('end_datetime', None)
        if end_datetime:
            # end_datetime is entered in Pacific Time
            end_datetime = pacific_to_utc(end_datetime)
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
            # the number of predicates indicates the granularity of targting
            granularity = (COUNTRY_GEO, REGION_GEO, CITY_GEO)[len(geo_predicate) - 1]
            geo_predicates.append(granularity % geo_predicate)
        return geo_predicates

    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords', None)
        if keywords:
            if len(keywords) > 500:
                raise forms.ValidationError('Maximum 500 characters for keywords.')
        return keywords

    def _clean_start_and_end_datetime(self, data):
        start = data.get('start_datetime') or datetime.now()
        data['start_datetime'] = start
        end = data.get('end_datetime')
        if end and end <= start:
            self._errors['end_datetime'] = ErrorList()
            self._errors['end_datetime'].append("Stop time must \
                                                be after start time")

    def _clean_gtee_adgroup_type(self, data):
        priority = data.get('gtee_priority')
        if not priority:
            self._errors['gtee_priority'] = ErrorList()
            self._errors['gtee_priority'].append('This field is required')
        elif priority in ['low', 'high']:
            data['adgroup_type'] = 'gtee_%s' % priority

    def _clean_gtee_budget(self, data):
        budget = data.get('budget')
        if not budget:
            data['daily_budget'] = None
            data['full_budget'] = None
            return

        for field in ['bid_strategy', 'bid', 'budget_type', 'budget_strategy']:
            if not data.get(field):
                self._errors[field] = ErrorList()
                self._errors[field].append('This field is required')
                return

        if data['budget_type'] == 'daily':
            data['daily_budget'] = self._calculate_budget(budget)
            data['full_budget'] = None
        else:
            if not data['end_datetime'] and (data['budget_strategy'] != 'allatonce'):
                self._errors['budget_strategy'] = ErrorList()
                self._errors['budget_strategy'].append('Delivery speed \
                                                       must be all at once \
                                                       for total budget \
                                                       with no stop time')
            data['full_budget'] = self._calculate_budget(budget)
            data['daily_budget'] = None

    def _clean_promo_adgroup_type(self, data):
        priority = data.get('promo_priority')
        if not priority:
            self._errors['promo_priority'] = ErrorList()
            self._errors['promo_priority'].append('This field is required')
        elif priority == 'backfill':
            data['adgroup_type'] = 'backfill_promo'

    def _clean_promo_budget(self, data):
        data['daily_budget'] = None
        data['full_budget'] = None
        data['budget_type'] = None
        data['budget_strategy'] = None

    def _clean_targeted_cities(self, data):
        if data.get('region_targeting') != 'city':
            data['cities'] = []

    def clean(self):
        cleaned_data = super(LineItemForm, self).clean()

        self._clean_start_and_end_datetime(cleaned_data)

        if cleaned_data['adgroup_type'] == 'gtee':
            self._clean_gtee_adgroup_type(cleaned_data)
            self._clean_gtee_budget(cleaned_data)

        elif cleaned_data['adgroup_type'] == 'promo':
            self._clean_promo_adgroup_type(cleaned_data)
            self._clean_promo_budget(cleaned_data)

        self._clean_targeted_cities(cleaned_data)

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
    name          = forms.CharField(label='Creative Name:', initial='Creative',
                                    widget=forms.TextInput(attrs={'class': 'required'}))

    format        = forms.ChoiceField(label='Format:', initial='320x50',
                                      choices=(('320x50', '320 x 50 (Banner)'),
                                               ('300x250', '300 x 250 (MRect)'),
                                               ('full', 'Phone Full Screen'),
                                               ('728x90', '728 x 90 (Tablet Leaderboard)'),
                                               ('160x600', '160 x 600 (Tablet Skyscraper)'),
                                               ('full_tablet', 'Tablet Full Screen'),
                                               ('custom', 'Custom')))
    landscape     = forms.BooleanField(label='Landscape:', required=False)


    custom_width  = forms.IntegerField(label='Custom Size:', required=False,
                                       widget=forms.TextInput(attrs={'class': 'number'}))
    custom_height = forms.IntegerField(required=False,
                                       widget=forms.TextInput(attrs={'class': 'number'}))

    ad_type       = forms.ChoiceField(label='Creative Type:', initial='image',
                                      choices=(('image', 'Image'),
                                               ('text_icon', 'Text and Tile'),
                                               ('html', 'HTML')),
                                      widget=forms.RadioSelect)

    url           = forms.URLField(label='Click URL:', required=False)
    launchpage    = forms.URLField(label='Intercept URL:', required=False)
    tracking_url  = forms.URLField(label='Impression Tracking URL:', required=False)

    conv_appid    = forms.CharField(label='Conversion Tracking ID:', required=False)

    def _get_appid(self, url):
        pattern = ''
        if 'itunes' in url:
            # itunes url
            # http://itunes.apple.com/il/app/imosaic-project/id335853048?mt=8
            # in this case: 335853048
            pattern = re.compile("http://itunes\.apple\.com.*id(\d+)")
        elif 'phobos' in url:
            # old phobos urls
            # http://phobos.apple.com/WebObjects/MZStore.woa/wa/viewSoftware?id=386584429&mt=8
            pattern = re.compile("http://phobos\.apple\.com.*id=(\d+)")
        else:
            # market://details?id=com.example.admob.lunarlander
            # in this case: com.example.admob.lunarlander
            # NOTE: there can not be any other characters after the id
            pattern = re.compile("market://.*id\=(.+)$")

        match = pattern.search(url)
        if match:
            store_id = match.group(1)
            return store_id

        return None

    def clean_name(self):
        return self.cleaned_data.get('name', '').strip()

    def clean_url(self):
        url = self.cleaned_data.get('url', None)
        if url:
            if url.find("://") == -1:
                raise forms.ValidationError("You need to specify a protocol \
                                            (like http://) at the beginning of your url")
        return url

    def clean_image_file(self):
        data = self.cleaned_data.get('image_file', None)

        # Check the image file type. We only support png, jpg, jpeg, and gif.
        if data:
            img = self.files.get('image_file', None)
            is_valid_image_type = any([str(img).endswith(ftype) for ftype in ['.png', '.jpeg',
                                                                              '.jpg', '.gif']])
            if not (img and is_valid_image_type):
                extension = _get_filetype_extension(img)
                if extension:
                    raise forms.ValidationError('Filetype (.%s) not supported.' % extension)
                else:
                    raise forms.ValidationError('Filetype not supported.')

        # Check to make sure an image file or url was provided.
        # We only need to check this if it's a new form being submitted

        if not self.instance:
            if not (self.cleaned_data.get('image_file', None) or \
                    self.cleaned_data.get('image_url', None)):
                raise forms.ValidationError('You must upload an image file \
                                            for a creative of this type.')

        return data

    def _save_image_file(self, obj):
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


# TODO: fix so there are no repeated definition of form fields.  Is something
#       weird with ModelForm inheritance?
class NewCreativeForm(AbstractCreativeForm):
    # text_icon
    line1       = forms.CharField(label='Line 1:', required=False)
    line2       = forms.CharField(label='Line 2:', required=False)

    # image text_icon
    image_file  = forms.FileField(label='Image File:', required=False)

    # text_icon
    action_icon = forms.ChoiceField(label='Action Icon:', initial='download_arrow4',
                                    choices=(('download_arrow4', SafeString('<img src="/images/download_arrow4.png" width="40" height="40"/>')),
                                             ('access_arrow', SafeString('<img src="/images/access_arrow.png" width="40" height="40"/>')),
                                             ('none', 'None')),
                                    widget=forms.RadioSelect)

    color       = forms.Field(label='Background Color:', initial='000000')
    font_color  = forms.Field(label='Font Color:', initial='FFFFFF')
    gradient    = forms.BooleanField(label='Gradient:', initial=True)

    # html
    html_data   = forms.CharField(label='HTML Body:', required=False,
                                  widget=forms.Textarea(attrs={
                                                                'placeholder': 'HTML Body Content',
                                                                'rows': 10
                                                               }))
    ormma_html  = forms.BooleanField(label='MRAID Ad:', required=False)

    class Meta:
        model = Creative
        fields = ('format', 'custom_width', 'custom_height', 'landscape',
                  'ad_type', 'name', 'url', 'launchpage', 'conv_appid',
                  'tracking_url', 'line1', 'line2', 'image_file', 'action_icon',
                  'color', 'font_color', 'gradient', 'html_data', 'ormma_html')


class ImageCreativeForm(AbstractCreativeForm):
    image_file = forms.FileField(label='Image File:', required=False)

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

    def save(self, commit=True):
        # TODO: repeated code
        obj = super(ImageCreativeForm, self).save(commit=False)

        if self.files.get('image_file'):
            self._save_image_file(obj)
        else:
            commit = False

        if not obj.conv_appid and obj.url:
            obj.conv_appid = self._get_appid(obj.url)

        if commit:
            obj.put()

        return obj

    class Meta():
        model = ImageCreative
        fields = ('format', 'custom_width', 'custom_height', 'landscape',
                  'ad_type', 'name', 'url', 'launchpage', 'conv_appid',
                  'tracking_url', 'image_file')


class TextAndTileCreativeForm(AbstractCreativeForm):
    line1 = forms.CharField(label='Line 1:', required=False)
    line2 = forms.CharField(label='Line 2:', required=False)

    image_file  = forms.FileField(label='Image File:', required=False)

    action_icon = forms.ChoiceField(label='Action Icon:', initial='download_arrow4',
                                    choices=(('download_arrow4', SafeString('<img src="/images/download_arrow4.png" width="40" height="40"/>')),
                                             ('access_arrow', SafeString('<img src="/images/access_arrow.png" width="40" height="40"/>')),
                                             ('none', 'None')),
                                    widget=forms.RadioSelect)

    color       = forms.Field(label='Background Color:', initial='000000')
    font_color  = forms.Field(label='Font Color:', initial='FFFFFF')
    gradient    = forms.BooleanField(label='Gradient:', initial=True)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', None)

        if instance:
            if instance.image_blob:
                image_url = helpers.get_url_for_blob(instance.image_blob)
            else:
                image_url = ''
            if not initial:
                initial = {}
            initial.update(image_url=image_url)
            kwargs.update(initial=initial)

        super(TextAndTileCreativeForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # TODO: repeated code
        obj = super(TextAndTileCreativeForm, self).save(commit=False)

        if self.files.get('image_file'):
            self._save_image_file(obj)

        if not obj.conv_appid and obj.url:
            obj.conv_appid = self._get_appid(obj.url)

        if commit:
            obj.put()

        return obj

    class Meta:
        model = TextAndTileCreative
        fields = ('format', 'custom_width', 'custom_height', 'landscape',
                  'ad_type', 'name', 'url', 'launchpage', 'conv_appid',
                  'tracking_url', 'line1', 'line2', 'image_file', 'action_icon',
                  'color', 'font_color', 'gradient')


class HtmlCreativeForm(AbstractCreativeForm):
    html_data  = forms.CharField(label='HTML Body:', required=False,
                                widget=forms.Textarea(attrs={
                                                              'placeholder': 'HTML Body Content',
                                                              'rows': 10
                                                             }))
    ormma_html = forms.BooleanField(label='MRAID Ad:', required=False)

    def save(self, commit=True):
        # TODO: repeated code
        obj = super(HtmlCreativeForm, self).save(commit=False)

        if not obj.conv_appid and obj.url:
            obj.conv_appid = self._get_appid(obj.url)

        if commit:
            obj.put()

        return obj

    class Meta:
        model = HtmlCreative
        fields = ('format', 'custom_width', 'custom_height', 'landscape',
                  'ad_type', 'name', 'url', 'launchpage', 'conv_appid',
                  'tracking_url', 'html_data', 'ormma_html')


# Marketplace
LEVELS = (
          ('a', 'Strict - Only allow ads appropriate for family audiences'),
          ('b', 'Moderate - Allow ads for general audiences'),
          ('c', 'Low - Allow ads for mature audiences, including alcohol and dating ads'),
          ('d', 'No filtering - Allow ads including those with provocative or suggestive imagery. \
                 MoPub always blocks illegal, pornographic and deceptive ads.')
          )


class ContentFilterForm(forms.Form):
    level = forms.ChoiceField(choices=LEVELS, widget=forms.RadioSelect)


def _get_filetype_extension(filename):
    if not type(filename) == str:
        filename = str(filename)
    if filename.find('.') >= 0:
        return filename.split('.')[-1]
    return None
