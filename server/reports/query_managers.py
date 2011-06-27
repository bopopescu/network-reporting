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
DEFAULT_REPORT_DIM_LIST = (('app', 'Apps'), ('adunit', 'Ad Units'), ('campaign', 'Campaigns'))

#I couldn't import this because it was causing circular imports and all other kinds of hell
def gen_report_worker(report, account, end=None):
    if end is None:
        end = datetime.datetime.now()
    man = ReportQueryManager()
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
    return

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
                    
    def new_report(self, report, now=None, testing=False, sched=False):
        #do stuff w/ report interval here
        #last month shouldn't just arbitrarily pick some days
        if isinstance(report, str) or isinstance(report, unicode):
            if sched:
                report = self.get_report_by_key(report, sched=False).schedule
            else:
                report = self.get_report_by_key(report, sched=sched)
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

        account = report.account
        new_report = Report(start = now - dt,
                            end = now,
                            account = account,
                            schedule = report,
                            )
        report.next_sched_date = date_magic.get_next_day(report.sched_interval, now)
        self.put_report(report)
        self.put_report(new_report)
        if testing:
            gen_report_worker(new_report.key(), account.key(), end=now)
            return report
        else:
            url = reverse('generate_reports')
            q_num = random.randint(0, NUM_REP_QS - 1)
            taskqueue.add(url=url,
                          queue_name=REP_Q_NAME % q_num,
                          params={"report": new_report.key(),
                                  "account": account.key(),
                                  })
        return new_report

    def add_report(self, d1, d2, d3, end, days, name=None, saved=True,interval=None, sched_interval=None, default=False, testing=False):
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
                                default=default,
                                )
        sched.put()
             
        dt = datetime.timedelta(days=days)

        report = Report(start = end - dt,
                        end = end,
                        account = self.account,
                        schedule = sched,
                        )
        report.put()
        #if in test mode don't use a TQ because they're stupid and don't work
        if testing:
            gen_report_worker(report.key(), self.account, end=end)
        else:
            url = reverse('generate_reports')
            q_num = random.randint(0, NUM_REP_QS - 1)
            taskqueue.add(url=url,
                          queue_name=REP_Q_NAME % q_num,
                          params={"report": report.key(),
                                  "account": str(self.account),
                                  },
                          )
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
