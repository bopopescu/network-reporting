from django import forms


class CustomizableSplitDateTimeWidget(forms.SplitDateTimeWidget):
    def __init__(self, date_attrs=None, time_attrs=None, date_format=None, time_format=None):
        widgets = (forms.DateInput(attrs=date_attrs, format=date_format),
                   forms.TimeInput(attrs=time_attrs, format=time_format))
        super(forms.SplitDateTimeWidget, self).__init__(widgets)
