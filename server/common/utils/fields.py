import logging

from google.appengine.ext import db
from django import forms

from django.forms.models import ModelChoiceField
from django.forms.fields import FileField, CharField, FloatField
from django.template import Context, loader
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.util import ValidationError, ErrorList
from django.forms.widgets import Textarea

from common.utils import widgets as mpwidgets
        
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


class MPModelMultipleChoiceField(ModelChoiceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""
    
    widget = forms.SelectMultiple
    
    default_error_messages = {
        'list': _(u'Enter a list of values.'),
        'invalid_choice': _(u'Select a valid choice. %s is not one of the'
                            u' available choices.'),
        'invalid_pk_value': _(u'"%s" is not a valid value for a primary key.')
    }

    def __init__(self, reference_class, query=None, choices=None,
                 empty_label=u'---------',
                 required=True, widget=forms.SelectMultiple, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        super(MPModelMultipleChoiceField,self).\
              __init__(reference_class,query,choices,
                       empty_label,
                       required,widget,label,initial,
                       help_text,*args,**kwargs)         


    def clean(self, value):
        import logging
        logging.info('self.required:%s'%self.required)
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
        return [db.Key(v) for v in value]