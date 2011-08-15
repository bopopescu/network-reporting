import datetime
import logging
import random
import time

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from google.appengine.api import taskqueue
from google.appengine.ext import db
from account.models import Account

from common.constants import DATE_FMT, PIPE_KEY, REP_KEY
from common.utils.query_managers import CachedQueryManager
from common.utils import date_magic
from common.utils.helpers import (blob_size, 
                                  shard_count, 
                                  clone_entity,
                                  build_key,
                                  )
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager, BlobLogQueryManager

from reports.models import Report, ScheduledReport
from reports.rep_mapreduce import GenReportPipeline
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY

from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message


REPORT_MSG = '%s|%s|%s|%s|%s|%s|%s'

NUM_REP_QS = 1
REP_Q_NAME = "gen-rep-%02d"
DEFAULT_REPORT_DIM_LIST = (('app', 'Apps'), ('adunit', 'Ad Units'), ('campaign', 'Campaigns'))
SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
REP_Q = SQS_CONN.create_queue('report_queue')


def fire_report_sqs(data):
    msg_data = REPORT_MSG % (data.d1, data.d2, data.d3, data.start.strftime('%y%m%d'), data.end.strftime('%y%m%d'), str(data.key()), str(data.account.key()))
    m = Message()
    m.set_body(msg_data)
    # Write returns True if success, keep trying until it succeeds
    while not REP_Q.write(m):
        pass
    


class ReportQueryManager(CachedQueryManager):
    Model = Report

    def __init__(self, account=None, offline=False):
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
        if report is None:
            report = self.add_report(d1, d2, d3, end, days, name, deleted)
        return report


    def check_report(self, d1, d2, d3, start, end):
        '''Returns a populated report if it's populated, none otherwise'''
        report = self.get_report(d1,d2,d3,start,end)
        if report.data:
            return report
        else:
            return None

    def get_saved(self, page=0, page_limit=50):
        '''Returns (page_limit) reports starting on 'page'
        '''
        report_q = Report.all().filter('account =', self.account).filter('saved =', True).filter('deleted =', False)
        reports = report_q.fetch(limit=page_limit,offset=page_limit*page)
        return reports

    def get_history(self, page=0, page_limit=50):
        '''Gives a history of ALL reports (saved and unsaved) for the user
        in order of most recently viewed'''
        #Not implemented
        return None

    def get_scheduled(self, to_fetch=50):
        report_q = ScheduledReport.all().filter('account =', self.account).filter('saved =', True).filter('deleted =', False).filter('default =', False)
        return report_q.fetch(to_fetch)

    def get_default_reports(self):
        # There are three by default, so fetching three should yield three
        reports = ScheduledReport.all().filter('account =', self.account).filter('deleted =', False).filter('default =', True).fetch(3)
        if len(reports) != 3:
            # Well shit
            report_dim_names = [(str(report.d1), str(report.name)) for report in reports]
            for (dim, name) in DEFAULT_REPORT_DIM_LIST:
                if (dim, name) not in report_dim_names:
                    reports.append(self.add_report(dim, None, None, None, 7, name=name, saved=True, interval='7days', default=True))
        return reports
                    
    def new_report(self, report, now=None, testing=False):
        if not isinstance(report, db.Model()) or isinstance(report, str) or isinstance(report, unicode):
            report = self.get_report_by_key(report)

        dt = datetime.timedelta(days=report.days) 
        one_day = datetime.timedelta(days=1)
        if now is None:
            now = datetime.datetime.now().date()

        # Find start and end based on interval things
        if report.interval:
            if report.interval == 'yesterday':
                now = now - one_day 
            elif report.interval == 'lmonth':
                start, end = date_magic.last_month(now)
                now = end.date()
                dt = end.date() - start.date()

        account = report.account.key()
        start = now - dt
        end = now
        acct_key = str(account)
        # Create new report
        new_report = Report(start = now - dt,
                            end = now,
                            account = account,
                            schedule = report,
                            )

        # Set up sched to run at a later time
        report.next_sched_date = date_magic.get_next_day(report.sched_interval, now)
        
        # Save the reports
        self.put_report(report)
        self.put_report(new_report)
        report_key = str(new_report.key())
        sched_key = str(report.key())

        report.last_run = datetime.datetime.now()
        report.put()

        fire_report_sqs(new_report)

        return new_report

    def add_report(self, 
                     d1, 
                     d2, 
                     d3, 
                     end, 
                     days, 
                     name=None, 
                     saved=False,
                     interval=None, 
                     sched_interval=None, 
                     recipients = None, 
                     testing=False):
        '''Create a new scheduled report with the given specs
        and create a new report to run

        If a Report object that is IDENTICAL to what this scheduler would create exists already, clone it and use that
        '''

        #############
        # Prep reports

        if interval is None:
            interval = 'custom'
        if name is None:
            dt = datetime.timedelta(days=days) 
            start = end - dt
            name = d1
            if d2:
                name += " > " + d2
            if d3:
                name += " > " + d3
            name += ' -'
            if interval == 'custom':
                name += ' ' + start.isoformat()
                name += ' -- ' + end.isoformat() 
            elif interval == '7days':
                name += ' Last 7 days'
            elif interval == 'lmonth':
                name += ' Last month'
            else:
                name += ' ' + interval.title()
            name = name.title()
        if d2 == '':
            d2 = None
        if d3 == '':
            d3 = None
        if not end:
            end = datetime.datetime.now().date()
        if sched_interval != 'none':
            if testing:
                next_sched_date =  date_magic.get_next_day(sched_interval, d = end)
            else:
                next_sched_date =  date_magic.get_next_day(sched_interval)
        else:
            if testing:
                next_sched_date = end
            else:
                next_sched_date = datetime.datetime.now().date()

        #########
        # Create the reports
        sched = ScheduledReport(d1=d1,
                                d2=d2,
                                d3=d3,
                                end=end,
                                days=days,
                                interval=interval,
                                sched_interval = sched_interval,
                                next_sched_date = next_sched_date,
                                account=self.account,
                                name=name,
                                saved=saved,
                                recipients=recipients or [],
                                )
        sched.put()
        dt = datetime.timedelta(days=days)
        start = end - dt
        end = end
        #ACCOUNT IS ACCOUNT KEY
        acct_key = str(self.account)

        report = Report(start = start,
                        end = end,
                        account = self.account,
                        schedule = sched,
                        )
        report.put()
        report_key = str(report.key())
        sched_key = str(sched.key())

        #not cloned, we're going to run this report
        sched.last_run = datetime.datetime.now()
        sched.put()

        fire_report_sqs(report)

        return sched 

    
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
        return new_report

    def put_report(self, report):
        if isinstance(report, list):
            db.put(report)
        else:
            report.put()
