from django import forms

from common.utils import forms as mpforms

from publisher.models import Site, App

class AppForm(mpforms.MPModelForm):
  TEMPLATE = 'publisher/forms/app_form.html'
  
  img_url = forms.URLField(verify_exists=False,required=False)
  img_file = forms.FileField(required=False)

  class Meta:
    model = App
    fields = ('name', 'app_type', 'url', 'package', 'description', 'adsense_app_name')
    
  def save(self,commit=True):
    obj = super(AppForm,self).save(commit=False)
    if self.cleaned_data['img_url']:#not self.request.POST.get("img_url") == "":
      try:
        response = urllib.urlopen(self.cleaned_data['img_url'])
        img = response.read()
        obj.icon = db.Blob(img)
      except: # TODO: appropriately handle the failure
        pass
    elif self.cleaned_data['img_file']:
      try:
        icon = images.resize(self.cleaned_data['img_file'], 60, 60)
        obj.icon = db.Blob(icon)
      except: # TODO: appropriate handle the failure
        pass
    if commit:
      obj.put()
    return obj      

class AdUnitForm(mpforms.MPModelForm):
  TEMPLATE = 'publisher/forms/adunit_form.html'
  
  # renamed to avoid conflicts when submitting both app and adunit together
  adunit_name = forms.CharField(required=True,initial="Banner Ad")
  adunit_description = forms.CharField(required=True,initial="General Purpose Banner Ad")

  class Meta:
    model = Site
    fields = ('ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
    
  def save(self,commit=True):
    obj = super(AdUnitForm,self).save(commit=False) 
    obj.name = self.cleaned_data['adunit_name']
    obj.description = self.cleaned_data['adunit_description'] 
    if commit:
      obj.put()
    return obj  

class SiteForm(forms.ModelForm):
	class Meta:
		model = Site
		fields = ('name', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
