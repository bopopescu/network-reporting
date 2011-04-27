import urllib2
import logging

from google.appengine.ext import db

from django import forms
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from reports.models import Report


class ReportForm(mpforms.MPModelForm):
    TEMPLATE = 'reports/forms/report_form.html'

    d1 = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget)
    d2 = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget)
    d3 = mpfields.MPChoiceField(choices=[('normal','Normal'),('backfill','Backfill')],widget=mpwidgets.MPSelectWidget)
    class Meta:
        model = Report
        fields = ('d1', 'd2', 'd3', 'start', 'end', 'name')

