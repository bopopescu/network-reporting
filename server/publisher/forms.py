import urllib2 as urllib
import logging

from google.appengine.ext import db
from google.appengine.api import images

from django import forms
from django.core.urlresolvers import reverse
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from publisher.models import Site, App



class AppForm(mpforms.MPModelForm):
  TEMPLATE = 'publisher/forms/app_form.html'

  img_url = forms.URLField(verify_exists=False,required=False)
  img_file = forms.FileField(required=False)
  
  def __init__(self, *args,**kwargs):
    instance = kwargs.get('instance',None)
    initial = kwargs.get('initial',None)

    if instance:
      img_url = reverse('publisher_app_icon',kwargs={'app_key':str(instance.key())})
      if not initial:
        initial = {}
      initial.update(img_url=img_url)  
      kwargs.update(initial=initial)
    super(AppForm,self).__init__(*args,**kwargs)

  class Meta:
    model = App
    fields = ('name', 'app_type', 'url', 'package', 'description', 'adsense_app_name')
    
  def save(self,commit=True):
    obj = super(AppForm,self).save(commit=False)
    if self.cleaned_data['img_url']:
      if not self.cleaned_data['img_url'] == self.initial.get('img_url'):
        try:
          response = urllib.urlopen(self.cleaned_data['img_url'])
          img = response.read()
          obj.icon = db.Blob(img)
        except Exception, e: # TODO: appropriately handle the failure
          raise Exception('WTF: %s'%e)
      else:
        logging.info("keeping same icon because the new is same as old")
        obj.icon = self.instance.icon # sets the icon to the original
    elif self.cleaned_data['img_file']:
      try:
        img = self.cleaned_data['img_file'].read()
        icon = images.resize( img, 60, 60)
        obj.icon = db.Blob(icon)
      except Exception, e: # TODO: appropriate handle the failure
        raise Exception('WTF2: %s'%e)
    elif self.instance: # if neither img_url or img_file come in just use the old value
      logging.info("keeping same icon because no new provided")
      obj.icon = self.instance.icon    
    if commit:
      obj.put()
    return obj      

class AdUnitForm(mpforms.MPModelForm):
  TEMPLATE = 'publisher/forms/adunit_form.html'
  
  # renamed to avoid conflicts when submitting both app and adunit together
  # adunit_name = forms.CharField# (required=True,initial="Banner Ad")
  # adunit_description = forms.CharField(required=True,initial="General Purpose Banner Ad")
  adunit_name = mpfields.MPTextField(required=True,initial="Banner Ad")
  adunit_description = mpfields.MPTextareaField(required=True,initial="General Purpose Banner Ad")

  class Meta:
    model = Site
    fields = ('app_key','ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
    
  def __init__(self, *args,**kwargs):
      instance = kwargs.get('instance',None)
      initial = kwargs.get('initial',None)
      data = kwargs.get('data',None)
      logging.info('instance: %s kwargs: %s data: %s'%(instance, kwargs,data))       
      # re-write the names (TODO: this is annoying, we should move to a widget model)
      if instance and not data:
        initial = initial or {}
        initial.update(adunit_name=instance.name,
                       adunit_description=instance.description)
        kwargs.update(initial=initial)  
      logging.info('instance: %s kwargs: %s data: %s'%(instance, kwargs,data))       
      super(AdUnitForm, self).__init__(*args,**kwargs)
    
    
  def save(self,commit=True):
    obj = super(AdUnitForm,self).save(commit=False) 
    logging.info('clean_data: %s'%self.cleaned_data)
    obj.name = self.cleaned_data['adunit_name']
    obj.description = self.cleaned_data['adunit_description'] 
    # TODO: hardcoding height and width
    if obj.format == "full":
      obj.width = 320.0
      obj.height = 480.0
    else:
      width,height = obj.format.split('x')
      obj.width, obj.height = float(width),float(height)

    if commit:
      obj.put()
    logging.info('name: %s description: %s'%(obj.name,obj.description))  
    return obj  

class SiteForm(forms.ModelForm):
  class Meta:
    model = Site
    fields = ('name', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
