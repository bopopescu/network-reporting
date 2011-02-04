import logging
from google.appengine.ext import db
from google.appengine.api import images

from advertiser.models import Campaign, AdGroup, Creative, \
                              TextCreative, TextAndTileCreative,\
                              HtmlCreative, ImageCreative
from publisher.models import Site as AdUnit
from django import forms
from common.utils import forms as mpforms

class CampaignForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/campaign_form.html'

  class Meta:
    model = Campaign
    fields = ('name', 'description', 'budget', 'campaign_type', 'start_date', 'end_date')

AdUnit.all()

class AdGroupForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/adgroup_form.html'
  
  # TODO: how can i make this dynamic
  site_keys = mpforms.MPModelMultipleChoiceField(AdUnit,required=False)
  keywords = mpforms.MPTextAreaField(required=False)
  geo_predicates = mpforms.MPTextAreaField()
  device_predicates = mpforms.MPTextAreaField(required=False)
  
  class Meta:
    model = AdGroup
    fields = ('name', 'network_type', 'priority_level', 'keywords',
              'bid', 'bid_strategy', 'geo_predicates', 
              'percent_users', 'site_keys',
              'hourly_frequency_cap','daily_frequency_cap','allocation_percentage',
              'allocation_type','budget')
              

class BaseCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/base_creative_form.html'
  
  class Meta:
    model = Creative
    fields = ('ad_type','name','tracking_url','url','display_url','format')
    
class TextCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/text_creative_form.html'
  
  class Meta:
    model = TextCreative
    fields = ('headline','line1','line2') + \
             ('ad_type','name','tracking_url','url','display_url','format')
    
class TextAndTileCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/text_tile_creative_form.html'
  
  class Meta:
    model = TextAndTileCreative
    fields = ('line1','line2', 'ad_type','name','tracking_url','url','format')
    
class HtmlCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/html_creative_form.html'
  
  class Meta:
    model = HtmlCreative
    fields = ('html_data',) + \
             ('ad_type','name','tracking_url','url','display_url','format')
             
class ImageCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/image_creative_form.html'
  
  image_file = forms.FileField()
  
  class Meta:
    model = ImageCreative
    fields = ('ad_type','name','tracking_url','url','display_url','format') 
    
  def save(self,commit=True):
    obj = super(ImageCreativeForm,self).save(commit=False)  
    img = images.Image(self.files.get('image_file').read())
    img.im_feeling_lucky()
    obj.image = db.Blob(img.execute_transforms())
    obj.image_width = img.width
    obj.image_height = img.height
    if commit:
      obj.put()
    return obj  