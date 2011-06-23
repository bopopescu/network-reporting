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

NUM_REP_QS = 1
REP_Q_NAME = "gen-rep-%02d"
COMMON_REPORT_DIM_LIST = (('app', 'Apps'), ('adunit', 'Ad Units'), ('campaign', 'Campaigns'))


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

    def get_report_by_key(self, report_key, view=False, sched=False):
        if sched:
            report = ScheduledReport.get(report_key)
        else:
            report = Report.get(report_key)
        if view:
            report.last_viewed = datetime.datetime.now()
            report.put()
        return report 

    def get_report(self, d1,d2,d3,start,end,name=None,view=False, deleted=False):
        '''Given the specs for a report, return that report.  If the report
        doesnt exist yet, create an empty one.  If this is a view request, update
        the last_viewed field of the report'''
        report_q = Report.all().filter('account =', self.account).filter('deleted =', deleted)
        report_q = report_q.filter('d1 =', d1).filter('start =', start).filter('end =', end)
        if d2:
            report_q = report_q.filter('d2 =', d2)
        if d3:
            report_q = report_q.filter('d3 =', d3)
        report = report_q.get()
        #This should always work.  There should be NO way we EVER
        # try to access a report that doesn't exist.  Every report
        # MUST have a corresponding scheduled report so that's good
        if view:
            report.last_viewed = datetime.datetime.now()
            report.put()
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

    def get_saved(self, page=0, page_limit=10):
        '''Returns (page_limit) reports starting on 'page'
        '''
        report_q = Report.all().filter('account =', self.account).filter('saved =', True).filter('deleted =', False)
        reports = report_q.fetch(limit=page_limit,offset=page_limit*page)
        return reports

    def get_history(self, page=0, page_limit=10):
        '''Gives a history of ALL reports (saved and unsaved) for the user
        in order of most recently viewed'''
        #Not implemented
        return None

    def get_scheduled(self):
        reports = []
        for dim, name in COMMON_REPORT_DIM_LIST:
            report = self.get_scheduled_report(dim, None, None, None, 7, name)
            reports.append(report)
        report_q = ScheduledReport.all().filter('account =', self.account).filter('saved =', True).filter('deleted =', False)
        for rep in report_q:
            reports.append(rep)
        return reports

    def get_common_reports(self):
        reports = []
        now = datetime.datetime.now().date()
        start, end = date_magic.last_seven(now)
        for dim,name in COMMON_REPORT_DIM_LIST:
            report = self.get_report(dim,None,None,start,end, name=name)
            reports.append(report)
        return reports

    def new_report(self, report, now=None, testing=False):
        #do stuff w/ report interval here
        #last month shouldn't just arbitrarily pick some days
        if isinstance(report, str) or isinstance(report, unicode):
            report = self.get_report_by_key(report, sched=False).schedule
        dt = datetime.timedelta(days=report.days) 
        one_day = datetime.timedelta(days=1)
        if now is None:
            now = datetime.datetime.now().date()
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
        rep_key_dict = dict(d1 = report.d1,
                            d2 = report.d2,
                            d3 = report.d3,
                            account = acct_key,
                            start = start.strftime(DATE_FMT),
                            end = end.strftime(DATE_FMT),
                            )
        key = build_key(REP_KEY, rep_key_dict)
        rep = Report.get_by_key_name(key)
        if rep:
            cloned = True
            new_report = clone_entity(rep, schedule=report)
        else:
            cloned = False
            new_report = Report(start = now - dt,
                                end = now,
                                account = account,
                                schedule = report,
                                )

        report.next_sched_date = date_magic.get_next_day(report.sched_interval, now)
        self.put_report(report)
        self.put_report(new_report)
        report_key = str(new_report.key())
        sched_key = str(report.key())
        if not cloned:
            report.last_run = datetime.datetime.now()
            report.put()
            blob_keys = BlobLogQueryManager.get_blobkeys_for_days(date_magic.gen_days(now-dt, now), str(account.key()))
            shards = shard_count(blob_size(blob_keys)) 
            pipe = GenReportPipeline(blob_keys,
                                     shards, 
                                     new_report.d1, 
                                     new_report.d2, 
                                     new_report.d3, 
                                     new_report.start.strftime(DATE_FMT), 
                                     new_report.end.strftime(DATE_FMT), 
                                     report_key = report_key,
                                     )

            key_dict = dict(type = 'GenReportPipeline',
                            key = report_key)
            pipe_key = PIPE_KEY % key_dict
            q_num = random.randint(0, NUM_REP_QS - 1) 

            pipe.start(idempotence_key = pipe_key, queue_name=REP_Q_NAME % q_num)
        return new_report

    def add_report(self, d1, d2, d3, end, days, name=None, saved=False,interval=None, sched_interval=None, recipients = None, testing=False):
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
                                recipients=recipients,
                                )
        sched.put()
        dt = datetime.timedelta(days=days)
        start = end - dt
        end = end
        #ACCOUNT IS ACCOUNT KEY
        acct_key = str(self.account)
        rep_key_dict = dict(d1 = d1,
                            d2 = d2,
                            d3 = d3,
                            account = acct_key,
                            start = start.strftime(DATE_FMT),
                            end = end.strftime(DATE_FMT),
                            )
        key = build_key(REP_KEY, rep_key_dict)
        rep = Report.get_by_key_name(key)
        if rep:
            cloned = True
            report = clone_entity(rep, schedule=sched)
        else:
            cloned = False
            #ACCOUNT IS ACCOUNT KEY
            report = Report(start = start,
                            end = end,
                            account = self.account,
                            schedule = sched,
                            )
        report.put()
        report_key = str(report.key())
        sched_key = str(sched.key())

        if not cloned:
            #not cloned, we're going to run this report
            sched.last_run = datetime.datetime.now()
            sched.put()
            ###########
            # Prep and run the pipeline
            blob_keys = BlobLogQueryManager.get_blobkeys_for_days(date_magic.gen_days(end-dt, end), str(report.account.key()))

            # Computer number of shards this job will need
            shards = shard_count(blob_size(blob_keys))

            # create the pipeline
            pipe = GenReportPipeline(blob_keys, 
                                     shards, 
                                     report.d1, 
                                     report.d2, 
                                     report.d3, 
                                     report.start.strftime(DATE_FMT), 
                                     report.end.strftime(DATE_FMT), 
                                     report_key = report_key,
                                     )

            key_dict = dict(type = 'GenReportPipeline',
                            key = report_key)
            pipe_key = PIPE_KEY % key_dict
            q_num = random.randint(0, NUM_REP_QS - 1) 
            #start pipeline w/ specific key + gen_rep queue
            pipe.start(idempotence_key = pipe_key, queue_name=REP_Q_NAME % q_num)
        return sched 

    def put_report(self, report):
        report.put()
