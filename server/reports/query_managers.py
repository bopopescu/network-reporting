import datetime
import logging
import random
import time
import urllib

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from google.appengine.api import taskqueue
from google.appengine.ext import db
from account.models import Account

from common.constants import DATE_FMT, PIPE_KEY, REP_KEY, IS_PROD
from common.utils.query_managers import CachedQueryManager
from common.utils import date_magic
from common.utils.helpers import clone_entity
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager, BlobLogQueryManager

from reports import report_server_api

from reports.models import Report, ScheduledReport
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message


REPORT_MSG = '%s|%s|%s|%s|%s|%s|%s|%s'
REP_Q = 'report_queue'
AWS_ACCT = 345840704531
SQS_ENDPOINT = 'queue.amazonaws.com'
SQS_URI = '/%s/%s' % (REP_Q, AWS_ACCT)
SQS_URL = 'http://%s%s' % (SQS_ENDPOINT, SQS_URI)

NUM_REP_QS = 1
REP_Q_NAME = "gen-rep-%02d"
DEFAULT_REPORT_DIM_LIST = (('app', 'Apps'), ('adunit', 'Ad Units'), ('campaign', 'Campaigns'))
REP_Q = None

def fire_report_sqs(data):
    global REP_Q
    if not REP_Q:
        SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
        REP_Q = SQS_CONN.create_queue('report_queue')
    # Don't send shit to EMR if we're not on prod
    if not IS_PROD:
        return
    msg_data = REPORT_MSG % (data.d1, data.d2, data.d3, data.start.strftime('%y%m%d'), data.end.strftime('%y%m%d'), str(data.key()), str(data.account.key()), time.time())


    m = Message()
    m.set_body(msg_data)
    # Write returns True if success, keep trying until it succeeds
    while not REP_Q.write(m):
        pass



