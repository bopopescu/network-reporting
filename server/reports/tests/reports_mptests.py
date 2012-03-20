import os, sys
import pprint
import pickle

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

import datetime
import logging
import random

import unittest
from nose.tools import eq_
from google.appengine.api import apiproxy_stub_map, memcache
from google.appengine.ext import db
from google.appengine.ext import testbed


#from django.template.loader import render_to_string
from advertiser.models import AdGroup, Creative, Campaign
from account.models import Account
from common.utils import date_magic
from publisher.models import App
from publisher.models import Site as AdUnit
from reports.models import Report, ScheduledReport
from reports.aws_reports.report_mapper import mapper_test, reduce_test
from reports.aws_reports.parse_utils import MO, WEEK, DAY, HOUR, DATE_FMT, DATE_FMT_HR, DATE_HR_LEN, DATE_LEN
from reports.query_managers import ReportQueryManager

#allows me to seed the random number generator so every time
#we get the same sequence of random numbers
DATE = datetime.date(2011,1,1)

DIMS = [None, 'app', 'adunit', 'campaign', 'creative', 'day', 'hour', 'country', 'marketing', 'brand', 'os', 'os_ver']

TIME_DIMS = ('day', 'hour')

INVALID_PAIRS = [('adunit', 'app'), ('creative', 'campaign'), ('hour', 'day'), ('os_ver', 'os'), ('marketing', 'brand')]

STATS = ('request_count', 'impression_count', 'click_count', 'conversion_count', 'revenue')

DIR = os.path.dirname(__file__)

NOW = datetime.datetime(2011, 1, 1).date()
one_day = datetime.timedelta(days=1)



def make_get_data(d1, d2=None, d3=None):
    """ Don't care about days because we're assuming that's all handled properly """
    file = open(DIR + '/test_data2.dat')
    fin = {}

    #Yo dawg, I heard you like functional programming
    mapt = reduce(lambda x,y: x+y, [[(key, val) for (key, val) in [out.split('\t') for out in mapper_test(line, d1, d2, d3)]] for line in file])

    mapt2 = map(lambda (key,vals): fin.update({key:vals}), [(key1, map(lambda (key3, value3): value3, filter(lambda (key2, value2): key1==key2, mapt))) for (key1, value1) in mapt])

    map_red = reduce(lambda x,y: x+y, [[a for a in reduce_test(key, values)] for key, values in fin.iteritems()])
    return map_red


def verify_data(data, *dims):
    file = open(DIR + '/test_data2.dat')
    lines = [line for line in file]
    for datum in data:
        keys, values = datum.split("\t")
        values = eval(values)
        logging.warning("Values is: %s" % values)
        lines_to_sum = []
        for line in lines:
            for i, key in enumerate(keys.split(':')):
                # When building the key for os_ver we append the os on so it makes sense when reading it.
                # This was done because wurfl is rtarded
                key_temp = ':%s:'
                if dims[i] in TIME_DIMS:
                    key_list, vals = line.split("\t")
                    t_keys = key_list.split(":")
                    time_key = t_keys[-1]

                    if len(time_key) == DATE_LEN:
                        time_obj = datetime.datetime.strptime(time_key, DATE_FMT)
                    elif len(time_key) == DATE_HR_LEN:
                        time_obj = datetime.datetime.strptime(time_key, DATE_FMT_HR)

                    if MO == dims[i]:
                        time_key = time_obj.strftime('%y%m')
                    elif WEEK == dims[i]: 
                        time_key = time_obj.strftime('%y%W')
                    elif DAY == dims[i]:
                        time_key = time_obj.strftime('%y%m%d')
                    elif HOUR == dims[i]:
                        time_key = time_obj.strftime('%H')
                    if not time_key == key:
                        break

                elif dims[i] == 'os_ver':
                    os_ver = key.split('_')[-1]
                    os = key.replace('_'+os_ver, '')
                    if key_temp % os_ver not in line:
                        break
                    if key_temp % os not in line:
                        break
                elif key_temp % key not in line:
                    break
            else:
                lines_to_sum.append(line)
        logging.warning("Lines to sum: %s" % lines_to_sum)
        vals_to_sum = []
        for line in lines_to_sum:
            key, vals = line.split('[')
            vals_to_sum.append(eval('[' + vals))
        summed_vals = [sum(zipt) for zipt in zip(*vals_to_sum)]
        logging.warning(keys)
        logging.warning(lines_to_sum)
        logging.warning('d1: %s, d2: %s, d3: %s' % dims)
        logging.warning("\nFrom map_red: %s\tComputed: %s\tEqual: %s" % (values, summed_vals, values == summed_vals))
        assert values == summed_vals
                

