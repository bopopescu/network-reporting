import logging, datetime

from urllib import urlencode
import urllib

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson
from django.template import loader
from google.appengine.api import mail, files
from google.appengine.ext import db
from google.appengine.ext.webapp import template, blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from common.ragendja.template import render_to_response, \
        render_to_string, \
        JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from mail.mails import REPORT_FINISHED_SIMPLE
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from reports.forms import ReportForm
from reports.models import ScheduledReport, \
        Report
from reports.query_managers import ReportQueryManager


from reports.forms import ReportForm


class ReportIndexHandler(RequestHandler):
    def get(self):
        manager = ReportQueryManager(self.account)
        scheduled = manager.get_scheduled()

        saved_reports = manager.get_saved()
        reports = scheduled + saved_reports

        for report in scheduled:
            report.form = ReportForm(instance=report,
                                     prefix=str(report.key()))

        reports = sorted(reports, key=lambda report: report.completed_at if isinstance(report,
            Report) else report.last_run)

        new_report_form = ReportForm(initial={'recipients': self.request.user.email},
                                     prefix='new')
        return render_to_response(self.request, 'reports/reports_index.html',
                                 {'reports': reports,
                                  'scheduled': scheduled,
                                  'new_report_form': new_report_form, })

@login_required
def reports_index(request, *args, **kwargs):
    return ReportIndexHandler()(request, *args, **kwargs)


class EditReportHandler(RequestHandler):
    def post(self, report_key=None):
        """
        Create a new ScheduledReport or edit an existing one
        """
        prefix = report_key or 'new'

        # TODO: refactor reports query managers and move there
        report = db.get(report_key) if report_key else None

        report_form = ReportForm(self.request.POST,
                                 instance=report,
                                 prefix=prefix)

        logging.info(report_form.__dict__)

        if report_form.is_valid():
            scheduled_report = report_form.save(commit=False)
            scheduled_report.account = self.account
            # TODO: refactor query managers to handle put
            scheduled_report.put()

            manager = ReportQueryManager(self.account)
            manager.add_report(scheduled_report)

            if report_key:
                self.request.flash['report_edit'] = "The requested edit requires " \
                        "the report to be re-run.  The request has been submitted " \
                        "and you will be notified via email when it has completed"
            else:
                self.request.flash['report_success'] = "Your report has been " \
                        "successfully submitted, you will be notified via email " \
                        "when it has completed!"

            return JSONResponse({
                'success': True,
                'redirect': reverse('reports_index')})
        else:
            errors = {}
            for key, value in report_form.errors.items():
                key = report_form.prefix + '-' + key
                errors[key] = ' '.join([error for error in value])

        logging.info('Errors')
        logging.info(errors)
        return JSONResponse({
            'errors': errors,
            'success': False,
        })


@login_required
def edit_report(request, *args, **kwargs):
    return EditReportHandler()(request, *args, **kwargs)


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
        if report.html_data_blob:
            return HttpResponseRedirect('/offline/reports/get_blob/%s/' % str(report.html_data_blob.key()))
        else:
            data = report.html_data
            ret = {}
            if data is None:
                #Not going to do this now
                #ret['map-status'], ret['shuf-status'], ret['red-status'] = MapReduceQueryManager.get_mr_status(type='report', key=report_key)
                data = 'none'
            ret['data'] = data
            json_ret = simplejson.dumps(ret)
            return HttpResponse(json_ret, mimetype='application/json')

def check_report(request, *args, **kwargs):
    return CheckReportHandler()(request, use_cache=False, *args, **kwargs)


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
        return HttpResponseRedirect('/reports/')

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
        scheds = ScheduledReport.all().filter('next_sched_date =', now)
        for sched in scheds:
            man.new_report(sched)
        return HttpResponse("Scheduled reports have been created")

def sched_runner(request, *args, **kwargs):
    return ScheduledRunner(login=False)(request, *args, **kwargs)



class ReportExporter(RequestHandler):
    def get(self, report_key, *args, **kwargs):
        return sswriter.write_report('csv', report_key, self.account.key())

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
