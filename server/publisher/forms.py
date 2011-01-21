from django import forms
from publisher.models import Site, App

class AppForm(forms.ModelForm):
	class Meta:
		model = App
		fields = ('name', 'app_type', 'url', 'package', 'description', 'adsense_app_name')

class SiteForm(forms.ModelForm):
	class Meta:
		model = Site
		fields = ('name', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords','width','height','format','adsense_channel_id')
