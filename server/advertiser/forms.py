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

from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from django import forms
from django.core.urlresolvers import reverse
from google.appengine.ext import db
from google.appengine.api import images, files
from publisher.models import Site as AdUnit

from budget.query_managers import BudgetQueryManager
from budget.tzinfo import Pacific, utc
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


"""
class CampaignForm(mpforms.MPModelForm):
    TEMPLATE = 'advertiser/forms/campaign_form.html'
    gtee_level = forms.Field(widget = forms.Select)
    promo_level = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget)
    mpx_level = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget, required=False)
    budget_strategy = mpfields.MPChoiceField(choices=[('evenly','Spread evenly'),('allatonce','All at once')],widget=mpwidgets.MPRadioWidget)
    budget_type = mpfields.MPChoiceField(choices=[('daily','Daily'),('full_campaign','Full Campaign')],widget=mpwidgets.MPSelectWidget)
    price_floor = mpfields.MPTextField(required=False, initial="0.25")
    start_time = mpfields.MPTextField(required=False)
    end_time = mpfields.MPTextField(required=False)

    #priority is now based off of campaign_type, not actually priority
    #gtee has 3 levels, this makes it so the database understands the three different levels of gtee
    #but the form sees one level of gtee and three levels of priority
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        if instance and instance.campaign_type:

            #Take datetimes from UTC to PST/PDT
            if instance.start_datetime:
                initial.update(start_datetime = instance.start_datetime.replace(tzinfo=utc).astimezone(Pacific))
            if instance.end_datetime:
                initial.update(end_datetime = instance.end_datetime.replace(tzinfo=utc).astimezone(Pacific))
            kwargs.update(initial=initial)

            # Set up camaign type
            vals = instance.campaign_type.split('_')
            if 'gtee' in vals:
                type_ = 'gtee'
                if 'high' in vals:
                    level = 'high'
                elif 'low' in vals:
                    level = 'low'
                else:
                    level = 'normal'
                if not initial:
                    initial = {}
                initial.update(campaign_type=type_)
                initial.update(gtee_level=level)
                kwargs.update(initial=initial)
            if 'promo' in vals:
                type_ = 'promo'
                if 'backfill' in vals:
                    level = 'backfill'
                else:
                    level = 'normal'
                initial.update(campaign_type=type_)
                initial.update(promo_level=level)
                kwargs.update(initial=initial)

            if 'marketplace' in vals:
                type_ = 'marketplace'
                if 'backfill' in vals:
                    level = 'backfill'
                else:
                    level = 'normal'
                initial.update(campaign_type=type_)
                initial.update(mpx_level=level)
                kwargs.update(initial=initial)
        super(CampaignForm, self).__init__(*args, **kwargs)

    #same as above, but so the one level of gtee and 3 levels of prioirty
    #get correctly merged into a single datastore field
    def save(self, commit=True):
        obj = super(CampaignForm, self).save(commit=False)
        if obj:
            start_time = self.cleaned_data['start_time']
            end_time = self.cleaned_data['end_time']
            start_date = self.cleaned_data['start_date']
            end_date = self.cleaned_data['end_date']
            fmt = '%I:%M %p'

            type_ = self.cleaned_data['campaign_type']
            if type_ == 'gtee':
                lev = self.cleaned_data['gtee_level']
                if lev == 'high':
                    type_ = 'gtee_high'
                elif lev == 'low':
                    type_ = 'gtee_low'
                elif lev == 'normal':
                    type_ = 'gtee'
                else:
                    logging.warning("Invalid gtee_level for gtee")
                obj.campaign_type = type_
            elif type_ == 'promo':
                lev = self.cleaned_data['promo_level']
                if lev == 'normal':
                    pass
                elif lev == 'backfill':
                    type_ = 'backfill_promo'
                else:
                    logging.warning("Invalid promo level")
                obj.campaign_type = type_
            elif type_ == 'marketplace':
                lev = self.cleaned_data['mpx_level']
                if lev == 'normal':
                    type_ = 'marketplace'
                elif lev == 'backfill':
                    type_ = 'backfill_marketplace'
                else:
                    type_ = 'marketplace'
                obj.campaign_type = type_
            if obj.budget_type == "full_campaign":
                obj.budget = None
            else:
                obj.full_budget = None


            # HACK:
            # Network campaigns don't use the date/time fields. Some foreign customers
            # were experiencing issues because date/time fields are formatted
            # differently in the browser and django would mark them invalid.
            # They're hidden fields in the form, so the error would never show
            # up. For network campaigns, we're just setting them to None as a quick
            # fix. See #603 in lighthouse for more.
            if not type_ in ('gtee', 'gtee_high', 'gtee_low', 'promo'):
                start_datetime = None
                start_datetime_time = None

            elif start_time and start_date:
                start_datetime_time = datetime.strptime(start_time, fmt)
                start_datetime = datetime(start_date.year,
                                          start_date.month,
                                          start_date.day,
                                          start_datetime_time.hour,
                                          start_datetime_time.minute,
                                          tzinfo=Pacific)

            else:
                start_datetime_time = datetime.today()
                start_datetime = datetime.today()

            if end_date and end_time:
                end_datetime_time = datetime.strptime(end_time, fmt)
                end_datetime = datetime(end_date.year,
                                        end_date.month,
                                        end_date.day,
                                        end_datetime_time.hour,
                                        end_datetime_time.minute,
                                        tzinfo=Pacific)
            else:
                end_datetime = None

            # Remove start/end date
            obj.end_date = None
            obj.start_date = None
            # Set the shizz
            obj.start_datetime = start_datetime
            obj.end_datetime = end_datetime


        if commit:
            obj.put()
        return obj

    class Meta:
      model = Campaign
      fields = ('name',
                'budget_strategy',
                'budget_type',
                'full_budget',
                'description',
                'budget',
                'campaign_type',
                'start_date',
                'end_date',
                'gtee_level',
                'promo_level',
                'start_time',
                'end_time',
                'start_datetime',
                'end_datetime')
"""


