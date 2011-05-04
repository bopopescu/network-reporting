import logging, datetime

from urllib import urlencode

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson
from django.template import loader
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils.decorators import whitelist_login_required
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from reports.forms import ReportForm
from reports.query_managers import ReportQueryManager

from reports.forms import ReportForm


class ReportIndexHandler(RequestHandler):
    def get(self):
        manager = ReportQueryManager(self.account)
        saved = manager.get_saved()
        history = manager.get_history()
        common = manager.get_common_reports()
        form_frag = ReportForm()
        return render_to_response(self.request, 'reports/report_index.html',
                dict(saved      = saved,
                     history    = history,
                     common     = common,
                     report_fragment = form_frag,
                     ))

@whitelist_login_required
def report_index(request, *args, **kwargs):
    return ReportIndexHandler()(request, *args, **kwargs)


class AddReportHandler(RequestHandler):
    TEMPLATE = 'reports/report_create_form.html'
    def get(self):
        report_form = ReportForm()
        return render_to_response(self.request,
                                 self.TEMPLATE, 
                                 dict(report_form=report_form))

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request, template_name=template_name, data=kwargs)
        
    def post(self, d1, start, end, d2=None, d3=None,name=None, saved=False):
        start = datetime.datetime.strptime(start, '%m/%d/%Y').date()
        end = datetime.datetime.strptime(end, '%m/%d/%Y').date()
        man = ReportQueryManager(self.account)
        if saved == "True":
            saved = True
        else:
            saved = False
        man.add_report(d1, d2, d3, start, end, name=name, saved=saved)
        return HttpResponseRedirect(reverse('reports_index'))

@whitelist_login_required
def add_report(request, *args, **kwargs):
    return AddReportHandler()(request, *args, **kwargs)


class RequestReportHandler(RequestHandler):
    def get(self):
        return None
        
    def post(self, d1, start, end, d2=None, d3=None):
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
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report)
        man.put(report)
        report.data = report.gen_data()
        logging.warning(report.data)
        report.status = 'done'
        report.completed_at = datetime.datetime.now()
        man.put_report(report)
        return HttpResponse('Report Generation Successful')
    def get(self):
        pass

def gen_report(request, *args, **kwargs):
    return GenReportHandler()(request, *args, **kwargs)


class ViewReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report_key)
        report_frag = ReportForm(instance=report)
        return render_to_response(self.request, 'reports/view_report.html',
                dict(report=report,
                     report_fragment = report_frag,))
    def post(self, *args, **kwargs):
        logging.warning("\n\nApathy\n\n")
        return

@whitelist_login_required
def view_report(request, *args, **kwargs):
    return ViewReportHandler()(request, *args, **kwargs)
