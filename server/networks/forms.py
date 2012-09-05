import re

from django import forms
from django.forms.util import ErrorList
from advertiser.models import Campaign, AdGroup

from common.constants import (COUNTRIES, IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES,
                              CITY_GEO, REGION_GEO, COUNTRY_GEO)

#THIS ORDER IS VERY IMPORTANT DO NOT CHANGE IT (thanks!)
GEO_LIST = (COUNTRY_GEO, REGION_GEO, CITY_GEO)

class NetworkCampaignForm(forms.ModelForm):
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Campaign Name'}))
    description = forms.CharField(label='Description:', required=False,
                                  widget=forms.Textarea(attrs={'cols': 50,
                                                               'rows': 3,
                                                               'placeholder': 'Campaign for My New App'}))

    class Meta:
        model = Campaign
        fields = ('name',
                  'description')


class NetworkAdGroupForm(forms.ModelForm):
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

    # Geo Targeting
    accept_targeted_locations = forms.TypedChoiceField(
        choices=(('0', 'Not Located'),
                 ('1', 'Located')),
        coerce=lambda x: bool(int(x)), initial=True,
        required=False, widget=forms.Select)
    targeted_countries = forms.MultipleChoiceField(
        choices=COUNTRIES, label='Country:', required=False,
        widget=forms.SelectMultiple(attrs={'data-placeholder': 'Ex: United States, ...'}))
    # non-db field
    region_targeting_type = forms.ChoiceField(
        choices=(('all', 'All Regions'),
                 ('regions_and_cities', 'Specific State / Metro Area / DMA (Wi-Fi Required), or Specific City within Country'),
                 ('zip_codes', 'Specific ZIP Codes within Country (Wi-Fi Required)')),
        initial='all', label='Region:', required=False,
        widget=forms.RadioSelect)
    targeted_regions = forms.Field(required=False, widget=forms.SelectMultiple(
            attrs={'data-placeholder': 'Ex: Ohio, Miami-Ft. Lauderdale FL, ...'}))
    targeted_cities = forms.Field(required=False, widget=forms.SelectMultiple(
            attrs={'data-placeholder': 'Ex: New York, NY, US, ...'}))
    targeted_zip_codes = forms.Field(required=False, widget=forms.Textarea(
            attrs={'class': 'input-text', 'placeholder': 'Ex: 94117 27705', 'rows': 3, 'cols': 50}))

    # Connectivity Targeting
    # non-db field
    connectivity_targeting_type = forms.ChoiceField(
        choices=(('all', 'All Carriers and Wi-Fi'),
                 ('wi-fi', 'Wi-Fi Only'),
                 ('carriers', 'Selected Carriers')),
        initial='all', label='Connectivity:', required=False,
        widget=forms.RadioSelect)
    targeted_carriers = forms.Field(required=False, widget=forms.SelectMultiple(
            attrs={'data-placeholder': 'Ex: Verizon, ...'}))

    keywords = forms.CharField(required=False,
                               label='Keywords:',
                               widget=forms.Textarea(attrs={'cols': 50,
                                                            'rows': 3}))

    def __init__(self, *args, **kwargs):
        initial = args[5] if len(args) > 5 else kwargs.get('initial', None)
        instance = args[9] if len(args) > 9 else kwargs.get('instance', None)

        if instance:
            if not initial:
                initial = {}

            if instance.network_type == 'custom' and instance.creatives.get():
                initial.update(custom_html=instance.creatives.get().html_data)
            elif instance.network_type == 'custom_native' and \
                    instance.creatives.get():
                initial.update(custom_method=instance.creatives.get().html_data)

            if instance.targeted_regions or instance.targeted_cities:
                initial['region_targeting_type'] = 'regions_and_cities'
            elif instance.targeted_zip_codes:
                initial['region_targeting_type'] = 'zip_codes'

            initial['targeted_zip_codes'] = '\n'.join(instance.targeted_zip_codes)

            if instance.targeted_carriers == ['Wi-Fi']:
                initial['connectivity_targeting_type'] = 'wi-fi'
            elif instance.targeted_carriers:
                initial['connectivity_targeting_type'] = 'carriers'

            kwargs.update(initial=initial)

        super(forms.ModelForm, self).__init__(*args, **kwargs)

    def clean_targeted_zip_codes(self):
        targeted_zip_codes = self.cleaned_data.get('targeted_zip_codes', None)
        if targeted_zip_codes:
            targeted_zip_codes = targeted_zip_codes.split()
            for targeted_zip_code in targeted_zip_codes:
                if not re.match('^\d{5}$', targeted_zip_code):
                    raise forms.ValidationError('Malformed ZIP code %s.' % targeted_zip_code)
        return targeted_zip_codes

    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords', None)

        if keywords:
            if len(keywords) > 500:
                raise forms.ValidationError('Maximum 500 characters for keywords.')

            if isinstance(keywords, basestring):
                keywords = keywords.replace(',', '\n').split('\n')
                keywords = [word.strip() for word in keywords]
        else:
            keywords = []

        return keywords

    def clean(self):
        cleaned_data = super(NetworkAdGroupForm, self).clean()

        self._clean_geographical_targeting(cleaned_data)
        self._clean_connectivity_targeting(cleaned_data)

        return cleaned_data

    def _clean_geographical_targeting(self, cleaned_data):
        if 'accept_targeted_locations' in cleaned_data and 'targeted_countries' in cleaned_data and not cleaned_data['accept_targeted_locations'] and not cleaned_data['targeted_countries']:
            self._errors['accept_targeted_locations'] = ErrorList()
            self._errors['accept_targeted_locations'].append('You must select some geography to target against.')
        if 'region_targeting_type' in cleaned_data and cleaned_data['region_targeting_type'] != 'regions_and_cities':
            cleaned_data['targeted_regions'] = []
            cleaned_data['targeted_cities'] = []
        if 'region_targeting_type' in cleaned_data and cleaned_data['region_targeting_type'] != 'zip_codes':
            cleaned_data['targeted_zip_codes'] = []

    def _clean_connectivity_targeting(self, cleaned_data):
        if 'connectivity_targeting_type' in cleaned_data and cleaned_data['connectivity_targeting_type'] == 'wi-fi':
            cleaned_data['targeted_carriers'] = ['Wi-Fi']
        elif 'connectivity_targeting_type' in cleaned_data and cleaned_data['connectivity_targeting_type'] != 'carriers':
            cleaned_data['targeted_carriers'] = []

    class Meta:
        model = AdGroup
        fields = ('device_targeting',
                  'target_iphone',
                  'target_ipod',
                  'target_ipad',
                  'ios_version_min',
                  'ios_version_max',
                  'target_android',
                  'android_version_min',
                  'android_version_max',
                  'target_other',
                  'accept_targeted_locations',
                  'targeted_countries',
                  'region_targeting_type',
                  'targeted_cities',
                  'targeted_regions',
                  'targeted_zip_codes',
                  'connectivity_targeting_type',
                  'targeted_carriers',
                  'keywords')


