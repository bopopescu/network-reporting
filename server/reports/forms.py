import urllib2
import logging

from google.appengine.ext import db

from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from reports.models import Report

APP = 'app'
AU = 'adunit'
CAMP = 'campaign'
CRTV = 'creative'
P = 'priority'
MO = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'
CO = 'country'
DEV = 'device'
OS = 'os'
KEY = 'kw'
CHOICES = [('','------------'), (APP, 'App'), (AU, 'Ad Unit'), (CAMP, 'Campaign'), (CRTV, 'Creative'), (P, 'Priority'), (MO, 'Month'), (WEEK, 'Week'), (DAY, 'Day'), (HOUR, 'Hour'), (CO, 'Country'),] #(DEV, 'Device'), (OS, 'Operating System'), (KEY, 'Keywords')]
TARG = 'targeting' # I don't know what this is


class ReportForm(mpforms.MPModelForm):

    TEMPLATE = 'reports/forms/report_form.html'
    d1 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())
    d2 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())
    d3 = mpfields.MPChoiceField(choices=CHOICES,widget=mpwidgets.MPSelectWidget())

    class Meta:
        model = Report
        fields = ('d1', 'd2', 'd3', 'start', 'end', 'name')

