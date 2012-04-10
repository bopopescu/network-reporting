from django import forms
from advertiser.models import Campaign

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
