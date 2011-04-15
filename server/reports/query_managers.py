import datetime
import logging
import time

from google.appengine.ext import db


from common.utils.cachedquerymanager import CachedQueryManager
from common.utils import date_magic
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from reports.models import Report

NUM_REP_QS = 1
REP_Q_NAME = "gen-rep-%02d"


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

    def get_report(self, d1,d2,d3,start,end,view=False, deleted=False):
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
        if report is None:
            report = self.add_report(d1,d2,d3,start,end)
        elif view:
            report.last_viewed = datetime.datetime.now()
            report.put()
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
        report_q = Reports.all().filter('account =', self.account).filter('saved =', True).filter('deleted =', False)
        reports = report_q.fetch(limit=page_limit,offset=page_limit*page)
        return reports

    def get_history(self, page=0, page_limit=10):
        '''Gives a history of ALL reports (saved and unsaved) for the user
        in order of most recently viewed'''
        #Not implemented
        return None

    def get_common_reports(self):
        reports = []
        now = datetime.datetime.now().date()
        start, end = date_magic.last_seven(now)
        for dim in COMMON_REPORT_DIM_LIST:
            report = self.get_report(dim,None,None,start,end)
            reports.append(report)
        return reports

    def add_report(self, d1, d2, d3, start, end, name=None, saved=False):
        '''Create a new report with the given specs'''
        if name is None:
            name = d1
            if d2:
                name += " > " + d2
            if d3:
                name += " > " + d3
            name += ' ' + start.isoformat()
            name += ' -- ' + end.isoformat() 
             
        report = Report(d1 = d1,
                        d2 = d2,
                        d3 = d3,
                        start = start,
                        end = end,
                        name = name,
                        account = self.account,
                        saved = saved,
                        status = 'created',
                        )
        report.put()
        url = reverse('generate_reports')
        q_num = random.randint(0, NUM_REP_QS - 1)
        taskqueue.add(url=url,
                      queue_name=REP_Q_NAME % q_num,
                      params={"report": report})
        return report
