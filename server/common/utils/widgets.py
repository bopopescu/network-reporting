"""
Mopub HTML Widget classes
We separate out Widget templates for simplicity and modularity
"""
from django.forms.widgets import Widget, Textarea
from django.template import Context, loader
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

class MPWidget(Widget):
    DEFAULT_CLASSES = ""
    def __init__(self,required=False):
           # The 'rows' and 'cols' attributes are required for HTML correctness.
           self.required = required
           super(MPWidget, self).__init__()

    def render(self, name, value, attrs=None,errors=False):
        if value is None:
            value = ''
        
        classes = attrs.get('class') or ""
        if errors:
             classes += " form-error"
        
        if self.DEFAULT_CLASSES:
            classes += " " + self.DEFAULT_CLASSES

        attrs['class'] = classes

        flat_attrs = mark_safe(self.flatatt(attrs))

        context_dict = dict(widget = self, name = name, value = value, flat_attrs = flat_attrs)
        c = Context(context_dict)
        t = loader.get_template(self.TEMPLATE)
        return t.render(c)
  
    def flatatt(self, attrs):
        """
        Convert a dictionary of attributes to a single string.
        The returned string will contain a leading space followed by key="value",
        XML-style pairs.  It is assumed that the keys do not need to be XML-escaped.
        If the passed dictionary is empty, then return an empty string.
        """
        return u''.join([u' %s="%s"' % (k, conditional_escape(v)) for k, v in attrs.items()])
    
    def build_attrs(self, extra_attrs=None, **kwargs):
        "Helper function for building an attribute dictionary."
        attrs = dict(self.attrs, **kwargs)
        if extra_attrs:
            attrs.update(extra_attrs)
        return attrs

class MPTextarea(MPWidget):
    TEMPLATE = 'widgets/textarea.html'
    DEFAULT_CLASSES = "input-text"
    def __init__(self, cols=50, rows=3, required=False):
           # The 'rows' and 'cols' attributes are required for HTML correctness.
           self.cols = cols
           self.rows = rows
           super(MPTextarea, self).__init__(required=required)

class MPTextInput(MPWidget):
    TEMPLATE = 'widgets/text_input.html'
    DEFAULT_CLASSES = "input-text"

class MPRadioInput(MPWidget):
    TEMPLATE = 'widgets/adunit_device_format.html'
    DEFAULT_CLASSES = "input-text"

class MPFormatWidget(MPWidget):
    TEMPLATE = 'widgets/adunit_format.html'

class MPNumberInput(MPTextInput):
    TEMPLATE = 'widgets/number_input.html'
    DEFAULT_CLASSES = "input-text input-text-number"

