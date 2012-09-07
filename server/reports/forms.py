import logging
from datetime import timedelta, datetime, date
from common.utils.timezones import Pacific_tzinfo
from django import forms
from reports.models import ScheduledReport


DIMENSIONS = [
    ('','------------'),
    ('app', 'App'),
    ('adunit', 'Ad Unit'),
    ('priority', 'Priority'),
    ('campaign', 'Order'),
    ('adgroup', 'Line Item'),
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
    class Meta:
        model = ScheduledReport
        fields = ('name',
                  'd1',
                  'd2',
                  'd3',
                  'start',
                  'end',
                  'days',
                  'name',
                  'interval',
                  'sched_interval',
                  'recipients',
                  'saved')

    
    TEMPLATE = 'reports/forms/report_form.html'
    name = forms.CharField(
        label='Name:',
        widget=forms.TextInput(attrs={
            'class': 'required',
            'placeholder': 'Report Name'
        })
    )
    d1 = forms.ChoiceField(
        choices=DIMENSIONS,
        label='Report Breakdown:',
        widget=forms.Select(attrs={
            'class': 'chzn-select',
            'style': 'width:120px'
        })
    )
    d2 = forms.ChoiceField(
        choices=DIMENSIONS,
        required=False,
        label='>',
        widget=forms.Select(attrs={
            'class': 'chzn-select',
            'style': 'width:120px'
        })
    )
    d3 = forms.ChoiceField(
        choices=DIMENSIONS,
        required=False,
        label='>',
        widget=forms.Select(attrs={
            'class': 'chzn-select',
            'style': 'width:120px'
        })
    )
    interval = forms.ChoiceField(
        choices=(
            ('yesterday', 'Yesterday'),
            ('7days', 'Last 7 days'),
            ('lmonth', 'Last month'),
            ('custom', 'Custom')
        ),
        label='Dates:',
        widget=forms.Select(attrs={
            'class': 'chzn-select',
            'style': 'width:100px'
        })
    )
    start = forms.DateField(
        input_formats=('%m/%d/%Y',),
        widget=forms.DateInput(attrs={
            'class': 'date',
            'placeholder': 'MM/DD/YYYY'
        },format='%m/%d/%Y',)
    )
    end = forms.DateField(
        input_formats=('%m/%d/%Y',),
        widget=forms.DateInput(attrs={
            'class': 'date',
            'placeholder': 'MM/DD/YYYY'
        },format='%m/%d/%Y',)
    )
    
    # NOTE: days doesn't get rendered
    days = forms.IntegerField(required=False)
    recipients = forms.CharField(
        label='Recipients:',
        widget=forms.Textarea(attrs={
            'cols': 50,
            'rows': 3,
            'placeholder': 'E-mail addresses to receive report'
        })
    )
    sched_interval = forms.ChoiceField(
        choices=(
            ('none', "Don't schedule"),
            ('daily', 'Daily'),
            ('weekly', 'Weekly'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly')
        ),
        label='Schedule:',
        widget=forms.Select(attrs={
            'class': 'chzn-select',
            'style': 'width:200px'
        })
    )
    # NOTE: saved is a hidden field set by the js on form submission
    saved = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class':'hidden'
        })
    )

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        #Initially was just a check, making it an int check since
        #0 is a valid property, but evals to false
        if instance:
            if (instance.days or instance.days == 0):
                dt = timedelta(days=instance.days)
                initial.update(start=instance.end-dt)
                kwargs.update(initial=initial)
            if not instance.interval:
                initial.update(interval='custom')
                kwargs.update(initial=initial)

            initial.update(recipients=', '.join(instance.recipients))
            kwargs.update(initial=initial)

        super(ReportForm, self).__init__(*args, **kwargs)

    def clean_start(self):
        """
        Reports must be limited to three months
        """
        start = self.cleaned_data.get('start', None)
        end = self.cleaned_data.get('end', None)
        scheduled = self.cleaned_data.get('sched_interval')
        
        today = datetime.now(Pacific_tzinfo()).date()
        yesterday = today - timedelta(1)
        current_hour = datetime.now(Pacific_tzinfo()).hour
                
        if start and end:
            days = (end - start).days
            if days > 92:
                raise forms.ValidationError('Reports are limited to three months.')
        else:
            raise forms.ValidationError('Start and end dates are required.')

        if scheduled == 'none':
            
            # Unscheduled reports for today can't run because we don't
            # have the data yet.
            if start == today and end == today:
                message = 'Report data for today has not yet been generated.'
                raise forms.ValidationError(message)
            
            if (start == yesterday) and (end == yesterday) and current_hour <= 12:
                message = 'Report data for yesterday has not yet been generated.'
                raise forms.ValidationError(message)
            
        return start

    def clean_days(self):
        start = None
        end = None
        if self.data.get(self.prefix + '-start', None):
            start = datetime.strptime(self.data.get(self.prefix + '-start', None),
                    '%m/%d/%Y').date()
            end = self.cleaned_data.get('end', None)
        if not start or not end:
            raise forms.ValidationError('Start and end dates are required.')

        return (end - start).days

    def clean_recipients(self):
        recipients = self.cleaned_data.get('recipients', None)
        recipients = [r.strip() for r in recipients.replace('\r','\n').replace(',','\n'). \
                split('\n') if r] if recipients else []
        recipients = filter(None, recipients)
        logging.info(recipients)
        return recipients


