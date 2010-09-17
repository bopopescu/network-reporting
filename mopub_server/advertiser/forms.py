from advertiser.models import Campaign, AdGroup
from django import forms

class CampaignForm(forms.ModelForm):
	class Meta:
		model = Campaign
		fields = ('name', 'description', 'budget', 'bid_strategy', 'geo_predicates', 'device_predicates')

class AdGroupForm(forms.ModelForm):
	class Meta:
		model = AdGroup
		fields = ('name', 'bid')
