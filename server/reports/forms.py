import logging
from datetime import timedelta

from django import forms
from reports.models import ScheduledReport

DIMENSIONS = [('','------------'),
              ('app', 'App'),
              ('adunit', 'Ad Unit'),
              ('priority', 'Priority'),
              ('campaign', 'Campaign'),
              ('creative', 'Creative'),
              ('month', 'Month'),
              ('week', 'Week'),
              ('day', 'Day'),
              ('hour', 'Hour'),
              ('country', 'Country'),
              ('marketing', 'Device'),
              ('os', 'OS'),
              ('os_ver', 'OS Version'),
           ]



class ReportForm(forms.ModelForm):

    TEMPLATE = 'reports/forms/report_form.html'
    d1 = forms.ChoiceField(choices=DIMENSIONS,
                           label='Report Breakdown:')
    d2 = forms.ChoiceField(choices=DIMENSIONS,
                           label='>')
    d3 = forms.ChoiceField(choices=DIMENSIONS,
                           label='>')
    interval = forms.ChoiceField(choices=(('yesterday', 'Yesterday'),
                                          ('7days', 'Last 7 days'),
                                          ('lmonth', 'Last month'),
                                          ('custom', 'Custom')),
                                 label='Dates:')
    sched_interval = forms.ChoiceField(choices=(('none', "Don't schedule"),
                                                ('daily', 'Daily'),
                                                ('weekly', 'Weekly'),
                                                ('monthly', 'Monthly'),
                                                ('quarterly', 'Quarterly')),
                                       label='Schedule:')
    start = forms.DateTimeField(input_formats=('%m/%d/%Y %I:%M %p',),
                                         label='Start:', required=False,
                                         widget=forms.DateInput(attrs={'class': 'date',
                                                                       'placeholder': 'MM/DD/YYYY'},
                                                                format='%m/%d/%Y',))
    recipients = forms.CharField(label='Recipients:',
                           widget=forms.TextInput())

    def __init__(self, save_as=False,*args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        self.save_as = save_as
        #Initially was just a check, making it an int check since
        #0 is a valid property, but evals to false
        if instance and (instance.days or instance.days == 0):
            dt = timedelta(days=instance.days)
            initial.update(start=instance.end-dt)
            kwargs.update(initial = initial)
        if instance and not instance.interval:
            initial.update(interval='custom')
            kwargs.update(initial = initial)
        super(ReportForm, self).__init__(*args, **kwargs)


    def save(self, commit=True):
        obj = super(ReportForm, self).save(commit=False)
        if obj:
            logging.info("\n\n\n\n\n:%s"%self.cleaned_data)
            start = self.cleaned_data['start']
            obj.days = obj.end - start
        if commit:
            obj.put()
        return obj


    class Meta:
        model = ScheduledReport
        fields = ('d1', 'd2', 'd3', 'end', 'days', 'name', 'interval', 'sched_interval', 'recipients')

