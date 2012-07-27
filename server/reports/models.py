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
from google.appengine.ext.webapp import template

#mopub imports
from account.models import Account
from advertiser.models import Creative
from common.constants import ISO_COUNTRIES, REP_KEY, CLONE_REP_KEY
from common.properties.dict_property import DictProperty
from common.utils import date_magic
from common.utils.helpers import cust_sum
from common.wurfl.query_managers import WurflQueryManager
from publisher.models import AdUnit
from mail.mails import (REPORT_FINISHED_SIMPLE,
                        REPORT_FAILED_SIMPLE,
                        REPORT_NO_DATA,
                        )

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

ONLINE_DIMS = CRTV_DIMS + AU_DIMS

NO_REQ = CRTV_DIMS
REPORT_MSG = '%s|%s|%s|%s|%s|%s|%s|%s'

LOG_FORMAT = "%s:\t%s\n"

FAILURE = 'REPFAIL%s'
NODAT = FAILURE % 0
MRFAILURE = FAILURE % 1
OTHER = FAILURE % 2

def log(mesg):
    try:
        my_log = open('/home/ubuntu/poller.log', 'a')
    except IOError:
        my_log = open('/tmp/poller.log', 'a')
    my_log.write(LOG_FORMAT % (time.time(), mesg))
    my_log.close()

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
    for k, v in stats_dict.iteritems():
        #if it's stats, make them object-like
        if isinstance(v, list):
            stats_dict[k] = build_stat_dict(v)
        #elif they're sub_stats, statsify those
        elif isinstance(v, dict):
            stats_dict[k] = statsify(v)
    return stats_dict




#class ScheduledReport -> has a "next report" time, "report every ____" time, report type, when it's time
#   to gen a report, this guy makes report objects
class ScheduledReport(db.Model):
    account = db.ReferenceProperty(collection_name='scheduled_reports')
    created_at = db.DateTimeProperty(auto_now_add=True)

    name = db.StringProperty()
    saved = db.BooleanProperty(default=False)
    deleted = db.BooleanProperty(default=False)
    last_run = db.DateTimeProperty()
    default = db.BooleanProperty(default=False)

    d1 = db.StringProperty(required=True)
    d2 = db.StringProperty()
    d3 = db.StringProperty()

    end = db.DateProperty(required=True)
    days = db.IntegerProperty(required=True)
    #daily, weekly, monthly
    interval = db.StringProperty(choices=['today', 'yesterday', '7days', 'lmonth', 'custom'], default='custom')

    sched_interval = db.StringProperty(choices = ['none', 'daily', 'weekly', 'monthly', 'quarterly'], default='none')
    next_sched_date = db.DateProperty(default=datetime.now().date())
    email = db.BooleanProperty(default=True)
    recipients = db.StringListProperty(default=[])

    _most_recent = db.ReferenceProperty(collection_name='parent_report')
    _details = db.StringProperty()
    _date_details = db.StringProperty()
    _dim_details = db.StringProperty()
    _status = db.StringProperty()


    @property
    def data(self):
        return self.most_recent.data

    @property
    def most_recent(self):
        if self._most_recent:
            return self._most_recent
        else:
            return self.reports.order('-created_at').get()
        #get the most recent report created by this scheduler

    @property
    def details(self):
        if self._details:
            return self._details
        else:
            return self.most_recent.details(self.interval)

    @property
    def date_details(self):
        if self._date_details:
            return self._date_details
        else:
            return self.most_recent.date_details(self.interval)

    @property
    def dim_details(self):
        if self._dim_details:
            return self._dim_details
        else:
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

    @property
    def status(self):
        if self.most_recent:
            return self.most_recent.status
        else:
            return self.status

    def __init__(self, *args, **kwargs):
        if 'next_sched_date' not in kwargs and 'sched_interval' in kwargs:
            sched_interval = kwargs.get('sched_interval')
            if sched_interval != 'none':
                kwargs['next_sched_date'] =  date_magic.get_next_day(sched_interval)
            else:
                kwargs['next_sched_date'] = datetime.now().date()

        super(ScheduledReport, self).__init__(*args, **kwargs)

