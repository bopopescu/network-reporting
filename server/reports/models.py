from google.appengine.ext import db
from google.appengine.api import users

from datetime import datetime

from account.models import Account
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from advertiser.query_managers import CampaignQueryManager, CreativeQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager

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

NAME_STR = "level%d-entry%d"
PUB_D = set((APP, AU))
ADV_D = set((CAMP, CRTV))
PRI_D = set((P, CAMP))

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
    data = db.TextProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()

    
    def gen_data(self):
        pub = None
        adv = None
        days = start -> stop days #TODO fix this 
        def gen_helper(self, pub, adv, days, level):
            if level == 1:
                dim = self.d1
            elif level == 2:
                dim = self.d2
            elif level == 3:
                dim = self.d3
            else:
                dim = 9001
                logging.error("impossible")
            ret = {}
            manager = StatsModelQueryManager(self.account)
            vals, type = self.get_vals(pub, adv, days, dim)
            for idx, val in enumerate(vals):
                if type == 'days':
                    days = val
                elif type == 'pub':
                    pub = val
                elif type == 'adv':
                    adv = val
                #days can be a list (actually I think it needs to be) but publisher/advertiser should NOT
                # going to make new function in SMQM that if given a list for these things it automatically
                # rolls them up
                name = NAME_STR % (level, idx) 
                stats = manager.get_rollup_for_days(publisher = pub, advertiser = adv, days = days)
                if level == 3:
                    ret[name] = dict(stats = stats)
                else:
                    ret[name] = dict(stats=stats, sub_stats = self.gen_helper(pub,adv,days,level+1))
            return ret
        return gen_helper(pub, adv, days, 0)

    def get_vals(self, pub, adv, days, dim):
        if dim in (MO, WEEK, HOUR, DAY):
            type = 'days'
            if dim == MO:
                vals = date_magic.get_months(days)
            elif dim == WEEK:
                vals = date_magic.get_weeks(days)
            elif dim == DAY:
                vals = date_magic.get_days(days)
            elif dim == HOUR:
                vals = date_magic.get_hours(days)
        elif dim == APP:
            #basic stuff
            man = AppQueryManager()
            type == 'pub'
            vals = man.reports_get_apps(account = self.account,
                                        publisher = pub,
                                        advertiser = adv,
                                        )
        elif dim == AU:
            man = AdUnitQueryManager()
            type == 'pub'
            vals = man.reports_get_adunits(account = self.account,
                                           publisher = pub,
                                           advertiser = adv,
                                           )
        elif dim == CAMP:
            man = CampaignQueryManager()
            type == 'adv'
            vals = man.reports_get_campaigns(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == CRTV:
            man = CreativeQueryManager()
            type == 'adv'
            vals = man.reports_get_creatives(account = self.account,
                                             publisher = pub,
                                             advertiser = adv,
                                             )
        elif dim == P:
            return "Not implemented yet"
            type == 'adv'
            #do priority stuff
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
        return vals, type


#class ScheduledReport -> has a "next report" time, "report every ____" time, report type, when it's tim
#   to gen a report, this guy makes report objects

