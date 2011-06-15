#generic python imports
import logging

from datetime import datetime, timedelta

from django.template import loader
#appengine imports
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import users

#mopub imports
#from account.models import Account
from common.constants import ISO_COUNTRIES, REP_KEY, CLONE_REP_KEY
from common.utils import date_magic
#import lots of dicts and things
from common.properties.dict_property import DictProperty
from advertiser.models import Creative
from publisher.models import AdUnit
from common.wurfl.query_managers import WurflQueryManager

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
MAR = 'marketing'
BRND = 'brand'
OS = 'os'
OS_VER = 'os_ver'
KEY = 'kw'
TARG = 'targeting' # I don't know what this is
C_TARG = 'custom targeting' # or this

ALL_COUNTRY = []
ALL_DEVICE = []
ALL_OS = []

NAME_STR = "dim%d-ent%d"


CRTV_DIMS = (CAMP, CRTV, P)
TIME_DIMS = (MO, WEEK, DAY, HOUR)
AU_DIMS = (APP, AU)
WURFL_DIMS = (MAR, BRND, OS, OS_VER)

NO_REQS = CRTV_DIMS

def build_stat_dict(stats):
    """ Return a dict that appears like a StatsModel object to django
        (haha django you are so dumb and easy to fool)

        Args:
            stats: List of stats, must have len = 5
        
        Returns:
            dict with keys like statsmodel properties
    """
    req, att, imp, clk, conv = stats
    return dict(request_count = req, 
                attempt_count = att, 
                impression_count = imp, 
                click_count = clk, 
                conversion_count = conv)

def statsify(stats_dict):
    """ Traverse the dict hierarchy, turning all list entries in all
        dictionaries into StatsModel-like dictionaries

        Args:
            stats_dict: dictionary of all stats to be formatted for viewing

        Returns:
            stats_dict, with objects instead of lists
    """
    for k,v in stats_dict.iteritems():
        #if it's stats, make them object-like
        if isinstance(v, list):
            stats_dict[k] = build_stat_dict(v)
        #elif they're sub_stats, statsify those
        elif isinstance(v, dict):
            stats_dict[k] = statsify(v)
    return stats_dict


            

