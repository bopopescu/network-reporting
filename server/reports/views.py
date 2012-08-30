import logging
from datetime import datetime, date

from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson

from google.appengine.ext import db
from common.ragendja.template import JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter
from reports.forms import ReportForm
from reports.models import ScheduledReport, Report
from reports.query_managers import ReportQueryManager

import report_server_api


class ReportIndexHandler(RequestHandler):
    def get(self):
        manager = ReportQueryManager(self.account)
        scheduled = manager.get_scheduled(limit=None)

        for report in scheduled:
            report.form = ReportForm(instance=report,
                                     prefix=str(report.key()))

        def sort_reports_key(report):
            if report.last_run:
                return report.last_run
            else:
                return datetime.min

        scheduled = sorted(scheduled, key=sort_reports_key, reverse=True)

        new_report_form = ReportForm(initial={'recipients': self.request.user.email},
                                     prefix='new')

        display_splash = date.today() < date(2012, 8, 1)
        return  {
            'scheduled': scheduled,
            'new_report_form': new_report_form,
            'display_splash': display_splash
        }

@login_required
def reports_index(request, *args, **kwargs):
    template = 'reports/reports_index.html'
    return ReportIndexHandler(template=template)(request, *args, **kwargs)    


class ReportStatusHandler(RequestHandler):
    
    def get(self, report_key):
        
        report = ScheduledReport.get(report_key)
        if report.account.key() != self.account.key():
            raise Http404

        return JSONResponse({'status': report.status})

@login_required
def report_status(request, *args, **kwargs):
    return ReportStatusHandler()(request, use_cache=False,*args, **kwargs)

    
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

        if report_form.is_valid():
            logging.info("Report form is valid")

            scheduled_report = report_form.save(commit=False)
            scheduled_report.account = self.account

            # Explicitly set next date to none if this is not a scheduled report
            if scheduled_report.sched_interval == 'none':
                scheduled_report.next_sched_date = None

            # TODO: refactor query managers to handle put
            scheduled_report.put()

            logging.info("Next date is " + str(scheduled_report.next_sched_date))

            manager = ReportQueryManager(self.account)
            manager.add_report(scheduled_report)

            if report_key:
                self.request.flash['report_edit'] = "The requested edit requires " \
                        "the report to be re-run.  The request has been submitted " \
                        "and you will be notified via email when it has completed."
            else:
                self.request.flash['report_success'] = "Your report has been " \
                        "successfully submitted, you will be notified via email " \
                        "when it has completed!"

            return JSONResponse({
                'success': True,
                'redirect': reverse('reports_index')
            })
        else:
            errors = {}
            for key, value in report_form.errors.items():
                # days is a derived field in the form
                if key != 'days':
                    key = report_form.prefix + '-' + key
                    errors[key] = ' '.join([error for error in value])
            logging.info("Report form is invalid.\nErrors: %s" % errors)

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
            now = datetime.now().date()
        else:
            now = datetime.strptime(now, '%y%m%d').date()

        scheds = ScheduledReport.all().filter('next_sched_date <=', now)
        scheds.filter('deleted =', False)
        scheds.filter('saved =', True)

        for sched in scheds:
            if sched.sched_interval != 'none':
                man.new_report(sched, now=now)
        return HttpResponse("Scheduled reports have been created")

def sched_runner(request, *args, **kwargs):
    return ScheduledRunner(login=False)(request, *args, **kwargs)


class ReportExporter(RequestHandler):
    def get(self, report_key):
        if db.Key(report_key).kind() == 'ScheduledReport':
            manager = ReportQueryManager(self.account)
            report_key = str(manager.get_report_data_by_sched_key(report_key).key())

        report = Report.get(report_key)

        if report.report_data_link:
            # The report was processed by the new system; use the
            # report_data_link to dynamically generate
            # a signed S3 link that points at the report output data
            return HttpResponseRedirect(
                report_server_api.get_report_data_url(report.report_data_link))
        else:
            # The report was processed by the old system
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
            # TODO: refactor qm to avoid db.get
            reports = [db.get(key) for key in keys]
            reports = [update_report(report, action) for report in reports]
            qm.put_report(reports)
        return HttpResponseRedirect(reverse('reports_index'))

def update_report_state(request, *args, **kwargs):
    return ReportStateUpdater()(request, *args, **kwargs)

def update_report(report, action):
    if action == 'delete':
        report.deleted = True
    return report


class ReportDoneHandler(RequestHandler):
    """
    Handle callback from report server.

    During the testing phase, we should comment out the 'put'
    statement and notifications so that it doesn't interfere with the
    existing system.
    """
    def post(self, report_id='', results_url='', status='', reason=''):
        logging.info('Got callback from reporting system: ' +
            str([report_id, results_url, status, reason]))

        report_query_manager = ReportQueryManager()
        report = report_query_manager.get_report_data_by_key(report_id)

        if status == 'done':
            # Reporting system was successful
            report.report_data_link = results_url

            report.completed_at = datetime.now()
            report.status = 'Completed'

            logging.info('Successfully got report')

            if settings.WRITE_REPORT_SERVER_RESULTS:
                # Only send email if we're using report server as
                # canonical source
                report.notify_complete()
        elif status == 'error':
            # Reporting system had a problem; translate reason to
            # appropriate status here
            if reason == 'no_data':
                report_status = 'No Data'
            else:
                report_status = 'Failed'

            report.status = report_status

            if settings.WRITE_REPORT_SERVER_RESULTS:
                # Only send email if we're using report server as
                # canonical source
                report.notify_failure(report_status)

        if settings.WRITE_REPORT_SERVER_RESULTS:
            # Only persist results if we're using report server as
            # canonical source
            report.put()

        return JSONResponse({'status': 'ok'})


def report_done(request, *args, **kwargs):
    return ReportDoneHandler(login=False)(request, *args, **kwargs)
