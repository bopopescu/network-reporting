import urllib2 as urllib
import logging

from google.appengine.ext import db
from google.appengine.api import images

from django import forms
from django.core.urlresolvers import reverse
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets 
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

ANIMATION_CHOICES = (
    (u'0', 'No Animation'),
    (u'1', 'Random'),
    (u'2', 'Flip from left'),
    (u'3', 'Flip from right'),
    (u'4', 'Curl up'),
    (u'5', 'Curl down'),
    (u'6', 'Fade'),
)

class AdUnitForm(mpforms.MPModelForm):
  TEMPLATE = 'publisher/forms/adunit_form.html'
  format = mpfields.MPTextField(required=True, widget = mpwidgets.MPFormatWidget)
  # animation_type = mpfields.MPChoiceField(choices=ANIMATION_CHOICES,widget=mpwidgets.MPSelectWidget)
  
  class Meta:
    model = Site
    fields = ('name','description','app_key','ad_type', 'backfill', 'backfill_threshold_cpm','keywords',
    'width','height', 'device_format', 'format','adsense_channel_id','refresh_interval')
 
 
class SiteForm(forms.ModelForm):
  class Meta:
    model = Site
    fields = ('name', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
