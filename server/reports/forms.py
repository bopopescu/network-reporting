import urllib2
import logging
from datetime import datetime, timedelta

from google.appengine.ext import db

from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from common.utils import date_magic
from reports.models import Report, ScheduledReport

APP = 'app'
AU = 'adunit'
CAMP = 'campaign'
CRTV = 'creative'
P = 'priority'
MO = 'month' #6
WEEK = 'week' #7
DAY = 'day' #8
HOUR = 'hour' #9
CO = 'country' #10
DEV = 'device' #11
OS = 'os' #12
KEY = 'kw' #13
CHOICES = [('','------------'), (APP, 'App'), (AU, 'Ad Unit'), (P, 'Priority'), (CAMP, 'Campaign'), (CRTV, 'Creative'), (MO, 'Month'), (WEEK, 'Week'), (DAY, 'Day'), (HOUR, 'Hour'),]# (CO, 'Country'), (DEV, 'Device'), (OS, 'Operating System'), (KEY, 'Keywords')]
TARG = 'targeting' # I don't know what this is

INT_CHCES = [('today', 'Today'), ('yesterday', 'Yesterday'), ('7days', 'Last 7 days'), ('lmonth', 'Last month'), ('custom', 'Custom')]
SCHED_CHCES = [('none', "Don't schedule"), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'), ('quarterly', 'Quarterly')]


class ReportForm(mpforms.MPModelForm):

    TEMPLATE = 'reports/forms/report_form.html'
    d1 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())
    d2 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())
    d3 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())
    interval = mpfields.MPChoiceField(choices=INT_CHCES, widget=mpwidgets.MPSelectWidget())
    sched_interval = mpfields.MPChoiceField(choices=SCHED_CHCES, widget=mpwidgets.MPSelectWidget())
    start = forms.Field()
    recipients = mpfields.MPTextField()

    def __init__(self, save_as=False,*args, **kwargs):
        instance = kwargs.get('instance', None)
        initial = kwargs.get('initial', {})
        self.save_as = save_as
        if instance and instance.days:
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
            start = self.cleaned_data['start']
            obj.days = obj.end - start
        if commit:
            obj.put()
        return obj
            

    class Meta:
        model = ScheduledReport
        fields = ('d1', 'd2', 'd3', 'end', 'days', 'name', 'interval', 'sched_interval', 'email', 'recipients')

