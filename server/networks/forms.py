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
    bid_strategy = forms.ChoiceField(choices=(('cpm', 'CPM'), ('cpc', 'CPC')),
                                     label='Rate:', initial='cpm')
    bid = forms.FloatField(initial=0.05,
                           widget=forms.TextInput(attrs={'class': 'float'}))
    active = forms.BooleanField(label='Active:', required=False)

    def clean_bid(self):
        bid = self.cleaned_data.get('bid', None)
        if bid != None and bid <= 0.0:
            raise forms.ValidationError("Bid must be greather than zero")
        return bid

    class Meta:
        model = AdGroup
        fields = ('bid_strategy',
                  'bid',
                  'active')
