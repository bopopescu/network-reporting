import logging

from google.appengine.ext import db
from google.appengine.ext.db.djangoforms import ModelChoiceField

from django import forms
from django.forms.forms import BoundField
from django.forms.fields import FileField, CharField
from django.template import Context, loader
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.util import ValidationError, ErrorList
from django.forms.widgets import Textarea


class MPModelForm(forms.ModelForm):
    TEMPLATE = 'advertiser/forms/form.html'
  
    def __iter__(self):
        for name, field in self.fields.items():
            yield MPBoundField(self, field, name)

    def __getitem__(self, name):
        "Returns a BoundField with the given name."
        try:
            field = self.fields[name]
        except KeyError:
            raise KeyError('Key %r not found in Form' % name)
        return MPBoundField(self, field, name)    
        
    def add_context(self,context):
      if not hasattr(self,'_extra_context'):
        self._extra_context = {}
      self._extra_context.update(context)  
        
    def as_template(self):
        "Helper function for fieldsting fields data from form."
        bound_fields = [BoundField(self, field, name) for name, field in self.fields.items()]
        context_dict = dict(form = self, bound_fields = bound_fields)
        if hasattr(self,'_extra_context'):
          context_dict.update(self._extra_context)
        c = Context(context_dict)
        # TODO: check for template ... if template does not exist
        # we could just get_template_from_string to some default
        # or we could pass in the template name ... whatever we want
        # import pdb; pdb.set_trace()
        t = loader.get_template(self.TEMPLATE)
        return t.render(c)
        
class MPBoundField(BoundField):
    "A Field plus data by MoPub"
    @property
    def value(self):
        """
        Adds a value property that easily gets pre-filled data be it from
        the model or from previous user input
        """
        if not self.form.is_bound:
            value = self.form.initial.get(self.name, self.field.initial)
            if callable(value):
                value = value()
        else:
            if isinstance(self.field, FileField) and self.data is None:
                value = self.form.initial.get(self.name, self.field.initial)
            else:
                value = self.data
        return value or ''
        
class MPTextAreaField(CharField):
    widget = Textarea
    
    def clean(self,value):
      super(MPTextAreaField,self).clean(value)
      if value:
        value = [v for v in value.lower().replace('\r','\n').split('\n') if v] 
      return value
        
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