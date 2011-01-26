from django import forms
from django.forms.forms import BoundField
from django.forms.fields import FileField
from django.template import Context, loader

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
        
    def as_template(self):
        "Helper function for fieldsting fields data from form."
        bound_fields = [BoundField(self, field, name) for name, field in self.fields.items()]
        c = Context(dict(form = self, bound_fields = bound_fields))
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
        