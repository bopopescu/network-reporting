import logging


from advertiser.models import Campaign, AdGroup
from publisher.models import Site as AdUnit
from django import forms
from common.utils import forms as mpforms

class CampaignForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/campaign_form.html'

  class Meta:
    model = Campaign
    fields = ('name', 'description', 'budget', 'campaign_type')

AdUnit.all()

class AdGroupForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/adgroup_form.html'

  site_keys = mpforms.MPModelMultipleChoiceField(None)
  class Meta:
    model = AdGroup
    fields = ('name', 'network_type', 'priority_level', 
              'bid', 'bid_strategy', 'geo_predicates', 
              'device_predicates', 'percent_users', 'site_keys',
              'hourly_frequency_cap','daily_frequency_cap',
              'budget','keywords')
                
  def clean_site_keys(self):
    logging.info("!"*10+'site_keys%s'%self.cleaned_data['site_keys']+'!'*10)
    return self.cleaned_data['site_keys']            

  def clean_keywords(self):     
    keywords = self.cleaned_data   
    keywords = [k for k in data.lower().replace('\r','\n').split('\n') if k] 
    return keywords 