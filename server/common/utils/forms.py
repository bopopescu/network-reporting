import logging

from google.appengine.ext import db

from django import forms
from django.forms.forms import BoundField
from django.forms.fields import FileField, CharField
from django.template import Context, loader
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _, ugettext
from django.forms.util import ValidationError, ErrorList
from django.forms.widgets import Textarea

class MPBoundField(BoundField):
    """"A Field plus data by MoPub."""
    TEMPLATE = "common/bound_field.html"

    def __unicode__(self):
        """Renders this field as an HTML widget with label and errors."""

        if self.field.show_hidden_initial:
            rendered_widget = self.as_widget(attrs=self.attrs) + self.as_hidden(only_initial=True)
        else:
            rendered_widget = self.as_widget(attrs=self.attrs)

        context_dict = dict(widget = rendered_widget,
                           errors = self.errors,
                           label = self.label,
                           field = self.field)
        c = Context(context_dict)
        t = loader.get_template(self.TEMPLATE)
        return t.render(c)


    def __init__(self, form, field, name, *args, **kwargs):
        self.attrs={}
        self.raw = False

        if field.required:
             self.attrs['class'] = "required"
        super(MPBoundField,self).__init__(form, field, name, *args, **kwargs)

    def add_attrs(self, attrs):
        for key in attrs.keys():
            if key == "label":
                self.add_label(attrs[key])
                continue
            if self.attrs.get(key):
                self.attrs[key] = attrs[key] + ' ' + self.attrs[key]
            else:
                self.attrs[key] = attrs[key]

    def add_label(self, label):
        self.label = label

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
        return value if value != None else ''

    def as_widget(self, widget=None, attrs=None, only_initial=False):
        """
        Renders the field by rendering the passed widget, adding any HTML
        attributes passed as attrs.  If no widget is specified, then the
        field's default widget will be used.
        """
        if not widget:
            widget = self.field.widget

        attrs = attrs or {}
        auto_id = self.auto_id
        if auto_id and 'id' not in attrs and 'id' not in widget.attrs:
            if not only_initial:
                attrs['id'] = auto_id
            else:
                attrs['id'] = self.html_initial_id

        if not self.form.is_bound:
            data = self.form.initial.get(self.name, self.field.initial)
            if callable(data):
                data = data()
        else:
            if isinstance(self.field, FileField) and self.data is None:
                data = self.form.initial.get(self.name, self.field.initial)
            else:
                data = self.data
        data = self.field.prepare_value(data)

        if not only_initial:
            name = self.html_name
        else:
            name = self.html_initial_name
        # pass error to mpforms but not to normal django forms
        try:
            return widget.render(name, data, attrs=attrs, errors=self.errors)
        except Exception, e:
            return widget.render(name, data, attrs=attrs)
        return widget.render(name, data, attrs=attrs, errors=bool(self.errors))


class MPForm(forms.Form):
    TEMPLATE = ''

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
      "Helper function for producing fields data from form."
      bound_fields = [MPBoundField(self, field, name) for name, field in self.fields.items()]
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

    def _html_output(self, normal_row, error_row, row_ender, help_text_html, errors_on_separate_row):
            "Helper function for outputting HTML. Used by as_table(), as_ul(), as_p()."
            top_errors = self.non_field_errors() # Errors that should be displayed above all fields.
            output, hidden_fields = [], []

            for name, field in self.fields.items():
                html_class_attr = ''
                bf = MPBoundField(self, field, name)
                bf_errors = self.error_class([conditional_escape(error) for error in bf.errors]) # Escape and cache in local variable.
                if bf.is_hidden:
                    if bf_errors:
                        top_errors.extend([u'(Hidden field %s) %s' % (name, force_unicode(e)) for e in bf_errors])
                    hidden_fields.append(unicode(bf))
                else:
                    # Create a 'class="..."' atribute if the row should have any
                    # CSS classes applied.
                    css_classes = bf.css_classes()
                    if css_classes:
                        html_class_attr = ' class="%s"' % css_classes

                    if errors_on_separate_row and bf_errors:
                        output.append(error_row % force_unicode(bf_errors))

                    if bf.label:
                        label = conditional_escape(force_unicode(bf.label))
                        # Only add the suffix if the label does not end in
                        # punctuation.
                        if self.label_suffix:
                            if label[-1] not in ':?.!':
                                label += self.label_suffix
                        label = bf.label_tag(label) or ''
                    else:
                        label = ''

                    if field.help_text:
                        help_text = help_text_html % force_unicode(field.help_text)
                    else:
                        help_text = u''

                    output.append(normal_row % {
                        # 'errors': force_unicode(bf_errors),
                        # 'label': force_unicode(label),
                        'field': unicode(bf),
                        'help_text': help_text,
                        'html_class_attr': html_class_attr
                    })

            if top_errors:
                output.insert(0, error_row % force_unicode(top_errors))

            if hidden_fields: # Insert any hidden fields in the last row.
                str_hidden = u''.join(hidden_fields)
                if output:
                    last_row = output[-1]
                    # Chop off the trailing row_ender (e.g. '</td></tr>') and
                    # insert the hidden fields.
                    if not last_row.endswith(row_ender):
                        # This can happen in the as_p() case (and possibly others
                        # that users write): if there are only top errors, we may
                        # not be able to conscript the last row for our purposes,
                        # so insert a new, empty row.
                        last_row = (normal_row % {'errors': '', 'label': '',
                                                  'field': '', 'help_text':'',
                                                  'html_class_attr': html_class_attr})
                        output.append(last_row)
                    output[-1] = last_row[:-len(row_ender)] + str_hidden + row_ender
                else:
                    # If there aren't any rows in the output, just append the
                    # hidden fields.
                    output.append(str_hidden)
            return mark_safe(u'\n'.join(output))

    def as_template(self):
        "Helper function for producing fields data from form."
        bound_fields = [MPBoundField(self, field, name) for name, field in self.fields.items()]
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