DONE_COMBOS = []

def report_runner(d1):                
    global DONE_COMBOS
    end = DATE + one_day
    start = DATE
    days = (end - start).days
    dt = datetime.timedelta(days=days)
    sched_past = NOW - one_day
    for d2 in DIMS:
        if (d1, d2) in INVALID_PAIRS or (d1 == d2):
            continue
        for d3 in DIMS:
            if (d2 is None and d3 is not None) or ((d1, d3) in INVALID_PAIRS) or ((d2, d3) in INVALID_PAIRS) or (d1 == d3) or (d2 == d3):
                continue
            if (d3 is None and (d1,d2) in DONE_COMBOS) or ((d2,d3) in DONE_COMBOS):
                continue
            DONE_COMBOS.append((d1,d2))
            DONE_COMBOS.append((d2,d3))
            verify_data(make_get_data(d1, d2=d2, d3=d3), d1, d2, d3)

def date_addition_mptest():
    end = datetime.date(2011, 8, 30)
    last_run = datetime.datetime(2011, 8, 30, 9, 47, 49, 727180)
    next_sched_date = datetime.date(2011, 8, 30)
    sched = ScheduledReport(d1 = 'campaign', 
                            d2 = 'creative',
                            d3 = 'day',
                            days = 7,
                            default = False,
                            deleted = False,
                            email = False,
                            end = end,
                            interval = '7days',
                            last_run = last_run,
                            name = 'Campaign > Creative > Day - Last 7 Days',
                            next_sched_date = next_sched_date,
                            saved = True,
                            sched_interval = None
                            )
    sched.put()
    completed_at = datetime.datetime(2011, 8, 30, 9, 54, 49, 164974)
    created_at = datetime.datetime(2011, 8, 30, 9, 47, 49, 624807)
    
    f = open(DIR + '/needs_days_added.dat').read()
    
    start = datetime.date(2011, 8, 23)
    rep = Report(completed_at = completed_at,
                 created_at = created_at,
                 end = end, # maybe these should be seperate objects
                 test_report_blob = f,
                 schedule = sched,
                 start = start
                 )
    # Should work....I think....
    rep.data = rep.parse_report_blob(f, {}, testing=True)
    check_missing_dates(0, [sched.d1, sched.d2, sched.d3], rep.data, sched.days)
    rep.export_data
    #assert False, rep.export_data
    
def check_missing_dates(level, dims, stats_dict, num_days):
    d = dims[level]
    if d in TIME_DIMS and d == 'day':
        assert len(stats_dict.keys()) == num_days, (stats_dict.keys(), num_days)
    else:
        for key in stats_dict.keys():
            # assumes sub_stats is not even in dict when it isn't used
            if 'sub_stats' in stats_dict[key]:
                check_missing_dates(level + 1, dims, stats_dict[key]['sub_stats'], num_days)


def os_mptest():
    report_runner('os')
 
def app_mptest():
    report_runner('app')

def adunit_mptest():
    report_runner('adunit')

def campaign_mptest():
    report_runner('campaign')

def creative_mptest():
    report_runner('creative')

def day_mptest():
    report_runner('day')

def hour_mptest():
    report_runner('hour')

def country_mptest():
    report_runner('country')

def marketing_mptest():
    report_runner('marketing')
            
def brand_mptest():
    report_runner('brand')

def os_ver_mptest():
    report_runner('os_ver')

#***********************#
#   SCHEDULED  REPORT   #
#         TESTS         #
#***********************#


def get_scheduled_reps(date):
    man = ReportQueryManager()
    reps = ScheduledReport.all().filter('next_sched_date =', date)
    return [rep for rep in reps]