class CampaignForm(forms.ModelForm):
    campaign_type = forms.ChoiceField(choices=(('gtee', 'Guaranteed'),
                                               ('promo', 'Promotional'),
                                               ('network', 'Network')),
                                      label='Campaign Type:')
    gtee_priority = forms.ChoiceField(choices=(('high', 'High'),
                                               ('normal', 'Normal'),
                                               ('low', 'Low')),
                                      initial='normal',
                                      label='Priority:')
    promo_priority = forms.ChoiceField(choices=(('normal', 'Normal'),
                                                ('backfill', 'Backfill')),
                                       initial='normal',
                                       label='Priority:')
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Campaign Name'}))
    description = forms.CharField(label='Description:',
                                  required=False,
                                  widget=forms.Textarea(attrs={'cols': 50,
                                                               'rows': 3,
                                                               'placeholder': 'Campaign for My New App'}))
    start_datetime = forms.DateTimeField(label='Start Time:',
                                         required=False,
                                         widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                            'placeholder': 'MM/DD/YYYY'},
                                                                                time_attrs={'class': 'time',
                                                                                            'placeholder': 'HH:MM'},
                                                                                date_format='%m/%d/%Y',
                                                                                time_format='%H:%M'))
    end_datetime = forms.DateTimeField(label='Stop Time:',
                                       required=False,
                                       widget=CustomizableSplitDateTimeWidget(date_attrs={'class': 'date',
                                                                                          'placeholder': 'MM/DD/YYYY'},
                                                                              time_attrs={'class': 'time',
                                                                                          'placeholder': 'HH:MM'},
                                                                              date_format='%m/%d/%Y',
                                                                              time_format='%H:%M'))
    budget = forms.FloatField(label='Delivery Amount:',
                              required=False,
                              widget=forms.TextInput(attrs={'class': 'number'}))
    budget_type = forms.ChoiceField(choices=(('daily', 'USD/day'),
                                             ('full_campaign', 'total USD')),
                                    initial='daily')
    budget_strategy = forms.ChoiceField(choices=(('evenly', 'Spread Evently'),
                                                 ('allatonce', 'All at once')),
                                        label='Delivery Speed:',
                                        initial='evenly',
                                        widget=forms.RadioSelect())
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        # hack to make the forms ordered correctly
        # TODO: fix common.utils.djangoforms.ModelForm to conform to
        # https://docs.djangoproject.com/en/1.2/topics/forms/modelforms/#changing-the-order-of-fields
        self.fields.keyOrder = self.Meta.fields
    def clean_start_datetime(self):
        logging.error(self.cleaned_data['start_datetime'])
        # if no start time is given, use the current time
        if not self.cleaned_data['start_datetime']:
            self.cleaned_data['start_datetime'] = datetime.now(Pacific_tzinfo())
        return self.cleaned_data['start_datetime']
    def clean(self):
        logging.error(self.cleaned_data['start_datetime'])
        # set the correct campaign_type using gtee_prioirty or promo_priority
        if self.cleaned_data['campaign_type'] == 'gtee':
            if self.cleaned_data['gtee_priority'] == 'low':
                self.cleaned_data['campaign_type'] = 'gtee_low'
            elif self.cleaned_data['gtee_priority'] == 'high':
                self.cleaned_data['campaign_type'] = 'gtee_high'
        elif self.cleaned_data['campaign_type'] == 'promo' and self.cleaned_data['promo_priority'] == 'backfill':
            self.cleaned_data['campaign_type'] == 'backfill_promo'
        return self.cleaned_data
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


