#generic python imports
import logging

from datetime import datetime

#appengine imports
from google.appengine.ext import db
from google.appengine.api import users

#mopub imports
from account.models import Account
from advertiser.query_managers import CampaignQueryManager, CreativeQueryManager
from common.utils import date_magic
from common.properties.dict_property import DictProperty
from django.utils import simplejson
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
TARG = 'targeting' # I don't know what this is
C_TARG = 'custom targeting' # or this

NAME_STR = "dim%d-ent%d"

class Report(db.Model):
    name = db.StringProperty()
    status = db.StringProperty(choices=['created', 'pending','done'], default='created')
    deleted = db.BooleanProperty(default=False)
    saved = db.BooleanProperty(default=False)

    account = db.ReferenceProperty(Account, collection_name='reports')

    created_at = db.DateTimeProperty(auto_now_add=True)
    last_viewed = db.DateTimeProperty()

    # defines the Report
    d1 = db.StringProperty(required=True) 
    d2 = db.StringProperty() 
    d3 = db.StringProperty() 
    start = db.DateProperty(required=True)
    end = db.DateProperty(required=True)

    #schedule stuff
    #scheduled_report = db.ReferenceProperty(ScheduledReport, collection_name = 'created_reports')

    #the actual report
    # data in JSON (or similar) used for easy exporting
    #SUPER SWEET CUSTOM PROPERTY (gogogadget Stack Overflow)
    data = DictProperty()
    # data in HTML format for webpages so I dont' hvae to do fancy shit (fuck that)
    html_data = db.TextProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()
    

    def __str__(self):
        return "Report(d1=%s, d2=%s, d3=%s, start=%s, end=%s)" % (self.d1, self.d2, self.d3, self.start, self.end)
    
    def gen_data(self, page_num=0, per_page=100):
        #pagination stuff for pagination later?
        pub = None
        adv = None
        days = date_magic.gen_days(self.start,self.end) 
        def gen_helper(pub, adv, days, level):
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
            manager = StatsModelQueryManager(self.account)
            vals, typ, date_fmt = self.get_vals(pub, adv, days, dim)
            if vals is None:
                return ret
            for idx, val in enumerate(vals):
                name = None
                if typ == 'days':
                    if type(val) != list:
                        name = str(val)
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
                # going to make new function in SMQM that if given a list for these things it automatically
                # rolls them up
                key = NAME_STR % (level, idx) 
                stats = manager.get_rollup_for_days(publisher = pub, advertiser = adv, days = days, date_fmt = date_fmt)
                if last_dim: 
                    ret[key] = dict(stats = stats, name = name)
                else:
                    ret[key] = dict(stats=stats, name = name, sub_stats = gen_helper(pub,adv,days,level+1))
            return ret
        return gen_helper(pub, adv, days, 0)

    def get_vals(self, pub, adv, days, dim):
        date_fmt = 'date'
        if dim in (MO, WEEK, HOUR, DAY):
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
            man = AppQueryManager()
            type = 'pub'
            vals = man.reports_get_apps(account = self.account,
                                        publisher = pub,
                                        advertiser = adv,
                                        )
        elif dim == AU:
            man = AdUnitQueryManager()
            type = 'pub'
            vals = man.reports_get_adunits(account = self.account,
                                           publisher = pub,
                                           advertiser = adv,
                                           )
        elif dim == CAMP:
            man = CampaignQueryManager()
            type = 'adv'
            vals = man.reports_get_campaigns(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == CRTV:
            man = CreativeQueryManager()
            type = 'adv'
            vals = man.reports_get_creatives(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == P:
            man = CampaignQueryManager()
            type = 'adv'
            vals = man.reports_get_campaigns(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             by_priority = True,
                                             )
        elif dim == CO:
            return "Not implemented yet"
            type = 'other'
            #do country stuff
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
        print "\n\nValue is %s for inputs %s" % (vals, (pub,adv, days,dim))
        return vals, type, date_fmt

    @property
    def details(self):
        if self.d3:
            det = "%s > %s > %s" % (self.d1, self.d2, self.d3)
        elif self.d2:
            det = "%s > %s" % (self.d1, self.d2)
        elif self.d1:
            det = "%s" % self.d1
        else:
            det = "how the fuck did you get to this state, at least one dim is required"
        s_str = self.start.strftime('%m/%d/%y')
        e_str = self.end.strftime('%m/%d/%y')
        date = '%s to %s' % (e_str, s_str)
        return date + "\n" + det.title()
            

#class ScheduledReport -> has a "next report" time, "report every ____" time, report type, when it's tim
#   to gen a report, this guy makes report objects