#################
#  Simple tests #
#################
#acct = Account()
#acct.put()
#
#man = ReportQueryManager(account=acct)
#
#def none_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='none_test', sched_interval = 'none', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 1
#    assert len(get_scheduled_reps(NOW + one_day)) == 0
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def daily_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='daily_test', sched_interval = 'daily', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 0 
#    assert len(get_scheduled_reps(NOW + one_day)) == 1
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def double_daily_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='dub_daily_test', sched_interval = 'daily', testing = True)
#    def assrt_daily(dte):
#        assert len(get_scheduled_reps(dte)) == 0 
#        assert len(get_scheduled_reps(dte + one_day)) == 1
#
#    assrt_daily(NOW)
#    tom = NOW + one_day
#    s = man.new_report(str(s.most_recent.key()), now=tom, testing=True)
#    assrt_daily(tom)
#
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def weekly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='weekly_test', sched_interval = 'weekly', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 0 
#    dte = NOW + one_day
#    for i in range(7):
#        if dte.weekday() == 0:
#            assert len(get_scheduled_reps(dte)) == 1
#            break
#        else:
#            assert len(get_scheduled_reps(dte)) == 0
#        dte += one_day
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return 
#    
#def double_weekly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='dub_weekly_test', sched_interval = 'weekly', testing = True)
#    def assrt_weekly(dte):
#        assert len(get_scheduled_reps(dte)) == 0 
#        dte = dte + one_day
#        for i in range(7):
#            if dte.weekday() == 0:
#                assert len(get_scheduled_reps(dte)) == 1
#                return dte
#            else:
#                assert len(get_scheduled_reps(dte)) == 0
#            dte += one_day
#
#    next_day = assrt_weekly(NOW)
#    s = man.new_report(str(s.most_recent.key()), now=next_day, testing=True)
#    assrt_weekly(next_day)
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def monthly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='monthly_test', sched_interval = 'monthly', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 0
#    dte = NOW + one_day
#    while dte.day != 1:
#        assert len(get_scheduled_reps(dte)) == 0
#        dte += one_day
#    assert len(get_scheduled_reps(dte)) == 1
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def double_monthly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='dub_monthly_test', sched_interval = 'monthly', testing = True)
#    def assrt_monthly(dte):
#        assert len(get_scheduled_reps(dte)) == 0
#        dte = dte + one_day
#        while dte.day != 1:
#            assert len(get_scheduled_reps(dte)) == 0
#            dte += one_day
#        assert len(get_scheduled_reps(dte)) == 1
#        return dte
#    next_day = assrt_monthly(NOW)
#    s = man.new_report(str(s.most_recent.key()), now=next_day, testing=True)
#    assrt_monthly(next_day)
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
##
#def quarterly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='quarterly_test', sched_interval = 'quarterly', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 0
#    end = datetime.datetime(2011, 4, 1).date()
#    dte = NOW + one_day
#    while dte != end:
#        assert len(get_scheduled_reps(dte)) == 0
#        dte += one_day
#    assert len(get_scheduled_reps(dte)) == 1
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return
#
#def double_quarterly_mptest():
#    s = man.add_report('app', None, None, NOW, 4, name='dub_quarterly_test', sched_interval = 'quarterly', testing = True)
#    assert len(get_scheduled_reps(NOW)) == 0
#    end = datetime.datetime(2011, 4, 1).date()
#    dte = NOW + one_day
#    while dte != end:
#        assert len(get_scheduled_reps(dte)) == 0
#        dte += one_day
#    assert len(get_scheduled_reps(dte)) == 1
#
#    s = man.new_report(str(s.most_recent.key()), now=dte, testing=True)
#
#    print '\n\n\n\n\n%s\n%s\n\n\n\n\n' % (date_magic.get_next_day('quarterly', dte), s.next_sched_date)
#    print get_scheduled_reps(dte)
#    assert len(get_scheduled_reps(dte)) == 0
#    end = datetime.datetime(2011, 7, 1).date()
#    dte = dte + one_day
#    while dte != end:
#        assert len(get_scheduled_reps(dte)) == 0
#        dte += one_day
#    assert len(get_scheduled_reps(dte)) == 1
#
#    #set next sched date to be in the past
#    s.next_sched_date = NOW - one_day 
#    s.put()
#    return

####################
# Test transitions #
####################

def daily_to_weekly_mptest():
    pass

def daily_to_montly_mptest():
    pass

def daily_to_quarterly_mptest():
    pass

def daily_to_none_mptest():
    pass

def weekly_to_daily_mptest():
    pass

def weekly_to_montly_mptest():
    pass

def weekly_to_quarterly_mptest():
    pass

def weekly_to_none_mptest():
    pass

def montly_to_daily_mptest():
    pass

def montly_to_weekly_mptest():
    pass

def montly_to_quarterly_mptest():
    pass

def montly_to_none_mptest():
    pass

def quarterly_to_daily_mptest():
    pass

def quarterly_to_weekly_mptest():
    pass

def quarterly_to_montly_mptest():
    pass

def quarterly_to_none_mptest():
    pass