"""
class DirectSoldCampaignForm(CampaignForm):
    class Meta(CampaignForm):
        pass


class GuaranteedCampaignForm(DirectSoldCampaignForm):
    class Meta(DirectSoldCampaignForm):
        pass


class PromotionalCampaignForm(PromotionalCampaignForm):
    class Meta(DirectSoldCampaignForm):
        pass


class NetworkCampaignForm(CampaignForm):
    class Meta(CampaignForm):
        pass
"""


"""
class AdGroupForm(mpforms.MPModelForm):
    TEMPLATE = 'advertiser/forms/adgroup_form.html'

    site_keys = mpfields.MPModelMultipleChoiceField(AdUnit,required=False)
    keywords = mpfields.MPKeywordsField(required=False)
    geo = forms.Field(widget=forms.MultipleHiddenInput, required=False)
    custom_html = mpfields.MPTextareaField(required=False)
    custom_method = mpfields.MPTextField(required=False)
    cities = forms.Field(widget=forms.MultipleHiddenInput, required=False)

    device_targeting = mpfields.MPChoiceField(choices=[(False,'All'),
                                                       (True,'Filter by device and OS')],
                                              widget=mpwidgets.MPRadioWidget)

    ios_version_max = mpfields.MPChoiceField(choices=IOS_VERSION_CHOICES,
                                             widget=mpwidgets.MPSelectWidget)

    ios_version_min = mpfields.MPChoiceField(choices=IOS_VERSION_CHOICES[1:],
                                             widget=mpwidgets.MPSelectWidget)

    android_version_max = mpfields.MPChoiceField(choices=ANDROID_VERSION_CHOICES,
                                          widget=mpwidgets.MPSelectWidget)

    android_version_min = mpfields.MPChoiceField(choices=ANDROID_VERSION_CHOICES[1:],
                                          widget=mpwidgets.MPSelectWidget)

    class Meta:
        model = AdGroup

        fields = ('name', 'network_type', 'keywords',
                  'bid', 'bid_strategy',
                  'site_keys',
                  'hourly_frequency_cap','daily_frequency_cap',
                  'allocation_percentage','budget',
                  "device_targeting",'target_iphone',
                  'target_ipod', 'target_ipad', 'ios_version_max','ios_version_min',
                  'target_android', 'android_version_max','android_version_min',
                  'target_other')

    def save( self, commit=True):
        obj = super(AdGroupForm, self).save(commit=False)
        if obj:
            geos = self.cleaned_data['geo']
            geo_preds = []
            for geo in geos:
                geo = tuple(geo.split(','))
                #Make the geo_list such that the one that needs 3 entries corresponds ot idx 2, 2 entires idx 1, 1 entry idx 0
                geo_preds.append(GEO_LIST[len(geo)-1] % geo)
            obj.geo_predicates = geo_preds
        if commit:
            obj.put()
        return obj

    def __init__(self, *args,**kwargs):
        instance = kwargs.get('instance',None)
        initial = kwargs.get('initial',None)
        if instance:
            if not initial:
                initial = {}

            if instance.network_type == 'custom' and instance.net_creative:
                initial.update(custom_html = instance.net_creative.html_data)

            if instance.network_type == 'custom_native' and instance.net_creative:
                initial.update(custom_method = instance.net_creative.html_data)

            # Set up cities
            cities = []
            for city in instance.cities:
                cities.append(city)
            geo_predicates = []
            for geo_pred in  instance.geo_predicates:
                preds = geo_pred.split(',')
                geo_predicates.append( ','.join( [ str( pred.split('=')[1] ) for pred in preds ] ) )
            initial.update(geo=geo_predicates)
            initial.update(cities=cities)
            #initial.update(geo=instance.geo_predicates)
            kwargs.update(initial=initial)



        super(AdGroupForm,self).__init__(*args,**kwargs)
"""


