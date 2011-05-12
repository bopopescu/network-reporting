import datetime
import logging
import random
import time

from django.core.urlresolvers import reverse
from django.template.loader import render_to_string
from google.appengine.api import taskqueue
from google.appengine.ext import db


from common.utils.query_managers import CachedQueryManager
from common.utils import date_magic
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from reports.models import Report, ScheduledReport

NUM_REP_QS = 1
REP_Q_NAME = "gen-rep-%02d"
COMMON_REPORT_DIM_LIST = (('app', 'Apps'), ('adunit', 'Ad Units'), ('campaign', 'Campaigns'))


class ReportQueryManager(CachedQueryManager):
    Model = Report

    def __init__(self, account, offline=False):
        if isinstance(account, db.Key):
            self.account = account
        elif isinstance(account, db.Model):
            self.account = account.key()
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

    def new_report(self, report):
        #do stuff w/ report interval here
        #last month shouldn't just arbitrarily pick some days
        if type(report) == str or type(report) == unicode:
            report = self.get_report_by_key(report, sched=False).schedule
        dt = datetime.timedelta(days=report.days) 
        one_day = datetime.timedelta(days=1)
        now = datetime.datetime.now().date()
        if report.interval:
            if report.interval == 'yesterday':
                now = datetime.datetime.now().date() - one_day 
            elif report.interval == 'lmonth':
                start, end = date_magic.last_month(now)
                now = end.date()
                dt = end.date() - start.date()
            
        new_report = Report(start = now - dt,
                            end = now,
                            account = self.account,
                            schedule = report,
                            )
        self.put_report(new_report)
        url = reverse('generate_reports')
        q_num = random.randint(0, NUM_REP_QS - 1)
        taskqueue.add(url=url,
                      queue_name=REP_Q_NAME % q_num,
                      params={"report": new_report.key(),
                              "account": str(self.account),
                              })
        return new_report

    def add_report(self, d1, d2, d3, end, days, name=None, saved=False,interval=None):
        if interval is None:
            interval = 'custom'
        '''Create a new scheduled report with the given specs
        and create a new report to run'''
        if name is None:
            dt = datetime.timedelta(days=days) 
            start = end - dt
            name = d1
            if d2:
                name += " > " + d2
            if d3:
                name += " > " + d3
            name += ' ' + start.isoformat()
            name += ' -- ' + end.isoformat() 
            name = name.title()
        if d2 == '':
            d2 = None
        if d3 == '':
            d3 = None
        if not end:
            end = datetime.datetime.now().date()
        sched = ScheduledReport(d1=d1,
                                d2=d2,
                                d3=d3,
                                end=end,
                                days=days,
                                interval=interval,
                                account=self.account,
                                name=name,
                                saved=saved,
                                )
        sched.put()
             
        dt = datetime.timedelta(days=days)

        report = Report(start = end - dt,
                        end = end,
                        account = self.account,
                        schedule = sched,
                        )
        report.put()
        url = reverse('generate_reports')
        q_num = random.randint(0, NUM_REP_QS - 1)
        taskqueue.add(url=url,
                      queue_name=REP_Q_NAME % q_num,
                      params={"report": report.key(),
                              "account": str(self.account),
                              })
        return sched 

    def put_report(self, report):
        report.put()
