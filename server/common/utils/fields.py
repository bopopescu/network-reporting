import logging

from google.appengine.ext import db
from django import forms

from django.forms.models import ModelChoiceField
from django.forms.fields import FileField, CharField, FloatField, ChoiceField
from django.template import Context, loader
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.util import ValidationError, ErrorList
from django.forms.widgets import Textarea

from common.utils import widgets as mpwidgets
        
"""
These are used to make custom fields with widgets.
To find the default widgets for a property, look in djangoforms
"""        

class MPTextareaField(CharField):
    widget = mpwidgets.MPTextarea

class MPKeywordsField(CharField):
    widget = mpwidgets.MPTextarea

    def clean(self,value):
      value = super(MPKeywordsField,self).clean(value)
      if value:
        value = [v for v in value.lower().replace('\r','\n').split('\n') if v] 
      return value
      
class MPTextField(CharField):
    widget = mpwidgets.MPTextInput
    
class MPFloatField(FloatField):
    widget = mpwidgets.MPNumberInput

class MPChoiceField(ChoiceField):
    widget = mpwidgets.MPRadioInput
    
    
class MPModelMultipleChoiceField(ModelChoiceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""
    
    widget = forms.SelectMultiple
    
    default_error_messages = {
        'list': _(u'Enter a list of values.'),
        'invalid_choice': _(u'Select a valid choice. %s is not one of the'
                            u' available choices.'),
        'invalid_pk_value': _(u'"%s" is not a valid value for a primary key.')
    }

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
        return [db.Key(v) for v in value]