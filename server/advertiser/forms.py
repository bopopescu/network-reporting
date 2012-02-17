from __future__ import with_statement

from datetime import datetime
from common.utils.timezones import Pacific_tzinfo

from advertiser.models import Campaign, AdGroup, Creative, \
                              TextCreative, TextAndTileCreative,\
                              HtmlCreative, ImageCreative

from common.constants import (  CITY_GEO,
                                REGION_GEO,
                                COUNTRY_GEO,
                                )
from common.utils import helpers

#THIS ORDER IS VERY IMPORTANT DO NOT CHANGE IT (thanks!)
GEO_LIST = ( COUNTRY_GEO, REGION_GEO, CITY_GEO )

from google.appengine.ext.db import Key

from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from django import forms
from django.forms.util import ErrorList
from django.core.urlresolvers import reverse
from google.appengine.ext import db
from google.appengine.api import images, files
from publisher.models import Site as AdUnit

from budget.query_managers import BudgetQueryManager
from budget.tzinfo import Pacific, UTC, utc
import logging
import re
import urlparse
import cgi

from common.constants import IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES
from widgets import CustomizableSplitDateTimeWidget


def get_filetype_extension(filename):
    if not type(filename) == str:
        filename = str(filename)
    if filename.find('.') >= 0:
        return filename.split('.')[-1]
    return None


