import logging, datetime

from urllib import urlencode

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson
from django.template import loader
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from mail.mails import REPORT_FINISHED_SIMPLE
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
        defaults, adding_reps = manager.get_default_reports()
        scheduled = defaults + scheduled
        if adding_reps:
            self.request.flash['generating_defaults'] = "Default reports are currently being generated, you will be notified when they are completed."
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
                            sched_interval=None, recipients=None, report_key=None):
        if not d2:
            d2 = None
        if not d3:
            d3 = None

        end = datetime.datetime.strptime(end, '%m/%d/%Y').date() if end else None
        if start:
            start = datetime.datetime.strptime(start, '%m/%d/%Y').date()
            days = (end - start).days
            if days > 31:
                self.request.flash['error'] = 'Please limit reports to one months worth of data.'
                return HttpResponseRedirect('/reports/')
        edit = False
        man = ReportQueryManager(self.account)
        if report_key is not None:
            logging.info("there is a report key")
            edit = True
            report = man.get_report_data_by_key(report_key)
            if d1 == report.d1 and d2 == report.d2 and d3 == report.d3 and start == report.start and end == report.end:
                # All the actual data dims are the same, edit the sched settings
                sched = report.schedule
                sched.name = name
                sched.sched_interval = sched_interval
                sched.put()
                return HttpResponseRedirect('/reports/view/%s/' % sched.key())

        saved = True
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
        if edit:
            self.request.flash['report_edit'] = 'The requested edit requires the report to be re-run.  The request has been submitted and you will be notified via email when it has completed'
        else:
            self.request.flash['report_success'] = 'Your report has been successfully submitted, you will be notified via email when it has completed!'
        return HttpResponseRedirect('/reports/')

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
        report = man.get_report_data_by_key(report_key)
        data = report.html_data
        ret = {}
        if data is None:
            #Not going to do this now
            #ret['map-status'], ret['shuf-status'], ret['red-status'] = MapReduceQueryManager.get_mr_status(type='report', key=report_key)
            data = 'none'
        ret['data'] = data
        return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

def check_report(request, *args, **kwargs):
    return CheckReportHandler()(request, use_cache=False, *args, **kwargs)

#Only scheduled reports get viewed
class ViewReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report_key)
        report_frag = ReportForm(initial = {'recipients': self.request.user.email}, instance=report, save_as=True)
        return render_to_response(self.request, 'reports/view_report.html',
                dict(report=report.most_recent,
                     report_fragment = report_frag,))

@login_required
def view_report(request, *args, **kwargs):
    return ViewReportHandler()(request, *args, **kwargs)


class SaveReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_data_by_key(report_key)
        report.schedule.saved = True
        man.put_report(report.schedule)
        return HttpResponse('K')

@login_required
def save_report(request, *args, **kwargs):
    return SaveReportHandler()(request, *args, **kwargs)



class RunReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        sched = man.get_report_data_by_key(report_key).schedule
        report = man.new_report(sched)
        return HttpResponseRedirect('/reports/view/'+str(report.schedule.key()))

@login_required
def run_report(request, *args, **kwargs):
    return RunReportHandler()(request, *args, **kwargs)


class ScheduledRunner(RequestHandler):
    def get(self, now=None):
        man = ReportQueryManager()
        if now is None:
            now = datetime.datetime.now().date()
        else:
            now = datetime.datetime.strptime(now, '%y%m%d')
        reps = ScheduledReport.all().filter('next_sched_date =', now)
        for rep in reps:
            man.new_report(rep, sched=True)
        return HttpResponse("Scheduled reports have been created")

def sched_runner(request, *args, **kwargs):
    return ScheduledRunner(login=False)(request, *args, **kwargs)



class ReportExporter(RequestHandler):
    def post(self, report_key, account_key, f_type, *args, **kwargs):
        return sswriter.write_report(f_type, report_key, account_key)

def exporter(request, *args, **kwargs):
    return ReportExporter()(request, *args, **kwargs)

class ReportStateUpdater(RequestHandler):
    def post(self, action='delete'):
        keys = self.request.POST.getlist('reportChangeStateForm-key') or []
        logging.warning(action)
        logging.warning(keys)
        if keys:
            qm = ReportQueryManager()
            reports = [qm.get_report_by_key(key) for key in keys]
            reports = [update_report(report, action) for report in reports]
            qm.put_report(reports)
        return HttpResponseRedirect(reverse('reports_index'))

def update_report_state(request, *args, **kwargs):
    return ReportStateUpdater()(request, *args, **kwargs)

def update_report(report, action):
    if action == 'delete':
        report.deleted = True
    return report
