from advertiser.models import Campaign, AdGroup
from django import forms

class CampaignForm(forms.ModelForm):
	class Meta:
		model = Campaign
		fields = ('name', 'description', 'budget')

class AdGroupForm(forms.ModelForm):
	class Meta:
		model = AdGroup
		fields = ('name', 'priority_level', 'bid', 'bid_strategy', 'geo_predicates', 'device_predicates')
