#generic python imports
import logging

from datetime import datetime, timedelta

#appengine imports
from django.template import loader
from django.utils import simplejson
from google.appengine.ext import db
from google.appengine.api import users

#mopub imports
from account.models import Account
from advertiser.query_managers import CampaignQueryManager, CreativeQueryManager
from common.utils import date_magic
from common.properties.dict_property import DictProperty
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

APP = 'app'
AU = 'adunit'
CAMP = 'campaign'
CRTV = 'creative'
P = 'priority'
MO = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'
CO = 'country'
DEV = 'device'
OS = 'os'
KEY = 'kw'
TARG = 'targeting' # I don't know what this is
C_TARG = 'custom targeting' # or this

ALL_COUNTRY = []
ALL_DEVICE = []
ALL_OS = []

NAME_STR = "dim%d-ent%d"

#class ScheduledReport -> has a "next report" time, "report every ____" time, report type, when it's tim
#   to gen a report, this guy makes report objects
class ScheduledReport(db.Model):
    account = db.ReferenceProperty(Account, collection_name='scheduled_reports')
    created_at = db.DateTimeProperty(auto_now_add=True)

    name = db.StringProperty()
    saved = db.BooleanProperty()
    deleted = db.BooleanProperty(default=False)
    last_run = db.DateTimeProperty()

    d1 = db.StringProperty(required=True) 
    d2 = db.StringProperty() 
    d3 = db.StringProperty() 
    end = db.DateProperty(required=True)
    days = db.IntegerProperty(required=True)
    #daily, weekly, monthly
    interval = db.StringProperty(choices=['today','yesterday', '7days', 'lmonth', 'custom'], default='custom')
    sched_interval = db.StringProperty(choices = ['none', 'daily', 'weekly', 'monthly', 'quarterly'], default='none')
    next_sched_date = db.DateProperty(default=datetime.now().date())


    @property
    def most_recent(self):
        return self.reports.order('-created_at').get()
        #get the most recent report created by this scheduler
    @property
    def details(self):
        return self.most_recent.details(self.interval)

    @property
    def date_details(self):
        return self.most_recent.date_details(self.interval)
    
    @property
    def dim_details(self):
        return self.most_recent.dim_details

    

