#generic python imports
import logging
import time
import traceback
import sys

from datetime import datetime, timedelta

from django.template import loader
#appengine imports
from google.appengine.ext import db
from google.appengine.ext import blobstore
from google.appengine.api import users, mail

#mopub imports
from account.models import Account
from advertiser.models import Creative
from common.constants import ISO_COUNTRIES, REP_KEY, CLONE_REP_KEY
from common.properties.dict_property import DictProperty
from common.utils import date_magic
from common.utils.helpers import cust_sum
from common.wurfl.query_managers import WurflQueryManager
from publisher.models import AdUnit
from mail.mails import REPORT_FINISHED_SIMPLE

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

NO_REQ = CRTV_DIMS

def build_stat_dict(stats):
    """ Return a dict that appears like a StatsModel object to django
        (haha django you are so dumb and easy to fool)

        Args:
            stats: List of stats, must have len = 5
        
        Returns:
            dict with keys like statsmodel properties
    """
    rev, req, att, imp, clk, conv = stats
    return dict(revenue = rev,
                request_count = req, 
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
    default = db.BooleanProperty(default=False)

    d1 = db.StringProperty(required=True) 
    d2 = db.StringProperty() 
    d3 = db.StringProperty() 

    end = db.DateProperty(required=True)
    days = db.IntegerProperty(required=True)
    #daily, weekly, monthly
    interval = db.StringProperty(choices=['today','yesterday', '7days', 'lmonth', 'custom'], default='custom')
    
    sched_interval = db.StringProperty(choices = ['none', 'daily', 'weekly', 'monthly', 'quarterly'], default='none')
    next_sched_date = db.DateProperty(default=datetime.now().date())
    email = db.BooleanProperty(default=False)
    recipients = db.StringListProperty(default=[])

    @property
    def data(self):
        return self.most_recent.data

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

    @property
    def schedule_details(self):
        if self.sched_interval == 'none':
            return None
        else:
            ret = '('+self.sched_interval+')'
            return ret.title()

    @property
    def interval_details(self):
        if self.interval == '7days':
            return 'Last 7 days'
        elif self.interval == 'lmonth':
            return 'Last month'
        else:
            return self.interval.title()

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


    def notify_complete(self):
        mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                 subject = 'Your report has completed')
        mesg_dict = dict(report_key = str(self.schedule.key()))
        mesg.body = REPORT_FINISHED_SIMPLE % mesg_dict
        if self.recipients:
            for recipient in self.recipients:
                mesg.to = recipient
                try:
                    mesg.send()
                except InvalidEmailError, e:
                    pass
        else:
            return

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

    @property
    def schedule_details(self):
        return self.schedule.schedule_details

    @property
    def interval_details(self):
        return self.schedule.interval_details

    @property
    def email(self):
        return self.schedule.email

    @property
    def recipients(self):
        return self.schedule.recipients

    @property
    def days(self):
        return self.schedule.days

    def __str__(self):
        return "Report(d1=%s, d2=%s, d3=%s, start=%s, end=%s)" % (self.d1, self.d2, self.d3, self.start, self.end)
    
    @property
    def html_data(self):
        return loader.render_to_string('reports/report.html', dict(all_stats=self.data))
        #if self.report_blob:
        #    logging.warning("parsing report blob")
        #    magic = self.parse_report_blob(self.report_blob.open())
        #    logging.warning('\n%s\n' % magic)
        #    return loader.render_to_string('reports/report.html', dict(all_stats=magic))
        #BACKWARDS COMPATIBILITY!
        #elif self.data:
        #   pass
        #else:
        #    return None
    @property
    def export_data(self):
        """ Turns the dictionary into a list lists """ 
        if self.data:
            d2 = d3 = False
            if self.d2:
                d2 = True
            if self.d3:
                d3 = True
            ret = []
            for key, value in self.data.iteritems():
                dat = [value['name']]
                if d2:
                    dat.append('')
                if d3:
                    dat.append('')
                if isinstance(value['stats'], dict):
                    stat_dat = [value['stats']['request_count'],value['stats']['impression_count'], value['stats']['click_count'], value['stats']['conversion_count']]
                else:
                    stat_dat = [value['stats'].request_count, value['stats'].impression_count, value['stats'].click_count, value['stats'].conversion_count] 
                dat += stat_dat
                ret.append(dat)
                #There's a smarter way to do this, but I'm in a hurry and (hopefully) this isn't needed for long
                if value.has_key('sub_stats'):
                    for key2, value2 in value['sub_stats'].iteritems():
                        dat2 = [value['name'], value2['name']]
                        if d3:
                            dat2.append('')
                        if isinstance(value2['stats'], dict):
                            stat_dat2 = [value2['stats']['request_count'],value2['stats']['impression_count'], value2['stats']['click_count'], value2['stats']['conversion_count']]
                        else:
                            stat_dat2 = [value2['stats'].request_count, value2['stats'].impression_count, value2['stats'].click_count, value2['stats'].conversion_count] 
                        dat2 += stat_dat2
                        ret.append(dat2)
                        #Really stupid
                        if value2.has_key('sub_stats'):
                            for key3, value3 in value2['sub_stats'].iteritems():
                                if isinstance(value3['stats'], dict):
                                    stat_dat3 = [value3['stats']['request_count'],value3['stats']['impression_count'], value3['stats']['click_count'], value3['stats']['conversion_count']]
                                else:
                                    stat_dat3 = [value3['stats'].request_count, value3['stats'].impression_count, value3['stats'].click_count, value3['stats'].conversion_count] 
                                dat3 = [value['name'], value2['name'], value3['name']] + stat_dat3
                                ret.append(dat3)
        else:
            return None
        return ret

    
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
        memo = {}
        for line in blobreader:
            #temp now refers to top of the dictionary
            temp = final
            keys, vals = line.split('\t')
            keys = keys.split(':')
            vals = eval(vals)
            req, att = self.get_stats_info(keys)
            #I'm using list comprehension for you Nafis
            bid_infos = [self.get_bid_info(idx, key, memo) for idx, key in enumerate(keys)]
            keys = [self.get_key_name(idx, key, memo) for idx,key in enumerate(keys)]

            # Invalid key somewhere in this line, don't use it
            if None in keys:
                continue
            if not req:
                vals[0] = '---'
            if not att:
                vals[1] = '---'
            for i,((key,name), (bid_strat, bid)) in enumerate(zip(keys, bid_infos)):
                # Preprocess the values to add revenue
                if len(vals) == 5:
                    rev = 0
                    req, att, imp, clk, conv = vals
                elif len(vals) == 6:
                    rev, req, att, imp, clk, conv = vals
                # Need to set rev if we can
                if bid_strat is not None:
                    if bid_strat == 'cpm':
                        rev = float(bid * imp)/1000
                    elif bid_strat == 'cpc':
                        rev = bid * clk
                    elif bid_strat == 'cpa':
                        rev = bid * conv
                vals = [rev, req, att, imp, clk, conv]
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
                            temp[key]['stats'] = [cust_sum(zipt) for zipt in zip(vals,temp[key]['stats'])]
                        else:
                            temp[key]['stats'] = vals
                    else:
                        #if no sub_stats entry, make it
                        if not temp[key].has_key('sub_stats'):
                            temp[key]['sub_stats'] = {}
                        temp = temp[key]['sub_stats']
        logging.debug(final)
        return self.rollup_revenue(statsify(final))


    def rollup_revenue(self, stats):
        def rollup_help(stats, depth):
            rev = 0.0
            for k,v in stats.iteritems():
                if depth == 0:
                    # Bottom level, just roll up
                    rev += v['stats']['revenue']
                else:
                    # Not bottom level, roll up and set 
                    rev += rollup_help(v['sub_stats'], depth-1)
                    stats[k]['stats']['revenue'] = rev
            return rev
        if self.d1 in [CRTV, CAMP]:
            # Top level already rolled up
            return stats
        elif self.d2 in [CRTV, CAMP]:
            depth = 0
        elif self.d3 in [CRTV,CAMP]:
            depth = 1
        else:
            # No levels have rev
            return stats

        for k,v in stats.iteritems():
            stats[k]['stats']['revenue'] = rollup_help(v['sub_stats'], depth)
        return stats



    def get_stats_info(self, keys):
        depth = len(keys)
        #If any of the dims are an adv, reqs is meaningless
        req = True
        att = False
        #only take all the dims that there are keys for
        if depth == 1:
            dim_list = (self.d1,)
        elif depth == 2:
            dim_list = (self.d1, self.d2)
        elif depth == 3:
            dim_list = (self.d1, self.d2, self.d3)
        else:
            logging.warning('Invalid key length')
        if set(dim_list).intersection(set(NO_REQ)):
            req = False
        for key, dim in zip(keys,dim_list):
            if dim in CRTV_DIMS:
                try:
                    crtv = Creative.get(key)
                #doesn't matter if we're crtv, camp, or priority, want to know the
                #campaign type and if it's a network regardless
                    if crtv.adgroup.campaign.campaign_type == 'network':
                        att = True
                except:
                    att = False
        return (req, att)

    def get_bid_info(self, idx, key, memo): 
        if idx == 0:
            dim = self.d1
        elif idx == 1:
            dim = self.d2
        elif idx == 2:
            dim = self.d3
        else:
            dim = None

        if dim in [CAMP, CRTV]:
            try:
                if memo.has_key(key):
                    crtv = memo[key]
                else:
                    crtv = Creative.get(key)
                    memo[key] = crtv
                if crtv.adgroup.campaign.campaign_type == 'network':
                    return None, None
                if dim == CRTV:
                    return (crtv.adgroup.bid_strategy, crtv.adgroup.bid)
                elif dim == CAMP:
                    camp = crtv.adgroup.campaign
                    return (crtv.adgroup.bid_strategy, crtv.adgroup.bid)
            except:
                log("Exception in bid info")
                f = open('/home/ubuntu/tb.log', 'a')
                traceback.print_tb(sys.exc_info()[2], file=f)
                f.close()
                return None, None
        return None, None


    def get_key_name(self, idx, key, memo):
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
            try:
                if memo.has_key(key):
                    crtv = memo[key]
                else:
                    crtv = Creative.get(key)
                    memo[key] = crtv
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
            except:
                return None

        elif dim in AU_DIMS:
            try:
                if memo.has_key(key):
                    au = memo[key]
                else:
                    au = AdUnit.get(key)
                    memo[key] = au
                if dim == AU:
                    return (str(au.key()), au.name)
                elif dim == APP:
                    app = au.app_key
                    return (str(app.key()), app.name)
            except:
                return None

        elif dim in TIME_DIMS:
            #This is cool that this was this easy

            #append dim to key because it's possible that day:hour breakdown
            #was requested, and the keys will be the same, this way they are uniquely 
            #ID'd
            try:
                if memo.has_key(key):
                    time = memo[key]
                else:
                    if dim == MO:
                        time = datetime.strptime(key,'%y%m')
                    elif dim == WEEK:
                        key1 = '0' + key
                        key2 = '6' + key
                        time = (datetime.strptime(key1,'%U%y%W'), datetime.strptime(key2,'%U%y%W'))
                    elif dim == DAY:
                        time = datetime.strptime(key,'%y%m%d')
                    elif dim == HOUR:
                        time = datetime.strptime(key,'%H')
                    else:
                        time = None
                    memo[key] = time
                return (key + dim, date_magic.date_name(time, dim))
            except:
                return None

        elif dim in WURFL_DIMS:
            try:
                return (key, WurflQueryManager().get_wurfl_name(key, dim))
            except:
                return None

        elif dim == CO:
            #TODO This needs to be fixed eventually...
            # Should be key, country(key) i.e. (US, United States) not (US, US)
            return (key, key)
        else:
            logging.warning("Not handling KW's yet")
