from google.appengine.ext import db
from common.utils import djangoforms
from common.utils import widgets as mpwidgets
from common.utils import fields as mpfields

class ChoiceProperty(db.StringProperty):

  def get_form_field(self, **kwargs):
    """Return a Django form field appropriate for a text property.

    This sets the widget default to forms.Textarea.
    """
    defaults = {'widget': mpwidgets.MPRadioInput}
    defaults.update(kwargs)
    return super(ChoiceProperty, self).get_form_field(**defaults)