class CampaignForm(forms.ModelForm):
    campaign_type = forms.ChoiceField(choices=(('gtee', 'Guaranteed'),
                                               ('promo', 'Promotional'),
                                               ('network', 'Network')),
                                      label='Campaign Type:')
    gtee_priority = forms.ChoiceField(choices=(('high', 'High'),
                                               ('normal', 'Normal'),
                                               ('low', 'Low')),
                                      initial='normal',
                                      label='Priority:',
                                      required=False)
    promo_priority = forms.ChoiceField(choices=(('normal', 'Normal'),
                                                ('backfill', 'Backfill')),
                                       initial='normal',
                                       label='Priority:',
                                       required=False)
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Campaign Name'}))
    description = forms.CharField(label='Description:',
                                  required=False,
                                  widget=forms.Textarea(attrs={'cols': 50,
                                                               'rows': 3,
                                                               'placeholder': 'Campaign for My New App'}))
    start_datetime = forms.DateTimeField(input_formats=(
                                                 '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
                                                 '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
                                                 '%Y-%m-%d',              # '2006-10-25'
                                                 '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
                                                 '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
                                                 '%m/%d/%Y',              # '10/25/2006'
                                                 '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
                                                 '%m/%d/%y %H:%M',        # '10/25/06 14:30'
                                                 '%m/%d/%y',              # '10/25/06'
                                                 '%Y-%m-%d %I:%M:%S %p',  # '2006-10-25 2:30:59 PM'
                                                 '%Y-%m-%d %I:%M %p',     # '2006-10-25 2:30 PM'
                                                 '%m/%d/%Y %I:%M:%S %p',  # '10/25/2006 2:30:59 PM'
                                                 '%m/%d/%Y %I:%M %p',     # '10/25/2006 2:30 PM'
                                                 '%m/%d/%y %I:%M:%S %p',  # '10/25/06 2:30:59 PM'
                                                 '%m/%d/%y %I:%M %p',     # '10/25/06 2:30 PM'
                                             ),
                                         label='Start Time:',
                                         required=False,
                                         widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                            'placeholder': 'MM/DD/YYYY'},
                                                                                time_attrs={'class': 'time',
                                                                                            'placeholder': 'HH:MM'},
                                                                                date_format='%m/%d/%Y',
                                                                                time_format='%H:%M'))
    end_datetime = forms.DateTimeField(input_formats=(
                                           '%Y-%m-%d %H:%M:%S',     # '2006-10-25 14:30:59'
                                           '%Y-%m-%d %H:%M',        # '2006-10-25 14:30'
                                           '%Y-%m-%d',              # '2006-10-25'
                                           '%m/%d/%Y %H:%M:%S',     # '10/25/2006 14:30:59'
                                           '%m/%d/%Y %H:%M',        # '10/25/2006 14:30'
                                           '%m/%d/%Y',              # '10/25/2006'
                                           '%m/%d/%y %H:%M:%S',     # '10/25/06 14:30:59'
                                           '%m/%d/%y %H:%M',        # '10/25/06 14:30'
                                           '%m/%d/%y',              # '10/25/06'
                                           '%Y-%m-%d %I:%M:%S %p',  # '2006-10-25 2:30:59 PM'
                                           '%Y-%m-%d %I:%M %p',     # '2006-10-25 2:30 PM'
                                           '%m/%d/%Y %I:%M:%S %p',  # '10/25/2006 2:30:59 PM'
                                           '%m/%d/%Y %I:%M %p',     # '10/25/2006 2:30 PM'
                                           '%m/%d/%y %I:%M:%S %p',  # '10/25/06 2:30:59 PM'
                                           '%m/%d/%y %I:%M %p',     # '10/25/06 2:30 PM'
                                       ),
                                       label='Stop Time:',
                                       required=False,
                                       widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                          'placeholder': 'MM/DD/YYYY'},
                                                                              time_attrs={'class': 'time',
                                                                                          'placeholder': 'HH:MM'},
                                                                              date_format='%m/%d/%Y',
                                                                              time_format='%H:%M'))
    budget = forms.FloatField(label='Delivery Amount:',
                              required=False,
                              widget=forms.TextInput(attrs={'class': 'float budget_type_dependent daily'}))
    full_budget = forms.FloatField(label='Delivery Amount:',
                                   required=False,
                                   widget=forms.TextInput(attrs={'class': 'float budget_type_dependent full_campaign'}))
    budget_type = forms.ChoiceField(choices=(('daily', 'USD/day'),
                                             ('full_campaign', 'total USD')),
                                    initial='daily')
    budget_strategy = forms.ChoiceField(choices=(('evenly', 'Spread Evenly'),
                                                 ('allatonce', 'All at once')),
                                        label='Delivery Speed:',
                                        initial='evenly',
                                        widget=forms.RadioSelect)

    def __init__(self, *args, **kwargs):
        # a little sketchy...
        instance = args[9] if len(args) > 9 else kwargs.get('instance', None)

        if instance:
            logging.error(instance.campaign_type)
            if 'gtee' in instance.campaign_type:
                if 'high' in instance.campaign_type:
                    instance.gtee_priority = 'high'
                elif 'low' in instance.campaign_type:
                    instance.gtee_priority = 'low'
                instance.campaign_type = 'gtee'
            elif instance.campaign_type == 'backfill_promo':
                instance.campaign_type = 'promo'
                instance.promo_priority = 'backfill'
            logging.error(instance.campaign_type)
            if hasattr(instance, 'gtee_priority'): logging.error(instance.gtee_priority)
            if hasattr(instance, 'promo_priority'): logging.error(instance.promo_priority)

            # convert datetimes from offset-naive UTC to Pacific
            if instance.start_datetime:
                instance.start_datetime = instance.start_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo())
            if instance.end_datetime:
                instance.end_datetime = instance.end_datetime.replace(tzinfo=UTC()).astimezone(Pacific_tzinfo())

        super(forms.ModelForm, self).__init__(*args, **kwargs)

        # hack to make the forms ordered correctly
        # TODO: fix common.utils.djangoforms.ModelForm to conform to
        # https://docs.djangoproject.com/en/1.2/topics/forms/modelforms/#changing-the-order-of-fields
        self.fields.keyOrder = self.Meta.fields

    def clean_start_datetime(self):
        start_datetime = self.cleaned_data.get('start_datetime', None)
        if start_datetime:
            # start_datetime is entered in Pacific Time
            start_datetime = start_datetime.replace(tzinfo=Pacific_tzinfo()).astimezone(UTC()).replace(tzinfo=None)
            # if this is a new campaign, it must start in the future
            if not self.instance and start_datetime < datetime.now():
                raise forms.ValidationError("Start time must be in the future")
        return start_datetime

    def clean_end_datetime(self):
        end_datetime = self.cleaned_data.get('end_datetime', None)
        if end_datetime:
            # end_datetime is entered in Pacific Time
            end_datetime = end_datetime.replace(tzinfo=Pacific_tzinfo()).astimezone(UTC()).replace(tzinfo=None)
        return end_datetime

    def clean(self):
        cleaned_data = super(CampaignForm, self).clean()

        start_datetime = cleaned_data.get('start_datetime', None)
        end_datetime = cleaned_data.get('end_datetime', None)

        if cleaned_data.get('campaign_type', None) in ['gtee', 'promo'] and not start_datetime:
            # if no start time is given, use the current time
            start_datetime = datetime.now()

        if 'campaign_type' in cleaned_data:
            # set the correct campaign_type using gtee_prioirty or promo_priority
            if cleaned_data['campaign_type'] == 'gtee':
                if cleaned_data.get('gtee_priority', None):
                    gtee_priority = cleaned_data['gtee_priority']
                    if gtee_priority == 'low':
                        cleaned_data['campaign_type'] = 'gtee_low'
                    elif gtee_priority == 'high':
                        cleaned_data['campaign_type'] = 'gtee_high'
                else:
                    if 'gtee_priority' not in self._errors:
                        self._errors['gtee_priority'] = ErrorList()
                    self._errors['gtee_priority'].append('This field is required')
            elif cleaned_data['campaign_type'] == 'promo':
                if cleaned_data.get('promo_priority', None):
                    if cleaned_data['promo_priority'] == 'backfill':
                        cleaned_data['campaign_type'] = 'backfill_promo'
                else:
                    if 'promo_priority' not in self._errors:
                        self._errors['promo_priority'] = ErrorList()
                    self._errors['promo_priority'].append('This field is required')

        if cleaned_data.get('budget_type', None):
            if cleaned_data['budget_type'] == 'daily':
                cleaned_data['full_budget'] = None
            else:
                cleaned_data['budget'] = None

        if start_datetime and end_datetime and end_datetime < start_datetime:
            if 'end_datetime' not in self._errors:
                self._errors['end_datetime'] = ErrorList()
            self._errors['end_datetime'].append("Stop time must be after start time")

        return cleaned_data

    # It is not standard to override a ModelForm's save method, but we need to
    # change the tzinfo of the datetimes because we display in Pacific and
    # store in UTC.  Can this be done in the model?
    def save(self, *args, **kwargs):
        campaign = super(CampaignForm, self).save(*args, **kwargs)

        # budget
        budget_obj = BudgetQueryManager.update_or_create_budget_for_campaign(campaign)
        campaign.budget_obj = budget_obj

        return campaign

    # TODO: doesn't work with djangoforms
    class Media:
        js = ('campaign_adgroup_form.js',)

    class Meta:
        model = Campaign
        fields = ('campaign_type',
                  'gtee_priority',
                  'promo_priority',
                  'name',
                  'description',
                  'start_datetime',
                  'end_datetime',
                  'budget',
                  'budget_type',
                  'budget_strategy')


