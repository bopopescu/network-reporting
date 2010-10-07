from advertiser.models import Campaign, AdGroup
from django import forms

class CampaignForm(forms.ModelForm):
	class Meta:
		model = Campaign
		fields = ('name', 'description', 'budget', 'campaign_type')

class AdGroupForm(forms.ModelForm):
	class Meta:
		model = AdGroup
		fields = ('name', 'network_type', 'priority_level', 'bid', 'bid_strategy', 'geo_predicates', 'device_predicates', 'percent_users','hourly_frequency_cap','daily_frequency_cap')
