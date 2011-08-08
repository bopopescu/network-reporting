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
        defaults = manager.get_default_reports()
        scheduled = defaults + scheduled
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
        report_form = ReportForm()
        return render_to_response(self.request,
                                 self.TEMPLATE, 
                                 dict(report_form=report_form))

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request, template_name=template_name, data=kwargs)
        
    def post(self, d1, end=None, days=None, start=None, d2=None, d3=None,name=None, saved=False, interval=None, sched_interval=None, report_key=None, email=False, recipients=None):
        end = datetime.datetime.strptime(end, '%m/%d/%Y').date() if end else None
        if start:
            start = datetime.datetime.strptime(start, '%m/%d/%Y').date()
            days = (end - start).days
        man = ReportQueryManager(self.account)

        recipients = [r.strip() for r in recipients.replace('\r', '\n').replace(',','\n').split('\n') if r] if recipients else []

        if report_key:
            report = man.get_report_by_key(report_key)
            sched = report.schedule
            if saved == 'True' or saved == 'true':
                new_rep = man.clone_report(report)
                new_sched = man.clone_report(sched, sched=True)
                new_sched.email = email
                new_sched.sched_interval = sched_interval
                new_sched.name = name
                new_sched.put()
                new_rep.schedule = new_sched
                new_rep.put()
                ##Return to index
                return HttpResponseRedirect('/reports/')
            #This is an edit
            else:
                if not sched.default:
                    sched.deleted = True
                sched.put()
                report = man.add_report(d1, 
                                    d2,
                                    d3, 
                                    end, 
                                    days, 
                                    name = name, 
                                    interval = interval,
                                    sched_interval = sched_interval,
                                    recipients = recipients,
                                    )
                return HttpResponseRedirect('/reports/view/'+str(report.key()))
        #Traditional report add
        else:
            report = man.add_report(d1, 
                                    d2,
                                    d3, 
                                    end, 
                                    days, 
                                    name = name, 
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
        report = man.get_report_by_key(report_key)
        data = report.html_data
        if data is None:
            data = 'none'
        ret = dict(data = data)
        return HttpResponse(simplejson.dumps(ret), mimetype='application/json')

@login_required
def check_report(request, *args, **kwargs):
    return CheckReportHandler()(request, *args, **kwargs)

def gen_report_worker(report, account):
    man = ReportQueryManager()
    report = man.get_report_by_key(report)
    report.status = 'pending'
    man.put_report(report)
    sched = report.schedule
    sched.last_run = datetime.datetime.now()
    man.put_report(sched)
    report.data = report.gen_data()
    if report.email:
        mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                 subject = 'Your report has completed')
        mesg_dict = dict(report_key = str(sched.key()))
        mesg.body = REPORT_FINISHED_SIMPLE % mesg_dict
        for recip in report.recipients:
            mesg.to = recip
            try:
                mesg.send()
            except InvalidEmailError:
                pass

    report.status = 'done'
    report.completed_at = datetime.datetime.now()
    man.put_report(report)
    return

#Only actual reports call this
class GenReportHandler(RequestHandler):
    def post(self, report, account):
        gen_report_worker(report, account)
        return HttpResponse('Report Generation Successful')

    def get(self, report):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report)
        report.status = 'pending'
        man.put_report(report)
        sched = report.schedule
        sched.last_run = datetime.datetime.now()
        man.put_report(sched)
        report.data = report.gen_data()
        report.status = 'done'
        report.completed_at = datetime.datetime.now()
        man.put_report(report)
        return HttpResponse('Report Generation Successful')

def gen_report(request, *args, **kwargs):
    return GenReportHandler()(request, use_cache=False, *args, **kwargs)

#Only scheduled reports get viewed
class ViewReportHandler(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        man = ReportQueryManager(self.account)
        report = man.get_report_by_key(report_key, sched=True)
        report_frag = ReportForm(initial = {'recipients': self.request.user.email}, instance=report, save_as=True)
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
            reports = [qm.get_report_by_key(key, sched=True) for key in keys]
            reports = [update_report(report, action) for report in reports]
            qm.put_report(reports)
        return HttpResponseRedirect(reverse('reports_index'))

def update_report_state(request, *args, **kwargs):
    return ReportStateUpdater()(request, *args, **kwargs)

def update_report(report, action):
    if action == 'delete':
        report.deleted = True
    return report
