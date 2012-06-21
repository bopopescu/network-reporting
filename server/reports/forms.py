import logging
from datetime import timedelta, \
        datetime

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
    name = forms.CharField(label='Name:',
                           widget=forms.TextInput(attrs={'class': 'required',
                                                         'placeholder': 'Report Name'}))
    d1 = forms.ChoiceField(choices=DIMENSIONS,
                           label='Report Breakdown:',
                           widget=forms.Select(attrs={'class': 'chzn-select'}))
    d2 = forms.ChoiceField(choices=DIMENSIONS,
                           required=False,
                           label='>',
                           widget=forms.Select(attrs={'class': 'chzn-select'}))
    d3 = forms.ChoiceField(choices=DIMENSIONS,
                           required=False,
                           label='>',
                           widget=forms.Select(attrs={'class': 'chzn-select'}))
    interval = forms.ChoiceField(choices=(('yesterday', 'Yesterday'),
                                          ('7days', 'Last 7 days'),
                                          ('lmonth', 'Last month'),
                                          ('custom', 'Custom')),
                                 label='Dates:',
                                 widget=forms.Select(attrs={'class': 'chzn-select'}))
    start = forms.DateField(input_formats=('%m/%d/%Y',),
                            widget=forms.DateInput(attrs={'class': 'date',
                                                          'placeholder': 'MM/DD/YYYY'},
                                                   format='%m/%d/%Y',))
    end = forms.DateField(input_formats=('%m/%d/%Y',),
                          widget=forms.DateInput(attrs={'class': 'date',
                                                        'placeholder': 'MM/DD/YYYY'},
                                                 format='%m/%d/%Y',))
    # NOTE: days doesn't get rendered
    days = forms.IntegerField(required=False)
    recipients = forms.CharField(label='Recipients:',
                                 widget=forms.Textarea(attrs={'cols': 50,
                                                              'rows': 3,
                                                              'placeholder': 'E-mail addresses to receive report'}))
    sched_interval = forms.ChoiceField(choices=(('none', "Don't schedule"),
                                                ('daily', 'Daily'),
                                                ('weekly', 'Weekly'),
                                                ('monthly', 'Monthly'),
                                                ('quarterly', 'Quarterly')),
                                       label='Schedule:',
                                       widget=forms.Select(attrs={'class': 'chzn-select'}))

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
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

    def clean_start(self):
        """
        Reports must be limited to three months
        """
        start = self.initial.get('start', None)
        end = self.initial.get('end', None)
        if start and end:
            days = (end - start).days
            if days > 92:
                raise forms.ValidationError('Please limit reports to three months.')
        logging.info('START')
        logging.info(start)
        return start

    def clean_days(self):
        start = self.initial.get('start', None)
        end = self.initial.get('end', None)

        return (end - start).days

    def clean_recipients(self):
        recipients = self.initial.get('recipients', None)
        recipients = [r.strip() for r in recipients.replace('\r','\n').replace(',','\n'). \
                split('\n') if r] if recipients else []
        recipients = filter(None, recipients)
        return recipients

    class Meta:
        model = ScheduledReport
        fields = ('name', 'd1', 'd2', 'd3', 'start', 'end', 'days', 'name', 'interval', 'sched_interval', 'recipients')

