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
from common.utils.request_handler import RequestHandler
from common.utils.decorators import whitelist_login_required

from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from reports.query_managers import ReportQueryManager
from reports.build_report import build_report



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
    def get(self):
        pass
    #should do this with forms (ugh)
    def post(self, d1, start, end, d2=None, d3=None,name=None, saved=False):
        pass

@whitelist_login_required
def add_report(request, *args, **kwargs):
    return AddReportHandler()(request, *args, **kwargs)

class RequestReportHandler(RequestHandler):
    #shoudl do this with forms...
    def get(self, d1, start, end, d2=None, d3=None):
        manager = ReportQueryManager(self.account)
        rep = manager.get_report(d1, d2, d3, start, end, view=True)
        #redirect to view handler


@whitelist_login_required
def request_report(request, *args, **kwargs):
    return RequestReportHandler()(request, *args, **kwargs)


class CheckReportHandler(RequestHandler):
    def get(self):
        pass

@whitelist_login_required
def check_report(request, *args, **kwargs):
    return CheckReportHandler()(request, *args, **kwargs)


class GenReportHandler(RequestHandler):
    def post(self, report):
        build_report(report)
        return HttpResponse('Report Generation Successful')
    def get(self):
        pass

def gen_report(request, *args, **kwargs):
    return GenReportHandler()(request, *args, **kwargs)


class ViewReportHandler(RequestHandler):
    def get(self, *args, **kwargs):
        logging.warning("\n\nTrying to view stuff\n\n")
        return
    def post(self, *args, **kwargs):
        logging.warning("\n\nApathy\n\n")
        return

@whitelist_login_required
def view_report(request, *args, **kwargs):
    return ViewReportHandler()(request, *args, **kwargs)