class AdGroupForm(forms.ModelForm):
    network_type = forms.ChoiceField(choices=(('admob_native', 'AdMob'),
                                              ('adsense', 'AdSense'),
                                              ('brightroll', 'BrightRoll'),
                                              ('ejam', 'eJam'),
                                              ('iAd', 'iAd'),
                                              ('inmobi', 'InMobi'),
                                              ('jumptap', 'Jumptap'),
                                              ('millennial_native', 'Millennial Media'),
                                              ('mobfox', 'MobFox'),
                                              ('custom', 'Custom Network'),
                                              ('custom_native', 'Custom Native Network')),
                                     label='Network Type:')
    custom_html = forms.CharField(label='Custom HTML:',
                                  required=False,
                                  widget=forms.Textarea(attrs={'placeholder': 'HTML Custom Content',
                                                               'rows': 3}))
    custom_method = forms.CharField(label='Custom Method:',
                                    required=False,
                                    widget=forms.TextInput(attrs={'placeholder': 'loadNativeSDK:'}))
    bid_strategy = forms.ChoiceField(choices=(('cpm', 'CPM'),
                                              ('cpc', 'CPC')),
                                     label='Rate:',
                                     initial='cpc')
    bid = forms.FloatField(widget=forms.TextInput(attrs={'class': 'number'}),
                           initial=0.05,
                           required=False)
    # site_keys defined in __init__
    allocation_percentage = forms.CharField(initial=100.0,
                                            label='Allocation:',
                                            required=False,
                                            widget=forms.TextInput(attrs={'class': 'number'}))
    allocation_type = forms.ChoiceField(choices=(('users', 'users'),
                                                 ('requests', 'requests')))
    daily_frequency_cap = forms.IntegerField(initial=0,
                                             label='Frequency Caps:',
                                             required=False,
                                             widget=forms.TextInput(attrs={'class': 'number'}))
    hourly_frequency_cap = forms.IntegerField(initial=0,
                                              required=False,
                                              widget=forms.TextInput(attrs={'class': 'number'}))
    device_targeting = forms.TypedChoiceField(choices=((0, 'All'),
                                                       (1, 'Filter by device and OS')),
                                              coerce=lambda x: bool(int(x)),
                                              initial=0,
                                              label='Device Targeting:',
                                              widget=forms.RadioSelect)
    target_iphone = forms.BooleanField(initial=True,
                                       label='iPhone',
                                       required=False)
    target_ipod = forms.BooleanField(initial=True,
                                     label='iPod',
                                     required=False)
    target_ipad = forms.BooleanField(initial=True,
                                     label='iPad',
                                     required=False)
    ios_version_min = forms.ChoiceField(choices=IOS_VERSION_CHOICES[1:],
                                        label='Min:')
    ios_version_max = forms.ChoiceField(choices=IOS_VERSION_CHOICES,
                                        label='Max:')
    target_android = forms.BooleanField(initial=True,
                                        label='Android',
                                        required=False)
    android_version_min = forms.ChoiceField(choices=ANDROID_VERSION_CHOICES[1:],
                                            label='Min:')
    android_version_max = forms.ChoiceField(choices=ANDROID_VERSION_CHOICES,
                                            label='Max:')
    target_other = forms.BooleanField(initial=True,
                                      label='Other',
                                      required=False)
    keywords = forms.CharField(required=False,
                               widget=forms.Textarea(attrs={'cols': 50,
                                                            'rows': 3}))
    def __init__(self, *args, **kwargs):
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        # allows us to set choices on instantiation
        site_keys = kwargs.get('site_keys', [])
        self.fields['site_keys'] = forms.MultipleChoiceField(choices=site_keys, required=False)
        # hack to make the forms ordered correctly
        # TODO: fix common.utils.djangoforms.ModelForm to conform to
        # https://docs.djangoproject.com/en/1.2/topics/forms/modelforms/#changing-the-order-of-fields
        self.fields.keyOrder = self.Meta.fields
    def clean(self):
        cleaned_data = super(AdGroupForm, self).clean()
        #logging.error(cleaned_data)
        #logging.error(cleaned_data['site_keys'])
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
                  'allocation_type',
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
                  # geo targeting
                  'keywords')


class AbstractCreativeForm(mpforms.MPModelForm):
    def save(self,commit=True):
        obj = super(AbstractCreativeForm,self).save(commit=False)
        if not obj.conv_appid and obj.url:
            obj.conv_appid = self._get_appid(obj.url)

        if commit:
            obj.put()
        return obj

    def _get_appid(self,url):
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

    class Meta:
        model = Creative
        fields = ('ad_type','name','tracking_url','url','display_url',
                  'format','custom_height','custom_width','landscape',
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
        fields = ('headline','line1','line2') + \
                 ('ad_type','name','tracking_url','url','display_url',
                  'format','custom_height','custom_width','landscape',
                  'conv_appid', 'launchpage')

class TextAndTileCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/text_tile_creative_form.html'

    image_url = forms.URLField(verify_exists=False,required=False)
    image_file = forms.FileField(required=False)

    class Meta:
        model = TextAndTileCreative
        fields = ('action_icon', 'color', 'font_color', 'gradient') + \
                 ('line1','line2', 'ad_type','name','tracking_url','url','format','custom_height','custom_width','landscape', 'conv_appid', 'launchpage')

    def __init__(self, *args,**kwargs):
        instance = kwargs.get('instance',None)
        initial = kwargs.get('initial',None)

        if instance:
            if instance.image_blob:
                image_url = helpers.get_url_for_blob(instance.image_blob) #reverse('advertiser_creative_image',kwargs={'creative_key':str(instance.key())})
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
        else:
            commit = False

        if commit:
            obj.put()
        return obj