class AdUnitAdGroupForm(forms.ModelForm):
    bid = forms.FloatField(initial=0.05,
                           widget=forms.TextInput(attrs={'class': 'float'}))
    active = forms.BooleanField(label='Active:', required=False)

    # Advanced settings available under more options in edit network form
    allocation_percentage = forms.FloatField(initial='', label='Allocation:',
                                             required=False,
                                             widget=forms.TextInput(
                                                 attrs={'class': 'float'}))
    daily_frequency_cap = forms.IntegerField(initial='', label='Frequency Caps:',
                                             required=False,
                                             widget=forms.TextInput(
                                                 attrs={'class': 'float'}))
    hourly_frequency_cap = forms.IntegerField(initial='', required=False,
                                              widget=forms.TextInput(
                                                  attrs={'class': 'float'}))

    # used for custom networks
    custom_html = forms.CharField(label='Custom HTML:', required=False,
                                  widget=forms.Textarea(attrs={'placeholder': 'HTML Custom Content',
                                                               'rows': 3}))
    # used for custom_native networks
    custom_method = forms.CharField(label='Custom Method:', required=False,
                                    widget=forms.TextInput(attrs={'placeholder': 'loadNativeSDK:'}))

    def __init__(self, *args, **kwargs):
        # network type is required for __init__
        self.network_type = kwargs.pop('network_type')

        initial = kwargs.get('initial', {})
        adgroup = kwargs.get('instance', None)

        if adgroup:
            if adgroup.network_type == 'custom' and adgroup.creatives.get():
                initial['custom_html'] = adgroup.creatives.get().html_data
            elif adgroup.network_type == 'custom_native' and \
                    adgroup.creatives.get():
                initial['custom_method'] = adgroup.creatives.get().html_data

        kwargs.update(initial=initial)

        super(forms.ModelForm, self).__init__(*args, **kwargs)

    def clean_bid(self):
        bid = self.cleaned_data.get('bid', None)
        if bid != None and bid <= 0.0:
            raise forms.ValidationError("Bid must be greather than zero")
        return bid

    def clean_allocation_percentage(self):
        allocation_percentage = self.cleaned_data.get('allocation_percentage', None)
        if (not isinstance(allocation_percentage, int) and
            not isinstance(allocation_percentage, float)):
            allocation_percentage = 100
        return allocation_percentage

    def clean_custom_html(self):
        custom_html = self.cleaned_data.get('custom_html', None)
        if self.network_type == 'custom' and self.cleaned_data.get('active', False) and \
                not custom_html:
            raise forms.ValidationError("This field is required if this adunit is turned on.")
        return custom_html

    def clean_custom_method(self):
        custom_method = self.cleaned_data.get('custom_method', None)
        if self.network_type == 'custom_native' and self.cleaned_data.get('active', False) and \
                not custom_method:
            raise forms.ValidationError("This field is required if this adunit is turned on.")
        return custom_method

    class Meta:
        model = AdGroup
        fields = ('bid',
                  'active',
                  'allocation_percentage',
                  'daily_frequency_cap',
                  'hourly_frequency_cap',)