#class ScheduledReport -> has a "next report" time, "report every ____" time, report type, when it's tim
#   to gen a report, this guy makes report objects
class ScheduledReport(db.Model):
    account = db.ReferenceProperty(collection_name='scheduled_reports')
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
    account = db.ReferenceProperty(collection_name='reports')
    created_at = db.DateTimeProperty(auto_now_add=True)

    #scheduled report
    schedule = db.ReferenceProperty(ScheduledReport, collection_name='reports')

    start = db.DateProperty(required=True)
    end = db.DateProperty(required=True)

    #the actual report (As of 6/13/11 with MR)
    report_blob = blobstore.BlobReferenceProperty()

    #the actual report
    data = DictProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()

    #Since we're cloning reports and they would both have the same key_name, no good
    clone_count = db.IntegerProperty()

    def __init__(self, parent=None, key_name=None, clone_count=0, **kwargs):
        if not key_name and not kwargs.get('key', None):
            sched = kwargs.get('schedule')
            start = kwargs.get('start')
            end = kwargs.get('end')
            acct = kwargs.get('account')
            start_str = start.strftime('%y%m%d') if start else 'None'
            end_str = end.strftime('%y%m%d') if end else 'None'
            acct_key = str(acct) if acct else 'None'
            d1 = sched.d1
            d2 = sched.d2
            d3 = sched.d3
            key_dict = dict(d1 = d1,
                            d2 = d2,
                            d3 = d3,
                            account = acct_key,
                            start = start_str,
                            end = end_str,
                            )
            if clone_count:
                key_dict.update(clone_count=clone_count)
                #Key this so it has a diff key than normal because it's a clone
                key_name = CLONE_REP_KEY % key_dict 
                #make this new guy have a higher clone count
                kwargs.update(clone_count = clone_count + 1)
            else:
                #no clone count, set clone_count = 1
                key_name = REP_KEY % key_dict
                kwargs.update(clone_count = 1)
        return super(Report, self).__init__(key_name=key_name, **kwargs)

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
    
    @property
    def html_data(self):
        if self.report_blob:
            magic = self.parse_report_blob(self.report_blob.open())
            return loader.render_to_string('reports/report.html', dict(all_stats=magic))
        #BACKWARDS COMPATIBILITY!
        elif self.data:
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
            det = "at least one dim is required"
        return det.title()

            
    #keys will either make sense, or be AU, CRTV
    """This is a second reduce.  It is possible to construct a worst-case scenario 
    (tons of creatives, very few campaigns (among others)) where this gets hella slow.
    This is done this way so the mapreduce NEVER has to touch the datastore to resolve things,
    all the resolution is done here.  In the future it might makes sense to take this and put it 
    into a second mapreduce job that's run when the report finalizes.
    """
    def parse_report_blob(self, blobreader):
        """ turns a reports report_blob blobstore object into a dictionary
        
        Args:
            blobreader: Line reader for this reports report_blob

        Returns:
            a dictionary of values in the following format:

            stats_dict = { KEY : 
                             { 'stats' : [req, att, etc.],
                               'name'  : <human readable name>,
                               'sub_stats' : stats_dict (recursiionnnn)
                              },
                              ....
                          }
        """
        final = {}
        for line in blobreader:
            #temp now refers to top of the dictionary
            temp = final
            keys, vals = line.split('||')
            keys = keys.split(':')
            vals = eval(vals)
            #I'm using list comprehension for you Nafis
            keys = [self.get_key_name(idx, key) for idx,key in enumerate(keys)]
            req, att = self.get_stats_info(keys)
            if not req:
                vals[0] = '---'
            if not att:
                vals[1] = '---'
            for i,(key,name) in enumerate(keys):
                #if this key doesn't exist, build that shit
                if not temp.has_key(key):
                    #this key doesn't exist, so no previous anything can exist
                    temp[key] = dict(name = name) 
                    if (i+1) == len(keys): #last key
                        temp[key]['stats'] = vals
                    else: #more keys
                        temp[key]['sub_stats'] = {}
                        #change our point of reference into the dict
                        #kind of like fake recursion
                        temp = temp[key]['sub_stats']
                else:
                    if temp[key]['name'] != name:
                        logging.warning("I fail at coding")
                    if (i+1) == len(keys):
                        #Since we're not doing anything smart-ish with the
                        #keys in the map/reduce phase (to speed it up by not
                        #doing Datastore reads) there is a possibility for 
                        #dupes.  If there are dupes, don't overwrite, sum
                        if temp[key].has_key('stats'):
                            temp[key]['stats'] = [sum(zipt) for zipt in zip(vals,temp[key]['stats'])]
                        else:
                            temp[key]['stats'] = vals
                    else:
                        #if no sub_stats entry, make it
                        if not temp[key].has_key('sub_stats'):
                            temp[key]['sub_stats'] = {}
                        temp = temp[key]['sub_stats']
        return statsify(final)


    def get_stats_info(self, keys):
        depth = len(keys)
        #If any of the dims are an adv, reqs is meaningless
        req = True
        att = False
        if not set((self.d1, self.d2, self.d3)).intersection(set(NO_REQ)):
            req = False
        for key, dim in zip(keys,(self.d1, self.d2, self.d3)):
            if dim in CRTV_DIMS:
                crtv = Creative.get(key)
                camp = crtv.adgroup.campaign
                #doesn't matter if we're crtv, camp, or priority, want to know the
                #campaign type and if it's a network regardless
                if crtv.adgroup.campaign.campaign_type == 'network':
                    att = True
        return (req, att)

    


    def get_key_name(self, idx, key):
        """ Turns arbitrary keys and things into human-readable names to 
            be output to the report

            Args:
               idx: level of this argument (should always be 0, 1, or 2)
               key: key string for this dim

            Returns:
                (key, name) so we can use 'key' for keying into DataTables
                and name to display
        """
        if idx == 0:
            dim = self.d1
        elif idx == 1:
            dim = self.d2
        elif idx == 2:
            dim = self.d3
        else:
            logging.error("Impossible dim level when rebuilding blob keys")
            dim = None

        if dim in CRTV_DIMS:
            crtv = Creative.get(key)
            if dim == CRTV:
                return (str(crtv.key()), crtv.name)
            elif dim == CAMP:
                camp = crtv.adgroup.campaign
                return (str(camp.key()), camp.name)
            elif dim == P:
                p = crtv.adgroup.campaign.campaign_type
                if 'gtee' in p:
                    p = 'guaranteed'
                return (p, p.title())

        elif dim in AU_DIMS:
            au = AdUnit.get(key)
            if dim == AU:
                return (str(au.key()), au.name)
            elif dim == APP:
                app = au.app_key
                return (str(app.key()), app.name)

        elif dim in TIME_DIMS:
            #This is cool that this was this easy

            #append dim to key because it's possible that day:hour breakdown
            #was requested, and the keys will be the same, this way they are uniquely 
            #ID'd
            time = datetime.strptime(key,'%y%m%d%H')
            return (key + dim, date_magic.date_name(time, dim))

        elif dim in WURFL_DIMS:
            return (key, WurflQueryManager().get_wurfl_name(key, dim))

        elif dim == CO:
            #TODO This needs to be fixed eventually...
            # Should be key, country(key) i.e. (US, United States) not (US, US)
            return (key, key)
        else:
            logging.warning("Not handling KW's yet")
