import logging, datetime

from urllib import urlencode
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from reports.query_managers import ReportQueryManager


class ReportIndexHandler(RequestHandler):
    def get(self):
        manager = ReportQueryManager(self.account)
        saved = manager.get_saved()
        history = manager.get_history()
        
        return render_to_response(self.request, 'reports/report_index.html',
                dict(saved      = saved,
                     history    = history
                     ))

@whitelist_login_required
def report_index(request, *args, **kwargs):
    return ReportIndexHandler()(request, *args, **kwargs)


class AddReportHandler(RequestHandler):
    def get(self)
        pass
    def post(self, d1, d2=None, d3=None, start, end, name=None, saved=False)
        pass

@whitelist_login_required
def add_report(request, *args, **kwargs):
    return AddReportHandler()(request, *args, **kwargs)

class ViewReportHandler(RequestHandler):
    def get(self, d1, d2=None, d3=None, start, end):
        manager = ReportQueryManager(self.account)
        rep = manager.get_report(d1, d2, d3, start, end, view=True)
        return render_to_response(self.request, 'reports/show_report.html',
                dict( report = rep))



@whitelist_login_required
def view_report(request, *args, **kwargs):
    return ViewReportHandler()(request, *args, **kwargs)


class CheckReportHandler(RequestHandler):
    def get(self):
        pass

@whitelist_login_required
def check_report(request, *args, **kwargs):
    return CheckReportHandler()(request, *args, **kwargs)



