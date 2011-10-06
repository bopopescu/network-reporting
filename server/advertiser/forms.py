from __future__ import with_statement


from advertiser.models import Campaign, AdGroup, Creative, \
                              TextCreative, TextAndTileCreative,\
                              HtmlCreative, ImageCreative
from common.constants import (  CITY_GEO,
                                REGION_GEO,
                                COUNTRY_GEO,
                                )
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

from budget.budget_service import update_budget
import logging
import re
import urlparse
import cgi

from common.constants import IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES

def get_filetype_extension(filename):
    if not type(filename) == str:
        filename = str(filename)
    if filename.find('.') >= 0:
        return filename.split('.')[-1]
    return None

class CampaignForm(mpforms.MPModelForm):
    TEMPLATE = 'advertiser/forms/campaign_form.html'
    gtee_level = forms.Field(widget = forms.Select)
    promo_level = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget)
    mpx_level = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget, required=False)
    budget_strategy = mpfields.MPChoiceField(choices=[('evenly','Spread evenly'),('allatonce','All at once')],widget=mpwidgets.MPRadioWidget)
    budget_type = mpfields.MPChoiceField(choices=[('daily','Daily'),('full_campaign','Full Campaign')],widget=mpwidgets.MPSelectWidget)
    price_floor = mpfields.MPTextField(required=False, initial="0.25")

    #priority is now based off of campaign_type, not actually priority
    #gtee has 3 levels, this makes it so the database understands the three different levels of gtee
    #but the form sees one level of gtee and three levels of priority
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        if instance and instance.campaign_type:
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
        if commit:
            obj.put()
            update_budget(obj, save_campaign = False)
            obj.put()
        return obj

    class Meta:
      model = Campaign
      fields = ('name', 'budget_strategy', 'budget_type', 'full_budget', 'description', 'budget', 'campaign_type', 'start_date', 'end_date', 'gtee_level','promo_level')


class AdGroupForm(mpforms.MPModelForm):
    TEMPLATE = 'advertiser/forms/adgroup_form.html'

    site_keys = mpfields.MPModelMultipleChoiceField(AdUnit,required=False)
    keywords = mpfields.MPKeywordsField(required=False)
    geo = forms.Field(widget=forms.MultipleHiddenInput, required=False)
    custom_html = mpfields.MPTextareaField(required=False)
    custom_method = mpfields.MPTextField(required=False)
    cities = forms.Field(widget=forms.MultipleHiddenInput, required=False)

    device_targeting = mpfields.MPChoiceField(choices=[(False,'All'),(True,'Filter by device and OS')],widget=mpwidgets.MPRadioWidget)

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
                  'percent_users', 'site_keys',
                  'hourly_frequency_cap','daily_frequency_cap','allocation_percentage',
                  'allocation_type','budget',
                  "device_targeting",
                  'target_iphone',
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
                cities.append(str(city))
            geo_predicates = []
            for geo_pred in  instance.geo_predicates:
                preds = geo_pred.split(',')
                geo_predicates.append( ','.join( [ str( pred.split('=')[1] ) for pred in preds ] ) )
            initial.update(geo=geo_predicates)
            initial.update(cities=cities)
            #initial.update(geo=instance.geo_predicates)
            kwargs.update(initial=initial)



        super(AdGroupForm,self).__init__(*args,**kwargs)

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
        qs_dict = cgi.parse_qs(urlparse.urlparse(url).query)
        if 'id' in qs_dict:
            itunes_id = qs_dict['id'][0]
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
        fields = ('ad_type','name','tracking_url','url','display_url','format','custom_height','custom_width','landscape', 'conv_appid', 'launchpage')

    def clean_name(self):
        data = self.cleaned_data.get('name', None)
        if not data:
            raise forms.ValidationError('You must give your creative a name.')
        return data


class TextCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/text_creative_form.html'

    class Meta:
        model = TextCreative
        fields = ('headline','line1','line2') + \
                 ('ad_type','name','tracking_url','url','display_url','format','custom_height','custom_width','landscape', 'conv_appid', 'launchpage')

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
            image_url = images.get_serving_url(instance.image_blob) #reverse('advertiser_creative_image',kwargs={'creative_key':str(instance.key())})
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
        fields = ('html_data',) + \
                 ('ad_type','name','tracking_url','url','display_url','format','custom_height','custom_width','landscape', 'conv_appid', 'launchpage')

class ImageCreativeForm(AbstractCreativeForm):
    TEMPLATE = 'advertiser/forms/image_creative_form.html'

    image_url = forms.URLField(verify_exists=False,required=False)
    image_file = forms.FileField(required=False)

    class Meta:
        model = ImageCreative
        fields = ('ad_type','name','tracking_url','url','display_url','format','custom_height','custom_width','landscape', 'conv_appid', 'launchpage')

    def __init__(self, *args,**kwargs):
        instance = kwargs.get('instance',None)
        initial = kwargs.get('initial',None)

        if instance:
            if instance.image_blob:
                try:
                    image_url = images.get_serving_url(instance.image_blob)
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