class Report(db.Model):
    #standard
    account = db.ReferenceProperty(Account, collection_name='reports')
    created_at = db.DateTimeProperty(auto_now_add=True)

    #scheduled report
    schedule = db.ReferenceProperty(ScheduledReport, collection_name='reports')

    start = db.DateProperty(required=True)
    end = db.DateProperty(required=True)

    #the actual report
    data = DictProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()

    @property
    def d1(self):
        return self.schedule.d1

    @property
    def d2(self):
        return self.schedule.d2

    @property
    def d3(self):
        return self.schedule.d3

    @property
    def name(self):
        return self.schedule.name

    

    def __str__(self):
        return "Report(d1=%s, d2=%s, d3=%s, start=%s, end=%s)" % (self.d1, self.d2, self.d3, self.start, self.end)
    
    def gen_data(self, page_num=0, per_page=100):
        #pagination stuff for pagination later?
        pub = None
        adv = None
        country = None
        device = None
        op_sys = None
        date_fmt = None
        days = date_magic.gen_days(self.start,self.end) 
        def gen_helper(pub, adv, days, country, device, op_sys, date_fmt, level):
            last_dim = False
            if level == 0:
                if self.d2 is None:
                    last_dim = True
                dim = self.d1
            elif level == 1:
                if self.d3 is None:
                    last_dim = True
                dim = self.d2
            elif level == 2:
                last_dim = True
                dim = self.d3
            else:
                dim = 9001
                logging.error("impossible")
            ret = {}
            manager = StatsModelQueryManager(self.account, offline=False)#True) #offline=self.offline)
            vals, typ, date_fmt = self.get_vals(pub, adv, days, country, device, op_sys, dim, date_fmt)
            if vals is None:
                return ret
            for idx, val in enumerate(vals):
                name = None
                if typ == 'co':
                    name = "<<COUNTRY NAME HERE>>"
                    country = val
                elif typ == 'dev':
                    name = '<<DEVICE NAME HERE>>'
                    device = val
                elif typ == 'os':
                    name = '<<OS NAME HERE>>'
                    op_sys = val
                elif typ == 'days':
                    name = date_magic.date_name(val, dim)
                    days = val
                elif typ == 'pub':
                    name = val.name
                    pub = val
                elif typ == 'adv':
                    if type(val) == list:
                        print val
                        name = val[0].campaign_type
                    else:
                        name = val.name
                    adv = val
                #days can be a list (actually I think it needs to be) but publisher/advertiser should NOT
                # rolls them up
                key = NAME_STR % (level, idx) 
                stats = manager.get_rollup_for_days(publisher = pub,
                                                    advertiser = adv,
                                                    country = country,
                                                    device = device,
                                                    op_sys = op_sys,
                                                    days = days,
                                                    date_fmt = date_fmt
                                                    )
                if last_dim: 
                    ret[key] = dict(stats = stats, name = name)
                else:
                    ret[key] = dict(stats=stats, name = name, sub_stats = gen_helper(pub,adv,days, country, device, op_sys,date_fmt, level+1))
            return ret
        return gen_helper(pub, adv, days, country, device, op_sys, date_fmt, 0)

    def get_vals(self, pub, adv, days, country, device, op_sys, dim, date_fmt=None):
        #This gets the list of values to iterate over for this level of the breakdown.  Country, device, OS, and keywords are irrelevant because they are independent of everythign else
        if date_fmt is None:
            #use preset format if it exists, otherwise use 'date'
            date_fmt = 'date'
        if dim in (MO, WEEK, HOUR, DAY):
            #assume it's not hour right away, if it is 'date_hour' it'll fix itself
            date_fmt = 'date'
            type = 'days'
            if dim == MO:
                vals = date_magic.get_months(days)
            elif dim == WEEK:
                vals = date_magic.get_weeks(days)
            elif dim == DAY:
                vals = date_magic.get_days(days)
            elif dim == HOUR:
                date_fmt = 'date_hour'
                vals = date_magic.get_hours(days)
        elif dim == APP:
            #basic stuff
            man = AppQueryManager
            type = 'pub'
            vals = man.reports_get_apps(account = self.account,
                                        publisher = pub,
                                        advertiser = adv,
                                        )
        elif dim == AU:
            man = AdUnitQueryManager
            type = 'pub'
            vals = man.reports_get_adunits(account = self.account,
                                           publisher = pub,
                                           advertiser = adv,
                                           )
        elif dim == CAMP:
            man = CampaignQueryManager
            type = 'adv'
            vals = man.reports_get_campaigns(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == CRTV:
            man = CreativeQueryManager
            type = 'adv'
            vals = man.reports_get_creatives(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == P:
            man = CampaignQueryManager
            type = 'adv'
            vals = man.reports_get_campaigns(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             by_priority = True,
                                             )
        elif dim == CO:
            type = 'co'
            vals = ALL_COUNTRY 
            #countries are indepent of publisher//advertiser
        elif dim == DEV:
            type = 'dev'
            vals = ALL_DEVICE
            #devices are indepent of publisher//advertiser
        elif dim == OS:
            type = 'os'
            vals = ALL_OS
            #OS's are indepent of publisher//advertiser
        elif dim == TARG:
            return "Not implemented yet"
            type = 'other'
            #do 'targeting' stuff
        elif dim == C_TARG:
            return "Not implemented yet"
            type = 'other'
            #do 'custom targeting' stuff
        else:
            logging.error("cry me a river ohh ohhhhh")
            return None, None
        return vals, type, date_fmt

    @property
    def html_data(self):
        if self.data:
            return loader.render_to_string('reports/report.html', dict(all_stats=self.data))
        else:
            return None
    
    @property
    def details(self):
        def detail_helper(interval):
            return self.dim_details + "<br/>" + self.date_details(interval)
        return detail_helper

    @property
    def date_details(self):
        def date_helper(interval):
            if interval == 'custom':
                s_str = self.start.strftime('%m/%d/%y')
                e_str = self.end.strftime('%m/%d/%y')
                return '%s to %s' % (s_str, e_str)
            else: 
                if interval == '7days':
                    return 'Last 7 days'
                elif interval == 'lmonth':
                    return 'Last month'
                else:
                    return interval.title()
        return date_helper
    
    @property
    def dim_details(self):
        if self.d3:
            det = "%s > %s > %s" % (self.d1, self.d2, self.d3)
        elif self.d2:
            det = "%s > %s" % (self.d1, self.d2)
        elif self.d1:
            det = "%s" % self.d1
        else:
            det = "how the fuck did you get to this state, at least one dim is required"
        return det.title()

            

