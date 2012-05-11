import logging
from django import forms
from advertiser.models import Campaign, AdGroup

from common.constants import (IOS_VERSION_CHOICES, ANDROID_VERSION_CHOICES,
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
    active = forms.BooleanField(label='Active:', required=False)
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

            geo_predicates = []
            for geo_predicate in instance.geo_predicates:
                preds = geo_predicate.split(',')
                geo_predicates.append(','.join([str(pred.split('=')[1]) for pred in preds]))
            initial.update(geo_predicates=geo_predicates)

            if len(geo_predicates) == 1 and len(instance.cities):
                initial['region_targeting'] = 'city'
                initial.update(cities=instance.cities)

            initial['active'] = instance.active

            kwargs.update(initial=initial)

        super(forms.ModelForm, self).__init__(*args, **kwargs)

    def clean_geo_predicates(self):
        geo_predicates = []
        for geo_predicate in self.cleaned_data.get('geo_predicates', []) or []:
            geo_predicate = tuple(geo_predicate.split(','))
            #Make the geo_list such that the one that needs 3 entries corresponds ot idx 2, 2 entires idx 1, 1 entry idx 0
            geo_predicates.append(GEO_LIST[len(geo_predicate) - 1] % geo_predicate)
        return geo_predicates

    def clean_keywords(self):
        keywords = self.cleaned_data.get('keywords', None)
        logging.warning("keywords: %s" % keywords)
        if keywords:
            if len(keywords) > 500:
                raise forms.ValidationError('Maximum 500 characters for keywords.')
        return keywords

    def clean(self):
        cleaned_data = super(NetworkAdGroupForm, self).clean()

        # don't store targeted cities unless region targeting for cities is selected
        if cleaned_data.get('region_targeting', None) != 'city':
            cleaned_data['cities'] = []

        return cleaned_data

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
                  'geo_predicates',
                  'region_targeting',
                  'cities',
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

    class Meta:
        model = AdGroup
        fields = ('bid',
                  'active',
                  'allocation_percentage',
                  'daily_frequency_cap',
                  'hourly_frequency_cap',)