class Report(db.Model):
    #standard
    account = db.ReferenceProperty(collection_name='reports')
    created_at = db.DateTimeProperty(auto_now_add=True)
    deleted = db.BooleanProperty(default=False)

    #scheduled report
    schedule = db.ReferenceProperty(ScheduledReport, collection_name='reports')

    start = db.DateProperty(required=True)
    end = db.DateProperty(required=True)

    #the actual report (As of 6/13/11 with MR)
    report_blob = blobstore.BlobReferenceProperty()

    html_data_blob = blobstore.BlobReferenceProperty()

    # This should never, ever be set on prod
    test_report_blob = db.TextProperty()

    #the actual report
    data = DictProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()
    status = db.StringProperty(default='Pending')

    @property
    def message(self):
        return REPORT_MSG % (self.d1, self.d2, self.d3, self.start.strftime('%y%m%d'), self.end.strftime('%y%m%d'), self.key(), self.account.key(), time.mktime(self.created_at.utctimetuple()))


    def notify_complete(self):
        mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                 subject = 'Your report has completed',
                                 bcc = 'report-monitoring@mopub.com')
        mesg_dict = dict(report_key = str(self.schedule.key()),
                         dim1 = self.d1,
                         dim2 = self.d2,
                         dim3 = self.d3,
                         start = self.start.strftime('%m/%d/%y'),
                         end = self.end.strftime('%m/%d/%y'))
        mesg.body = REPORT_FINISHED_SIMPLE % mesg_dict
        if self.email and self.recipients:
            mesg.to = self.recipients
        else:
            mesg.to = 'report-monitoring@mopub.com'

        try:
            mesg.send()
        except mail.InvalidEmailError, e:
            pass

    def notify_failure(self, reason=OTHER):
        mesg_dict = dict(dim1 = self.d1,
                         dim2 = self.d2,
                         dim3 = self.d3,
                         start = self.start.strftime('%m/%d/%y'),
                         end = self.end.strftime('%m/%d/%y'))
        if reason == NODAT:
            mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                     subject = 'No data for your report',
                                     bcc = 'report-monitoring@mopub.com',
                                     )
            mesg.body = REPORT_NO_DATA % mesg_dict
        else:
            mesg = mail.EmailMessage(sender = 'olp@mopub.com',
                                     subject = 'Your report has failed',
                                     bcc = 'report-monitoring@mopub.com',
                                     )
            mesg.body = REPORT_FAILED_SIMPLE % mesg_dict

        if self.email and self.recipients:
            mesg.to = self.recipients
        else:
            mesg.to = 'report-monitoring@mopub.com'

        try:
            mesg.send()
        except mail.InvalidEmailError, e:
            pass

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
    def dims(self):
        return [self.d1, self.d2, self.d3]

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
        """ Turns the dictionary into a list of lists """
        if self.data:
            level_total = sum([1 for d in self.dims if d])
            data = self.get_export_data(0, level_total - 1, [], self.data)
            return data
        else:
            return None

    def get_export_data(self, level, level_total, names, stats_dict):
        if self.dims[level] == DAY and self.report_blob:
            # sort days numerically
            keys = sorted(stats_dict.keys(), key=lambda a: int(a[:a.find('day')]))
        else:
            # sort everything else alphabetically
            keys = sorted(stats_dict.keys())

        data_list = []
        for key in keys:
            value = stats_dict[key]
            data = list(names)
            data.append(value['name'])

            if level_total == level:
                if isinstance(value['stats'], dict):
                    impressions = float(value['stats']['impression_count'])
                    ctr = 'n/a' if impressions == 0 else value['stats']['click_count'] / impressions
                    data += [value['stats']['request_count'], value['stats']['impression_count'], value['stats']['click_count'], value['stats']['conversion_count'], value['stats']['revenue'], ctr]
                else:
                    data += [value['stats'].request_count, value['stats'].impression_count, value['stats'].click_count, value['stats'].conversion_count]

                data_list.append(data)

            if 'sub_stats' in value:
                temp_names = list(names)
                temp_names.append(value['name'])
                data_list += (self.get_export_data(level + 1, level_total, temp_names, value['sub_stats']))

        return data_list



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


    def batch_get_objs(self, blobreader, offline=False):
        """ Takes a blobreader, goes through the lines and gets the keys that
        neede a db get and batches them, then gets all of them and derefs
        them to the appropriate obj (apps from adunits for example)"""
        if offline:
            return None
        batch = {}
        key_dims = {}
        # Map everything to objects by (dim, key) since everything of
        # simliar types has the same key, but the dims are different
        # so the (dim, key) pairs are unique
        dimkey_to_obj = {}
        batch[CRTV] = []
        batch[AU] = []
        for line in blobreader:
            keys, vals = line.split('\t')
            keys = keys.split(':')
            for i, key in enumerate(keys):
                if i == 0:
                    dim = self.d1
                elif i == 1:
                    dim = self.d2
                elif i == 2:
                    dim = self.d3

                if dim not in ONLINE_DIMS:
                    continue

                if key not in key_dims:
                    key_dims[key] = []

                if dim not in key_dims[key]:
                    key_dims[key].append(dim)

                if dim in CRTV_DIMS:
                    if key not in batch[CRTV]:
                        batch[CRTV].append(key)

                elif dim in AU_DIMS:
                    if key not in batch[AU]:
                        batch[AU].append(key)

        if offline:
            return dimkey_to_obj

        # list of everything
        log("Batch[AU]: %s" % batch[AU])
        log("Batch[CRTV]: %s" % batch[CRTV])
        adunits = AdUnit.get(batch[AU])
        crtvs = Creative.get(batch[CRTV])

        for adunit in adunits:
            if not adunit:
                continue
            obj_key = str(adunit.key())
            for dim in key_dims[obj_key]:
                key_tuple = (str(dim), obj_key)
                if dim == AU:
                    dimkey_to_obj[key_tuple] = adunit
                elif dim == APP:
                    dimkey_to_obj[key_tuple] = adunit.app_key

        for crtv in crtvs:
            if not crtv:
                continue
            obj_key = str(crtv.key())
            for dim in key_dims[obj_key]:
                key_tuple = (str(dim), obj_key)
                crtv_tuple = (str(CRTV), obj_key)

                if dim == CRTV:
                    dimkey_to_obj[key_tuple] = crtv
                elif dim == CAMP:
                    dimkey_to_obj[key_tuple] = crtv.adgroup.campaign
                    dimkey_to_obj[crtv_tuple] = crtv
                elif dim == P:
                    priority = crtv.adgroup.campaign.campaign_type
                    if 'gtee' in priority:
                        priority = 'guaranteed'
                    dimkey_to_obj[key_tuple] = priority
                    dimkey_to_obj[crtv_tuple] = crtv

        blobreader.close()
        return dimkey_to_obj





    #keys will either make sense, or be AU, CRTV
    """This is a second reduce.  It is possible to construct a worst-case scenario
    (tons of creatives, very few campaigns (among others)) where this gets hella slow.
    This is done this way so the mapreduce NEVER has to touch the datastore to resolve things,
    all the resolution is done here.  In the future it might makes sense to take this and put it
    into a second mapreduce job that's run when the report finalizes.
    """
    def parse_report_blob(self, blobreader, dimkey_to_obj, testing=False):
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
        if testing:
            blobreader = blobreader.split('\n')[:-1]
        for line in blobreader:
            #temp now refers to top of the dictionary
            temp = final
            keys, vals = line.split('\t')
            keys = keys.split(':')
            keylen = len(keys)
            if keylen == 1:
                dim_list = (self.d1,)
            elif keylen == 2:
                dim_list = (self.d1, self.d2)
            elif keylen == 3:
                dim_list = (self.d1, self.d2, self.d3)
            dims_keys = zip(keys, dim_list)
            # Hack because people fucking broke shit and deleted things
            # and other dumb shit
            all_keys_in = [False] * len(keys)
            for dimkey in dimkey_to_obj:
                for i, (key, dim) in enumerate(dims_keys):
                    if key in dimkey or dim not in ONLINE_DIMS:
                        all_keys_in[i] = True

            if dimkey_to_obj and not all(all_keys_in):
                continue
            vals = eval(vals)
            req, att = self.get_stats_info(keys, dimkey_to_obj, testing)
            #I'm using list comprehension for you Nafis
            bid_infos = [self.get_bid_info(idx, key, dimkey_to_obj, testing) for idx, key in enumerate(keys)]
            keys = [self.get_key_name(idx, key, dimkey_to_obj, testing) for idx, key in enumerate(keys)]

            # Invalid key somewhere in this line, don't use it
            if None in keys:
                continue
            if not req:
                vals[0] = '---'
            if not att:
                vals[1] = '---'
            for i, ((key, name), (bid_strat, bid)) in enumerate(zip(keys, bid_infos)):
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
                            temp[key]['stats'] = [cust_sum(zipt) for zipt in zip(vals, temp[key]['stats'])]
                        else:
                            temp[key]['stats'] = vals
                    else:
                        #if no sub_stats entry, make it
                        if not temp[key].has_key('sub_stats'):
                            temp[key]['sub_stats'] = {}
                        temp = temp[key]['sub_stats']

        # add missing days on a request for a range
        self.add_missing_dates(0, final)

        # logging.debug(final)
        if not testing:
            blobreader.close()
        return self.rollup_revenue(statsify(final))


    def add_missing_dates(self, level, stats_dict):
        d = self.dims[level]
        if d == DAY:
            dates = set(stats_dict.keys())
            stats_len = len(stats_dict[stats_dict.keys()[0]]['stats'])

            # go from start date to end date checking if date is in the hash set
            # if it's not add it to final
            for single_date in date_magic.gen_days(self.start, self.end - timedelta(days=1)):
                # key is in '%y%m%dday' format
                if single_date.strftime('%y%m%dday') not in dates:
                    stats_dict[single_date.strftime('%y%m%dday')] = {'stats' : [0] * stats_len,
                                                                     'name'  : date_magic.date_name(single_date, d)}
        else:
            for key in stats_dict.keys():
                # sub_stats is not in dict when it isn't used
                if 'sub_stats' in stats_dict[key]:
                    self.add_missing_dates(level + 1, stats_dict[key]['sub_stats'])

    def rollup_revenue(self, stats):
        def rollup_help(stats, depth):
            rev = 0.0
            for k, v in stats.iteritems():
                if depth == 0:
                    # Bottom level, just roll up
                    rev += v['stats']['revenue']
                else:
                    # Not bottom level, roll up and set
                    if 'sub_stats' in v:
                        rev += rollup_help(v['sub_stats'], depth-1)
                    stats[k]['stats']['revenue'] = rev
            return rev
        if self.d1 in [CRTV, CAMP]:
            # Top level already rolled up
            return stats
        elif self.d2 in [CRTV, CAMP]:
            depth = 0
        elif self.d3 in [CRTV, CAMP]:
            depth = 1
        else:
            # No levels have rev
            return stats

        for k,v in stats.iteritems():
            if 'sub_stats' in v:
                stats[k]['stats']['revenue'] = rollup_help(v['sub_stats'], depth)
            else:
                stats[k]['stats']['revenue'] = '---'
        return stats



    def get_stats_info(self, keys, dimkey_to_obj, offline = False):
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
            logging.warning('Keys: %s' % keys)
        if set(dim_list).intersection(set(NO_REQ)):
            req = False
        if offline:
            return (req, False)
        for key, dim in zip(keys, dim_list):
            if dim in CRTV_DIMS:
                key_tuple = (str(dim), str(key))
                if dim == CRTV:
                    crtv = dimkey_to_obj[key_tuple]
                    priority = crtv.adgroup.campaign.campaign_type

                elif dim == CAMP:
                    camp = dimkey_to_obj[key_tuple]
                    priority = camp.campaign_type

                elif dim == P:
                    priority = dimkey_to_obj[key_tuple]

                else:
                    priority = None
                if priority == 'network':
                    att = True

        return (req, att)

    def get_bid_info(self, idx, key, dimkey_to_obj, offline = False):
        if idx == 0:
            dim = self.d1
        elif idx == 1:
            dim = self.d2
        elif idx == 2:
            dim = self.d3
        else:
            dim = None

        if offline:
            return None, None

        key_tuple = (str(CRTV), str(key))
        if dim in [CAMP, CRTV]:
            crtv = dimkey_to_obj[key_tuple]
            adgroup = crtv.adgroup
            try:
                if adgroup.campaign.campaign_type in ('network', 'marketplace', 'backfill_marketplace'):
                    return None, None
                else:
                    return (adgroup.bid_strategy, adgroup.bid)
            except Exception:
                # This should only ever be called by the EC2 instance, so
                # this should be safe
                f = open('/home/ubuntu/tb.log', 'a')
                traceback.print_exc(file=f)
                f.close()
                return None, None

        return None, None

    def get_key_name(self, idx, key, dimkey_to_obj, offline=False):
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

        if dim in ONLINE_DIMS and offline:
            return ('%s-%s' % (dim, key), key)

        key_tuple = (str(dim), str(key))

        if dim in CRTV_DIMS:
            if dim == CRTV:
                crtv = dimkey_to_obj[key_tuple]
                return (str(crtv.key()), crtv.name)
            elif dim == CAMP:
                camp = dimkey_to_obj[key_tuple]
                return (str(camp.key()), camp.name)
            elif dim == P:
                priority = dimkey_to_obj[key_tuple]
                return (priority, priority.title())

        elif dim in AU_DIMS:
            if dim == AU:
                adunit = dimkey_to_obj[key_tuple]
                return (str(adunit.key()), adunit.name)
            elif dim == APP:
                app = dimkey_to_obj[key_tuple]
                return (str(app.key()), app.name)

        elif dim in TIME_DIMS:
            #This is cool that this was this easy

            #append dim to key because it's possible that day:hour breakdown
            #was requested, and the keys will be the same, this way they are uniquely
            #ID'd
            try:
                if dim == MO:
                    time_key = datetime.strptime(key,'%y%m')
                elif dim == WEEK:
                    key1 = '1' + key
                    key2 = '0' + key
                    time_key = (datetime.strptime(key1,'%w%y%W'), datetime.strptime(key2,'%w%y%W'))
                elif dim == DAY:
                    time_key = datetime.strptime(key,'%y%m%d')
                elif dim == HOUR:
                    time_key = datetime.strptime(key,'%H')
                else:
                    time_key = None
                return (key + dim, date_magic.date_name(time_key, dim))
            except Exception:
                return None

        elif dim in WURFL_DIMS:
            try:
                return (key, WurflQueryManager().get_wurfl_name(key, dim))
            except Exception:
                return None

        elif dim == CO:
            #TODO This needs to be fixed eventually...
            # Should be key, country(key) i.e. (US, United States) not (US, US)
            return (key, key)
        else:
            logging.warning("Not handling KW's yet")
