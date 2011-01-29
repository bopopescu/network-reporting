import logging

from google.appengine.ext import db

from django import forms
from django.forms.forms import BoundField
from django.forms.fields import FileField, CharField
from django.forms.models import ModelChoiceField
from django.template import Context, loader
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.util import ValidationError, ErrorList
from django.forms.widgets import SelectMultiple, Textarea


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
        import logging
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
        Adds a value property that easily get pre-filled data be it from
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
      value = [v for v in value.lower().replace('\r','\n').split('\n') if v] 
      return value
        
class MPModelMultipleChoiceField(ModelChoiceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""
    widget = SelectMultiple
    # hidden_widget = MultipleHiddenInput
    default_error_messages = {
        'list': _(u'Enter a list of values.'),
        'invalid_choice': _(u'Select a valid choice. %s is not one of the'
                            u' available choices.'),
        'invalid_pk_value': _(u'"%s" is not a valid value for a primary key.')
    }

    def __init__(self, queryset, cache_choices=False, required=True,
                 widget=None, label=None, initial=None,
                 help_text=None, *args, **kwargs):
        super(MPModelMultipleChoiceField, self).__init__(queryset, None,
            cache_choices, required, widget, label, initial, help_text,
            *args, **kwargs)

    def clean(self, value):
        if self.required and not value:
            raise ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise ValidationError(self.error_messages['list'])
            
        qs = self.queryset
        qs = [o for o in qs if force_unicode(o.key()) in value]
        keys = set([force_unicode(o.key()) for o in qs])
        for val in value:
            if force_unicode(val) not in keys:
                raise ValidationError(self.error_messages['invalid_choice'] % val)
        return [db.Key(k) for k in keys]