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
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from reports.forms import ReportForm
from reports.models import ScheduledReport
from reports.query_managers import ReportQueryManager


from reports.forms import ReportForm


class ReportIndexHandler(RequestHandler):
    def get(self):
        manager = ReportQueryManager(self.account)
        saved = manager.get_saved()
        scheduled = manager.get_scheduled()
        report_form = ReportForm(initial={'recipients':self.request.user.email})
        return render_to_response(self.request, 'reports/report_index.html',
                dict(scheduled  = scheduled,
                     report_fragment = report_form,
                     ))

@login_required
def report_index(request, *args, **kwargs):
    return ReportIndexHandler()(request, *args, **kwargs)


class AddReportHandler(RequestHandler):
    TEMPLATE = 'reports/report_create_form.html'
    def get(self):
        report_form = ReportForm(initial={'recipients':[self.user.email]})
        return render_to_response(self.request,
                                 self.TEMPLATE, 
                                 dict(report_form=report_form))

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request, template_name=template_name, data=kwargs)
        
    def post(self, d1, end, days=None, start=None, d2=None, d3=None,
                            name=None, saved=False, interval=None, 
                            sched_interval=None, recipients=None):

        end = datetime.datetime.strptime(end, '%m/%d/%Y').date()
        if start:
            start = datetime.datetime.strptime(start, '%m/%d/%Y').date()
            days = (end - start).days
        man = ReportQueryManager(self.account)
        if saved == "True" or saved == 'true':
            saved = True
        else:
            saved = False
        
        recipients = [r.strip() for r in recipients.replace('\r','\n').replace(',','\n').split('\n') if r] if recipients else []    
            
        report = man.add_report(d1, 
                                d2,
                                d3, 
                                end, 
                                days, 
                                name = name, 
                                saved = saved, 
                                interval = interval,
                                sched_interval = sched_interval,
                                recipients = recipients,
                                )
        return HttpResponseRedirect('/reports/view/'+str(report.key()))

@login_required
def add_report(request, *args, **kwargs):
    return AddReportHandler()(request, *args, **kwargs)


class RequestReportHandler(RequestHandler):
    def get(self):
        return None
        
    def post(self, d1, start, end, d2=None, d3=None):
        manager = ReportQueryManager(self.account)
        rep = manager.get_report(d1, d2, d3, start, end, view=True)
        #redirect to view handler

@login_required
def request_report(request, *args, **kwargs):
    return RequestReportHandler()(request, *args, **kwargs)


class CheckReportHandler(RequestHandler):
    def get(self, report_key):
        man = ReportQueryManager(self.account)
        #Sched is false, this is a standard report
        report = man.get_report_by_key(report_key)
        data = report.html_data
        ret = {}
        if data is None:
            #Not going to do this now
            #ret['map-status'], ret['shuf-status'], ret['red-status'] = MapReduceQueryManager.get_mr_status(type='report', key=report_key)
            data = 'none'
        ret['data'] = data
        return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

@login_required
def check_report(request, *args, **kwargs):
    return CheckReportHandler(use_cache=False)(request, *args, **kwargs)

#Only scheduled reports get viewed
class ViewReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report_key, sched=True)
        report_frag = ReportForm(instance=report, save_as=True)
        return render_to_response(self.request, 'reports/view_report.html',
                dict(report=report.most_recent,
                     report_fragment = report_frag,))
    def post(self, report_key, save=False):
        return

@login_required
def view_report(request, *args, **kwargs):
    return ViewReportHandler()(request, *args, **kwargs)


class SaveReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report_key)
        report.schedule.saved = True
        man.put_report(report.schedule)
        return HttpResponse('K')

@login_required
def save_report(request, *args, **kwargs):
    return SaveReportHandler()(request, *args, **kwargs)



class RunReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.new_report(report_key)
        return HttpResponseRedirect('/reports/view/'+str(report.schedule.key()))

@login_required
def run_report(request, *args, **kwargs):
    return RunReportHandler()(request, *args, **kwargs)


class ScheduledRunner(RequestHandler):
    def get(self):
        man = ReportQueryManager()
        now = datetime.datetime.now().date()
        reps = ScheduledReport.all().filter('next_sched_date =', now)
        for rep in reps:
            man.new_report(rep)
        return HttpResponse("Scheduled reports have been created")

def sched_runner(request, *args, **kwargs):
    return ScheduledRunner()(request, *args, **kwargs)
