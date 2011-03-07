from advertiser.models import Campaign, AdGroup, Creative, \
                              TextCreative, TextAndTileCreative,\
                              HtmlCreative, ImageCreative
from common.constants import (  CITY_GEO,
                                REGION_GEO,
                                COUNTRY_GEO,
                                )
#THIS ORDER IS VERY IMPORTANT DO NOT CHANGE IT (thanks!)
GEO_LIST = ( COUNTRY_GEO, REGION_GEO, CITY_GEO )

from common.utils import forms as mpforms
from django import forms
from django.core.urlresolvers import reverse
from google.appengine.ext import db
from google.appengine.api import images
from publisher.models import Site as AdUnit

import logging

class CampaignForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/campaign_form.html'
  
  def __init__(self, *args, **kwargs):
      instance = kwargs.get('instance', None)
      initial = kwargs.get('initial', None)
      if instance:
          vals = instance.campaign_type.split('_')
          if 'gtee' in vals: 
              type = 'gtee'
              if 'high' in vals:
                  level = 'high'
              elif 'low' in vals:
                  level = 'low'
              else:
                  level = 'normal'
              if not initial:
                  initial = {}
              initial.update(campaign_type=type)
              initial.update(gtee_level=level)
              kwargs.update(initial=initial)
      super(CampaignForm, self).__init__(*args, **kwargs)
      
  def save(self, commit=True):
      obj = super(CampaignForm, self).save(commit=False)
      if obj:
          logging.warning(obj)
          logging.warning(self.cleaned_data)
          type = self.cleaned_data['campaign_type']
          if type == 'gtee':
              lev = self.cleaned_data['gtee_level']
              if lev == 'high': 
                  type = 'gtee_high'
              elif lev == 'low':
                  type = 'gtee_low'
              elif lev == 'normal':
                  type = 'gtee'
              else:
                  logging.warning("Invalid gtee_level for gtee")
              obj.campaign_type = type     
      if commit:
          obj.put()
      return obj

  class Meta:
    model = Campaign
    fields = ('name', 'description', 'budget', 'campaign_type', 'start_date', 'end_date', 'gtee_level')

AdUnit.all()

class AdGroupForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/adgroup_form.html'
  
  # TODO: how can i make this dynamic
  site_keys = mpforms.MPModelMultipleChoiceField(AdUnit,required=False)
  keywords = mpforms.MPTextAreaField(required=False)
  geo = forms.Field(widget = forms.MultipleHiddenInput)
  device_predicates = mpforms.MPTextAreaField(required=False)
  
  class Meta:
    model = AdGroup
    fields = ('name', 'network_type', 'priority_level', 'keywords',
              'bid', 'bid_strategy', 
              'percent_users', 'site_keys',
              'hourly_frequency_cap','daily_frequency_cap','allocation_percentage',
              'allocation_type','budget')

  def save( self, commit=True):
      obj = super(AdGroupForm, self).save(commit=False)
      if obj:
          geos = self.cleaned_data['geo']
          geo_preds = []
          for geo in geos:
              geo = tuple(geo.split(','))
              #Make the geo_list such that the one that needs 3 entries corresponds ot idx 2, 2 entires idx 1, 1 entry idx 0
              geo_preds.append(GEO_LIST[len(geo)-1] % geo)
          obj.geo_predicates = geo_preds
      if commit:
          obj.put()
      return obj

  def __init__(self, *args,**kwargs):
    instance = kwargs.get('instance',None)
    initial = kwargs.get('initial',None)

    if instance:
      geo_predicates = [] 
      for geo_pred in  instance.geo_predicates: 
          preds = geo_pred.split(',')
          geo_predicates.append( ','.join( [ str( pred.split('=')[1] ) for pred in preds ] ) )
      if not initial:
        initial = {}
      initial.update(geo=geo_predicates)
      #initial.update(geo=instance.geo_predicates)
      kwargs.update(initial=initial)
    super(AdGroupForm,self).__init__(*args,**kwargs)    


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
  
  image_url = forms.URLField(verify_exists=False,required=False)
  image_file = forms.FileField(required=False)
  
  class Meta:
    model = TextAndTileCreative
    fields = ('line1','line2', 'ad_type','name','tracking_url','url','format')
    
  def __init__(self, *args,**kwargs):
    instance = kwargs.get('instance',None)
    initial = kwargs.get('initial',None)

    if instance:
      image_url = reverse('advertiser_creative_image',kwargs={'creative_key':str(instance.key())})
      if not initial:
        initial = {}
      initial.update(image_url=image_url)  
      kwargs.update(initial=initial)
    super(TextAndTileCreativeForm,self).__init__(*args,**kwargs)    

  def save(self,commit=True):
    obj = super(TextAndTileCreativeForm,self).save(commit=False)  
    if self.files.get('image_file',None):
      img = images.Image(self.files.get('image_file').read())
      img.im_feeling_lucky()
      obj.image = db.Blob(img.execute_transforms())
      obj.image_width = img.width
      obj.image_height = img.height
    if commit:
      obj.put()
    return obj  
    
class HtmlCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/html_creative_form.html'
  
  class Meta:
    model = HtmlCreative
    fields = ('html_data',) + \
             ('ad_type','name','tracking_url','url','display_url','format')
             
class ImageCreativeForm(mpforms.MPModelForm):
  TEMPLATE = 'advertiser/forms/image_creative_form.html'
  
  image_url = forms.URLField(verify_exists=False,required=False)
  image_file = forms.FileField(required=False)
  
  class Meta:
    model = ImageCreative
    fields = ('ad_type','name','tracking_url','url','display_url','format') 
    
  def __init__(self, *args,**kwargs):
    instance = kwargs.get('instance',None)
    initial = kwargs.get('initial',None)

    if instance:
      image_url = reverse('advertiser_creative_image',kwargs={'creative_key':str(instance.key())})
      if not initial:
        initial = {}
      initial.update(image_url=image_url)  
      kwargs.update(initial=initial)
    super(ImageCreativeForm,self).__init__(*args,**kwargs)    
    
  def save(self,commit=True):
    obj = super(ImageCreativeForm,self).save(commit=False)  
    if self.files.get('image_file',None):
      img = images.Image(self.files.get('image_file').read())
      img.im_feeling_lucky()
      obj.image = db.Blob(img.execute_transforms())
      obj.image_width = img.width
      obj.image_height = img.height
    if commit:
      obj.put()
    return obj  
    
  # def save(self,commit=True):
  #   obj = super(AppForm,self).save(commit=False)
  #   if self.cleaned_data['img_url']:
  #     if not self.cleaned_data['img_url'] == self.initial.get('img_url'):
  #       try:
  #         response = urllib.urlopen(self.cleaned_data['img_url'])
  #         img = response.read()
  #         obj.icon = db.Blob(img)
  #       except Exception, e: # TODO: appropriately handle the failure
  #         raise Exception('WTF: %s'%e)
  #     else:
  #       logging.info("keeping same icon because the new is same as old")
  #       obj.icon = self.instance.icon # sets the icon to the original
  #   elif self.cleaned_data['img_file']:
  #     try:
  #       icon = images.resize(self.cleaned_data['img_file'], 60, 60)
  #       obj.icon = db.Blob(icon)
  #     except Exception: # TODO: appropriate handle the failure
  #       raise Exception('WTF2: %s'%e)
  #   elif self.instance: # if neither img_url or img_file come in just use the old value
  #     logging.info("keeping same icon because no new provided")
  #     obj.icon = self.instance.icon    
  #   if commit:
  #     obj.put()
  #   return obj      
    
