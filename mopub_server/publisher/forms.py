from django import forms
from publisher.models import Site

class SiteForm(forms.ModelForm):
	class Meta:
		model = Site
		fields = ('name', 'url', 'description', 'ad_type', 'backfill', 'backfill_threshold_cpm', 'keywords')
