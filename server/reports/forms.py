import urllib2
import loggin

from google.appengine.ext import db

from django import forms
from django.cor.urlresolvers import reverse
from common.utils import forms as mpforms
from common.utils import fields as mpfields
from common.utils import widgets as mpwidgets
from reports.models import Report


class ReportForm(mpforms.MPModelForm):
    TEMPLATE = 'reports/forms/report_form.html'

    class Meta:
        model = Report
        fields = ('d1', 'd2', 'd3', 'start', 'end', 'name')

