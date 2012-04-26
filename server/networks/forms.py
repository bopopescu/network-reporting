from django import forms
from advertiser.models import Campaign, AdGroup

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

    def clean_bid(self):
        bid = self.cleaned_data.get('bid', None)
        if bid != None and bid <= 0.0:
            raise forms.ValidationError("Bid must be greather than zero")
        return bid

    class Meta:
        model = AdGroup
        fields = ('bid',
                  'active')