class AdGroupForm(forms.ModelForm):
    network_type = forms.ChoiceField(choices=(('admob_native', 'AdMob'),
                                              ('adsense', 'AdSense'),
                                              ('brightroll', 'BrightRoll'),
                                              ('ejam', 'TapIt'),
                                              ('iAd', 'iAd'),
                                              ('inmobi', 'InMobi'),
                                              ('jumptap', 'Jumptap'),
                                              ('millennial_native', 'Millennial Media'),
                                              ('mobfox', 'MobFox'),
                                              ('custom', 'Custom Network'),
                                              ('custom_native', 'Custom Native Network')),
                                     label='Network Type:', required=False)
    custom_html = forms.CharField(label='Custom HTML:', required=False,
                                  widget=forms.Textarea(attrs={'placeholder': 'HTML Custom Content',
                                                               'rows': 3}))
    custom_method = forms.CharField(label='Custom Method:', required=False,
                                    widget=forms.TextInput(attrs={'placeholder': 'loadNativeSDK:'}))
    bid_strategy = forms.ChoiceField(choices=(('cpm', 'CPM'), ('cpc', 'CPC')),
                                     label='Rate:', initial='cpc')
    bid = forms.FloatField(initial=0.05,
                           widget=forms.TextInput(attrs={'class': 'float'}))
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
    region_targeting = forms.ChoiceField(choices=(('all', 'Everywhere'),
                                                  ('city', 'City')),
                                         initial='all',
                                         label='Region Targeting:',
                                         widget=forms.RadioSelect)
    #geo_predicates
    cities = forms.Field(required=False, widget=forms.SelectMultiple)
    keywords = forms.CharField(required=False,
                               widget=forms.Textarea(attrs={'cols': 50,
                                                            'rows': 3}))

    def coerce_network_state(optimize):
        if optimize:
            return NetworkStates.OPTIMIZED_NETWORK_ADGROUP
        else:
            return NetworkStates.NETWORK_ADGROUP

    network_state = forms.TypedChoiceField(coerce=coerce_network_state,
                                              initial=False,
                                              label='Optimize:',
                                              widget=forms.CheckboxInput)

    def __init__(self, *args, **kwargs):
        #data = args[0] if len(args) > 0 else kwargs.get('data', None)
        #initial = args[4] if len(args) > 4 else kwargs.get('initial', None)
        instance = args[8] if len(args) > 8 else kwargs.get('instance', None)

        is_staff = kwargs.pop('is_staff', False)

        # allows us to set choices on instantiation
        site_keys = kwargs.pop('site_keys', [])

        super(forms.ModelForm, self).__init__(*args, **kwargs)

        if is_staff or (instance and instance.network_type == 'admob'):
            self.fields['network_type'].choices.append(('admob', 'AdMob Javascript (deprecated)'))

        if is_staff or (instance and instance.network_type == 'millennial'):
            self.fields['network_type'].choices.append(('millennial', 'Millennial Server-side (deprecated)'))

        if is_staff or (instance and instance.network_type == 'greystripe'):
            self.fields['network_type'].choices.append(('greystripe', 'GreyStripe (deprecated)'))

        self.fields['site_keys'] = forms.MultipleChoiceField(choices=site_keys, required=False)

        # hack to make the forms ordered correctly
        # TODO: fix common.utils.djangoforms.ModelForm to conform to
        # https://docs.djangoproject.com/en/1.2/topics/forms/modelforms/#changing-the-order-of-fields
        self.fields.keyOrder = self.Meta.fields

    def clean_allocation_percentage(self):
        allocation_percentage = self.cleaned_data.get('allocation_percentage', None)
        if (not isinstance(allocation_percentage, int) and
            not isinstance(allocation_percentage, float)):
            allocation_percentage = 100
        return allocation_percentage

    def clean(self):
        cleaned_data = super(AdGroupForm, self).clean()
        # don't store targeted cities unless region targeting for cities is selected
        if cleaned_data.get('region_targeting', None) != 'city':
            cleaned_data['cities'] = []
        if cleaned_data.get('site_keys', []):
            cleaned_data['site_keys'] = [Key(site_key) for site_key in cleaned_data['site_keys']]
        return cleaned_data

    class Meta:
        model = AdGroup
        fields = ('name',
                  'network_type',
                  'custom_html',
                  'custom_method',
                  'bid_strategy',
                  'bid',
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
        data = self.cleaned_data.get('name', None)
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
        super(TextAndTileCreativeForm,self).__init__(*args,**kwargs)

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

    def save(self,commit=True):
        obj = super(TextAndTileCreativeForm,self).save(commit=False)
        if self.files.get('image_file',None):
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
                 ('ad_type','name','tracking_url','url','display_url','format',
                  'custom_height','custom_width','landscape', 'conv_appid',
                  'launchpage')

class ImageCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/image_creative_form.html'

    image_url = forms.URLField(verify_exists=False,required=False)
    image_file = forms.FileField(required=False)

    class Meta:
        model = ImageCreative
        fields = ('ad_type','name','tracking_url','url','display_url','format',
                  'custom_height','custom_width','landscape', 'conv_appid',
                  'launchpage')

    def __init__(self, *args,**kwargs):
        instance = kwargs.get('instance',None)
        initial = kwargs.get('initial',None)

        if instance:
            if instance.image_blob:
                try:
                    image_url = helpers.get_url_for_blob(instance.image_blob)
                except:
                    image_url = None
            else:
                image_url = None
            if not initial:
                initial = {}
            initial.update(image_url=image_url)
            kwargs.update(initial=initial)
        super(ImageCreativeForm,self).__init__(*args,**kwargs)

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
        obj = super(ImageCreativeForm,self).save(commit=False)
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
    ('d', 'No filtering - Allow ads including those with provocative or suggestive imagery. MoPub always blocks illegal or deceptive ads.'),
    )

from django.forms.widgets import RadioSelect

class ContentFilterForm(forms.Form):
    level = forms.ChoiceField(choices = LEVELS, widget = RadioSelect)