class ReportQueryManager(CachedQueryManager):
    Model = Report

    def __init__(self, account=None, offline=True):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
        elif account is None:
            self.account = None
        else:
            self.account = db.Key(account)

        self.offline = offline

        self.obj_cache = {}

    def migrate_relevant_reports(self):
        scheduled = self.get_scheduled()
        defaults, adding = self.get_default_reports(dont_add=True)
        all_reps = scheduled + defaults
        for rep in all_reps:
            print "Working on %s" % rep
            self.migrate_scheduled_data(rep)


    def migrate_scheduled_data(self, scheduled):
        # I don't think anybody has more than 100 of these guys...

        #Update scheds most recent
        most_recent = scheduled.most_recent
        if most_recent is None:
            return
        if not scheduled._most_recent:
            print "Updating most recent"
            self.update_most_recent(scheduled, most_recent)

        # Update all status's that are lazily set
        datum = scheduled.most_recent
        status = datum.status
        if datum.status == 'Completed' or datum.status == 'No Data':
            print "Already has status stuff set"
            return
        if datum.data and status != 'Completed':
            datum.status = 'Completed'
            Report.put(datum)

    def update_most_recent(self, sched, most_recent):
        sched._most_recent = most_recent
        sched._details = most_recent.details(sched.interval)
        sched._date_details = most_recent.date_details(sched.interval)
        sched._dim_details = most_recent.dim_details
        sched._status = most_recent.status
        sched.put()


    def get_report_by_key(self, report_key, view=False):
        return ScheduledReport.get(report_key)

    def get_report_data_by_sched_key(self, report_key):
        return ScheduledReport.get(report_key).most_recent

    def get_report_data_by_key(self, data_key):
        return Report.get(data_key)

    def get_report(self, d1,d2,d3,start,end,name=None,view=False, deleted=False):
        '''Given the specs for a report, return that report.  If the report
        doesnt exist yet, create an empty one.  If this is a view request, update
        the last_viewed field of the report'''
        report_q = Report.all().filter('account =', self.account).filter('deleted =', deleted)
        report_q = report_q.filter('d1 =', d1).filter('end =', end).filter('start =', start)
        if d2:
            report_q = report_q.filter('d2 =', d2)
        if d3:
            report_q = report_q.filter('d3 =', d3)
        report = report_q.get()
        #This should always work.  There should be NO way we EVER
        # try to access a report that doesn't exist.  Every report
        # MUST have a corresponding scheduled report so that's good
        return report

    def get_scheduled_report(self, d1, d2, d3, end=None, days=None, name=None, deleted=False):
        rep_q = ScheduledReport.all().filter('account =', self.account).filter('deleted =', deleted).filter('d1 =', d1)
        if d2:
            rep_q = rep_q.filter('d2 =', d2)
        if d3:
            rep_q = rep_q.filter('d3 =', d3)
        if end:
            rep_q = rep_q.filter('end =', end)
        if days:
            rep_q = rep_q.filter('days =', days)
        report = rep_q.get()
        return report


    def check_report(self, d1, d2, d3, start, end):
        '''Returns a populated report if it's populated, none otherwise'''
        report = self.get_report(d1,d2,d3,start,end)
        if report.data:
            return report
        else:
            return None

    def get_scheduled(self, saved=True, deleted=False, default=False,
            not_sched_interval=None, limit=50):
        report_q = ScheduledReport.all().filter('account =', self.account)
        if saved != None:
            report_q.filter('saved =', saved)
        if deleted != None:
            report_q.filter('deleted =', deleted)
        if default != None:
            report_q.filter('default =', default)
        if not_sched_interval:
            report_q.filter('sched_interval !=', not_sched_interval)
        return list(report_q.run(batch_size=300, limit=limit))

    def get_reports_to_schedule(self, now, interval):
        """Get all scheduled reports that are to be run now."""
        scheds = ScheduledReport.all().filter('next_sched_date =', now)

        # Only run reports scheduled for the argument interval
        scheds.filter('sched_interval =', interval)

        # Don't run deleted or unsaved reports
        scheds.filter('deleted =', False)
        scheds.filter('saved =', True)

        return scheds

    def new_report(self, report, now=None, testing=False):
        if not isinstance(report, db.Model) or isinstance(report, str) or isinstance(report, unicode):
            report = self.get_report_by_key(report)

        dt = datetime.timedelta(days=report.days)
        one_day = datetime.timedelta(days=1)

        if now is None:
            now = datetime.datetime.now().date()

        # Get report start and end
        if report.interval == 'yesterday':
            report_end = now - one_day
        elif report.interval == 'lmonth':
            start, end = date_magic.last_month(now)

            if isinstance(end, datetime.datetime):
                end = end.date()
            if isinstance(start, datetime.datetime):
                start = start.date()

            report_end = end
            dt = end - start
        else:
            report_end = now

        account = report.account.key()

        # Create new report
        new_report = Report(
            start=report_end - dt,
            end=report_end,
            account=account,
            schedule=report)

        # Set up sched to run at a later time
        logging.info(
            'Now is %s, next_sched_date is %s, sched_interval is %s' %
            (now, report.next_sched_date, report.sched_interval))

        report.next_sched_date = date_magic.get_next_day(report.sched_interval, now)

        logging.info('New next_sched_date is %s' % report.next_sched_date)

        # Save the reports
        self.put_report(report)
        self.put_report(new_report)

        # Update most recent
        self.update_most_recent(report, new_report)

        report.last_run = datetime.datetime.now()
        report.put()

        # Send report request to both old and new systems
        report_server_api.submit_report_request(new_report)
        #fire_report_sqs(new_report)

        return new_report

    def add_report(self, scheduled_report):
        '''Create a new report given specs from it's scheduled_report

        If a Report object that is IDENTICAL to what this scheduler would create exists already, clone it and use that
        '''
        start = scheduled_report.end - datetime.timedelta(days=scheduled_report.days)
        report = Report(start=start,
                        end=scheduled_report.end,
                        account=self.account,
                        schedule=scheduled_report)
        report.put()
        # Update most recent
        self.update_most_recent(scheduled_report, report)

        #not cloned, we're going to run this report
        scheduled_report.last_run = datetime.datetime.now()
        scheduled_report.put()

        # Send report request to both old and new systems
        report_server_api.submit_report_request(report)
        #fire_report_sqs(report)

    def clone_report(self, report, sched=False):
        """ Does exactly what you think it will

                Caveat: scheduled reports that are cloned won't be rescheduled

        """
        if sched:
            new_report = ScheduledReport(account = report.account,
                                        name = report.name,
                                        saved = report.saved,
                                        deleted = report.deleted,
                                        last_run = report.last_run,
                                        d1 = report.d1,
                                        d2 = report.d2,
                                        d3 = report.d3,
                                        end = report.end,
                                        days = report.days,
                                        interval = report.interval,
                                        )

            new_report.put()
        else:
            new_report = Report(account = report.account,
                                schedule = report.schedule,
                                start = report.start,
                                end = report.end,
                                data = report.data
                                )
            new_report.put()
            # Update most recent
            self.update_most_recent(schedule, new_report)

        return new_report

    def put_report(self, report):
        if isinstance(report, list):
            db.put(report)
        else:
            report.put()
