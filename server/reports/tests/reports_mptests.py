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
from reports.query_managers import ReportQueryManager
from reporting.aws_logging.stats_updater import update_model, put_models
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

#allows me to seed the random number generator so every time
#we get the same sequence of random numbers
RANDOM_SEED = 'r4nd0ms33d'

APP_NAME = "Test App %d"
AU_NAME = "Test Adunit %d for App %d"
CAMP_NAME = "Test Camp %d"
AG_NAME = "Adgroup for Camp %d"
CRTV_NAME = "Test Creative %d For Campaign %d"
#FOR ALL YOU CARE THIS IS THE BEGINNING OF TIME
DATE = datetime.date(2011,1,1)
#Set this to true if you are impatient
QUICK = True
if QUICK:
    APP_CT = 1
    AU_CT = 2 
    CAMP_CT = 2 
    CRTV_CT = 1 
    STATS_FOR_DAYS = 1
else:
    APP_CT = 2
    AU_CT = 2 # per app
    CAMP_CT = 3
    CRTV_CT = 2 #per campaign
    STATS_FOR_DAYS = 5 

IOS = 'iOS'
DRD = 'Android'
HTC = 'HTC'
EVO = 'Evo'
MAG = 'Magic'
APL = 'Apple'
I3G = 'iPhone_3G'
I4 = 'iPhone_4'
A12 = '1.2'
A16 = '1.6'
I11 = '1.1'
I34 = '3.4'

DIMS = [None, 'app', 'adunit', 'campaign', 'creative', 'day', 'hour', 'country', 'marketing', 'brand', 'os', 'os_ver']

INVALID_PAIRS = [('adunit', 'app'), ('creative', 'campaign'), ('hour', 'day'), ('os_ver', 'os'), ('marketing', 'brand')]

BRANDS = [HTC, APL]
MARS = [EVO, MAG, I4, I3G]
#ding Dzun dun dun dun dunn dun DZUN dzun dun 
OSS = [DRD, IOS]
OSVERS = [A12, A16, I11, I34]
        

#Device/OS dicts
BRAND_MAR = { HTC : [EVO, MAG], 
              APL : [I4, I3G]}
BRAND_OS = { HTC : [DRD], 
             APL: [IOS] }
BRAND_OSVER = { HTC : [A12, A16], 
                APL : [I11, I34]}

MAR_OS  = { EVO: [DRD], 
            MAG : [DRD], 
            I4: [IOS], 
            I3G : [IOS]}
MAR_OSVER = { EVO: [A12, A16], 
              MAG: [A12], 
              I3G: [I11, I34], 
              I4: [I34]}
MAR_BRAND = { EVO : [HTC], 
              MAG: [HTC], 
              I4 : [APL], 
              I3G: [APL]}

OS_BRAND = { DRD : [HTC], 
             IOS : [APL]}
OS_MAR = { IOS: [I4, I3G], 
           DRD: [EVO, MAG]}
OS_OSVER = { IOS: [I11, I34], 
             DRD: [A12, A16]}

OSVER_BRAND = {I11: [APL], 
               I34: [APL], 
               A12: [HTC], 
               A16: [HTC]}
OSVER_MAR = {I11: [I3G], 
             I34: [I3G, I4], 
             A12: [MAG, EVO], 
             A16: [EVO]}
OSVER_OS = {I11: [IOS], 
            I34: [IOS], 
            A12: [DRD], 
            A16: [DRD]}

FAKE_WURFL = [BRAND_MAR, BRAND_OS, BRAND_OSVER, MAR_OS, MAR_OSVER, MAR_BRAND, OS_BRAND, OS_MAR, OS_OSVER, OSVER_BRAND, OSVER_MAR, OSVER_OS]


#countries
COUNTRIES = ['US', 'CA',]
SPEC_COUNTRIES = [('US', 'United States'), ('CA', "Canadia")]

#hours per day
HPD = 4
STATS = ('request_count', 'impression_count', 'click_count', 'conversion_count', 'revenue')

if QUICK:
    CAMP_TARGETING = (((True,True), (False, True)),)
else:
    CAMP_TARGETING = (((True, True, False), (True, False, False)), ((False, True, True), (False, False, True))) 

# len(CAMP_TARGETING) = APP_CT 
# len(Each entry in CAMP_TARGETING) = AU_CT 
# len(each entry in each entry of CAMP_TARGETING) = CAMP_CT 
# Basically, for each adunit in each app, which campaigns should target it 

DIR = os.path.dirname(__file__)
class TestReports():
    
    #Generate a bunch of psuedo-random (deterministically, same every time) stat values
    # and make the stats models for them.  What fun
    def gen_stats(self):
        try:
            print "attemping to open pickle"
            f = open(DIR + '/report_data.pkl')
            self.nums = pickle.load(f)
        except:
            print "failed to open pickle"
            f = open(DIR + '/report_data.pkl', 'w')
            self.gen_nums()
            pickle.dump(self.nums, f)
        stats = []
        for au in self.adunits:
            au_key = au.key()
            for adgroup in self.adgroups:
                if au_key in adgroup.site_keys:
                    for crtv in adgroup.creatives:
                        c_key = crtv.key()
                        for brand in BRANDS:
                            for mar in MARS:
                                if mar not in BRAND_MAR[brand]:
                                    continue
                                for os in OSS:
                                    if (os not in BRAND_OS[brand]) or (os not in MAR_OS[mar]):
                                        continue
                                    for osver in OSVERS:
                                        if (osver not in BRAND_OSVER[brand]) or (osver not in MAR_OSVER[mar]) or (osver not in OS_OSVER[os]):
                                            continue
                                        for country in COUNTRIES:
                                            for day in range(STATS_FOR_DAYS):
                                                for hour in range(HPD):
                                                    dte = self.dte + datetime.timedelta(days=day, hours=hour)
                                                    counts = [None, None, None, None] 
                                                    for k,v in self.nums[au_key][c_key][brand][mar][os][osver][country][day][hour].iteritems():
                                                        if k == 'request_count':
                                                            counts[0] = v
                                                        elif k == 'impression_count':
                                                            counts[1] = v
                                                        elif k == 'click_count':
                                                            counts[2] = v
                                                        elif k == 'conversion_count':
                                                            counts[3] = v
                                                        else:
                                                            continue
                                                    update_model(adunit_key = str(au_key),
                                                                 creative_key = str(c_key),
                                                                 country_code = country,
                                                                 brand_name = brand,
                                                                 marketing_name = mar,
                                                                 device_os = os,
                                                                 device_os_version = osver,
                                                                 date_hour = dte,
                                                                 counts = counts
                                                                 )
    #need 2 letter country code (country), brand_name, marketing_name, device_os, device_os_version
    #                                                model = StatsModel(publisher=au, advertiser=crtv, country=country, brand_name = brand, marketing_name = mar, device_os = os, device_os_version = osver, date_hour=dte)
    #                                                for stat in STATS:
    #                                                    setattr(model, stat, self.nums[au_key][c_key][brand][mar][os][osver][country][day][hour][stat])
    #                                                stats.append(model)
        put_models()
    #    self.smqm.put_stats(stats)



    #Generate all the numbers for the stats objects we're gonna make.  AWESSOOMMEEE
    #Seed the random number generator with the same seed so the sequenece is the same every time
    #COBB AINT GOT SHIT ON ME WHAT NOW
    #3 Levels deep is for bitches
    def gen_nums(self):
        random.seed(RANDOM_SEED)
        self.nums = {}
        #Best nested set of for loops ever
        #see comment farther down
        for au in self.adunits:
            au_key = au.key()
            self.nums[au_key] = {}
            for adgroup in self.adgroups:
                if au_key in adgroup.site_keys:
                    for crtv in adgroup.creatives:
                        c_key = crtv.key()
                        self.nums[au_key][c_key] = {} 
                        #i just added device/os/country stuff and this shit just got even fucking better.  So epic
                        #Tom complained and I told him to cry abou it
                        for brand in BRANDS:
                            self.nums[au_key][c_key][brand] = {}
                            for mar in MARS:
                                if mar not in BRAND_MAR[brand]:
                                    #invalid marketing name for this brand
                                    continue
                                self.nums[au_key][c_key][brand][mar] = {}
                                for os in OSS:
                                    if (os not in BRAND_OS[brand]) or (os not in MAR_OS[mar]):
                                        #invalid os for this brand or marketing name
                                        continue
                                    self.nums[au_key][c_key][brand][mar][os] = {}
                                    for osver in OSVERS:
                                        if (osver not in BRAND_OSVER[brand]) or (osver not in MAR_OSVER[mar]) or (osver not in OS_OSVER[os]):
                                            #invalid os version for brand, marketing name, or os
                                            continue
                                        self.nums[au_key][c_key][brand][mar][os][osver] = {}
                                        for country in COUNTRIES:
                                            self.nums[au_key][c_key][brand][mar][os][osver][country] = {}

                                            for day in range(STATS_FOR_DAYS):
                                                self.nums[au_key][c_key][brand][mar][os][osver][country][day] = {} 
                                                for hour in range(HPD):
                                                    self.nums[au_key][c_key][brand][mar][os][osver][country][day][hour] = {}
                                                    last_int = 400 
                                                    for stat in STATS:
                                                        if stat == 'revenue':
                                                            last_int = 40
                                                        rand_num = random.randint(1,last_int)
                                                        if stat == 'revenue':
                                                            rand_num = float(rand_num)
                                                        self.nums[au_key][c_key][brand][mar][os][osver][country][day][hour][stat] = rand_num
                                                        last_int = rand_num

                     
    def tearDown(self):
        self.testbed.deactivate()

    def setUp(self):
        self.dte = datetime.datetime(2011,1,1,0)
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        self.account = Account()
        self.account.put()

        self.smqm = StatsModelQueryManager(self.account)

        self.apps = []
        self.adunits = []

        self.campaigns = []
        self.adgroups = []
        self.creatives = []
        temp_keys = []
        for i in range(CAMP_CT):
            temp_keys.append([])

        for i in range(APP_CT):
            #create apps
            self.apps.append(App(account=self.account, name=APP_NAME % i))
        for app_num,app in enumerate(self.apps):
            #put apps 
            app.put()
            for au in range(AU_CT):
                #create + put adunits for apps
                adunit = AdUnit(account=self.account, app_key=app, name=AU_NAME % (au, app_num))
                adunit.put()
                #Iterate over targeting info
                for camp, bool in enumerate(CAMP_TARGETING[app_num][au]):
                    #if we should target this au
                    if bool:
                        #store this au for that campaign
                        temp_keys[camp].append(adunit.key())
                #store adunits
                self.adunits.append(adunit)
        for targets, c_id in zip(temp_keys, range(CAMP_CT)):
            #gen + put camp
            camp = Campaign(name=CAMP_NAME % c_id, account = self.account)
            camp.put()
            #add to list
            self.campaigns.append(camp)
            #gen + put adgroup
            adgroup = AdGroup(account=self.account,
                              campaign = camp,
                              site_keys = targets,
                              bid_strategy = 'cpc')
            adgroup.put()
            #add to list
            self.adgroups.append(adgroup)
            for crtv_id in range(CRTV_CT):
                crtv = Creative(account=self.account,
                                name = CRTV_NAME % (crtv_id, c_id),
                                ad_group = adgroup.key(),
                                trackign_url = "test-tracking-url",
                                cpc=.03)
                crtv.put()
                #add to list
                self.creatives.append(crtv)
        self.gen_stats()


# app, adunit, campaign, creative, priority, month, week, day, hour, country

#priority supercedes campaign and creative

# -- What???
# targeting, custom targeting

tester = TestReports()
tester.setUp()

NOW = datetime.datetime(2011, 1, 1).date()
one_day = datetime.timedelta(days=1)

def make_get_data(d1, end, start, next_sched_date, d2=None, d3=None):
    days = (end-start).days
    s = ScheduledReport(d1=d1, d2=d2, d3=d3, end = end, days = days, next_sched_date = next_sched_date, account=tester.account)
    s.put()
    r = Report(start = start, end = end, account = tester.account, schedule = s)
    r.put()
    return r.gen_data(wurfl_dicts = FAKE_WURFL, countries = SPEC_COUNTRIES)
    

def verify_data(data):
    #Returns a list of numbers if verified, False otherwise
    req_tot = imp_tot = clk_tot = conv_tot = 0
    for k,v in data.iteritems():
        stats = v['stats']
        req = stats.request_count
        imp = stats.impression_count
        clk = stats.click_count
        conv = stats.conversion_count
        req_tot += req
        imp_tot += imp
        clk_tot += clk
        conv_tot += conv
        if v.has_key('sub-stats'):
            total = verify_data(v['sub-stats'])
            t_req, t_imp, t_clk, t_conv = total
            if req != 0 and t_req != 0 and req != t_req:
                return False
            if imp != t_imp:
                return False
            if clk != t_clk:
                return False
            if conv != t_conv:
                return False
    return [req_tot, imp_tot, clk_tot, conv_tot]
                
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
            assert verify_data(make_get_data(d1, end, start, sched_past, d2=d2, d3=d3))


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
            
def simple_mptest():
    end = DATE + one_day
    start = DATE
    days = (end - start).days
    dt = datetime.timedelta(days=days)
    sched_past = NOW - one_day
    d1 = make_get_data('app', end, start, sched_past)
#    pprint.pprint(d1)
    print "\n\n"
    d2 = make_get_data('campaign', end, start, sched_past)
#    pprint.pprint(d2)
    print "\n\n"
    d3 = make_get_data('campaign', end, start, sched_past, d2='os')
#    pprint.pprint(d3)
    assert True
    return
    rep2 = Report(d1='campaign', d2='app', d3='day', start=DATE, end=DATE+datetime.timedelta(days=1), account=tester.account)
    rep3 = Report(d1='month', d2='week', d3='campaign', start=DATE, end=DATE+datetime.timedelta(days=1), account=tester.account)
    data1 = rep1.gen_data()
    data2 = rep2.gen_data()
    data3 = rep3.gen_data()
    assert True

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

man = ReportQueryManager(account=tester.account)

def none_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='none_test', sched_interval = 'none', testing = True)
    assert len(get_scheduled_reps(NOW)) == 1
    assert len(get_scheduled_reps(NOW + one_day)) == 0
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def daily_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='daily_test', sched_interval = 'daily', testing = True)
    assert len(get_scheduled_reps(NOW)) == 0 
    assert len(get_scheduled_reps(NOW + one_day)) == 1
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def double_daily_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='dub_daily_test', sched_interval = 'daily', testing = True)
    def assrt_daily(dte):
        assert len(get_scheduled_reps(dte)) == 0 
        assert len(get_scheduled_reps(dte + one_day)) == 1

    assrt_daily(NOW)
    tom = NOW + one_day
    s = man.new_report(str(s.most_recent.key()), now=tom, testing=True)
    assrt_daily(tom)

    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def weekly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='weekly_test', sched_interval = 'weekly', testing = True)
    assert len(get_scheduled_reps(NOW)) == 0 
    dte = NOW + one_day
    for i in range(7):
        if dte.weekday() == 0:
            assert len(get_scheduled_reps(dte)) == 1
            break
        else:
            assert len(get_scheduled_reps(dte)) == 0
        dte += one_day
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return 
    
def double_weekly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='dub_weekly_test', sched_interval = 'weekly', testing = True)
    def assrt_weekly(dte):
        assert len(get_scheduled_reps(dte)) == 0 
        dte = dte + one_day
        for i in range(7):
            if dte.weekday() == 0:
                assert len(get_scheduled_reps(dte)) == 1
                return dte
            else:
                assert len(get_scheduled_reps(dte)) == 0
            dte += one_day

    next_day = assrt_weekly(NOW)
    s = man.new_report(str(s.most_recent.key()), now=next_day, testing=True)
    assrt_weekly(next_day)
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def monthly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='monthly_test', sched_interval = 'monthly', testing = True)
    assert len(get_scheduled_reps(NOW)) == 0
    dte = NOW + one_day
    while dte.day != 1:
        assert len(get_scheduled_reps(dte)) == 0
        dte += one_day
    assert len(get_scheduled_reps(dte)) == 1
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def double_monthly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='dub_monthly_test', sched_interval = 'monthly', testing = True)
    def assrt_monthly(dte):
        assert len(get_scheduled_reps(dte)) == 0
        dte = dte + one_day
        while dte.day != 1:
            assert len(get_scheduled_reps(dte)) == 0
            dte += one_day
        assert len(get_scheduled_reps(dte)) == 1
        return dte
    next_day = assrt_monthly(NOW)
    s = man.new_report(str(s.most_recent.key()), now=next_day, testing=True)
    assrt_monthly(next_day)
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def quarterly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='quarterly_test', sched_interval = 'quarterly', testing = True)
    assert len(get_scheduled_reps(NOW)) == 0
    end = datetime.datetime(2011, 4, 1).date()
    dte = NOW + one_day
    while dte != end:
        assert len(get_scheduled_reps(dte)) == 0
        dte += one_day
    assert len(get_scheduled_reps(dte)) == 1
    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

def double_quarterly_mptest():
    s = man.add_report('app', None, None, NOW, 4, name='dub_quarterly_test', sched_interval = 'quarterly', testing = True)
    assert len(get_scheduled_reps(NOW)) == 0
    end = datetime.datetime(2011, 4, 1).date()
    dte = NOW + one_day
    while dte != end:
        assert len(get_scheduled_reps(dte)) == 0
        dte += one_day
    assert len(get_scheduled_reps(dte)) == 1

    s = man.new_report(str(s.most_recent.key()), now=dte, testing=True)

    print '\n\n\n\n\n%s\n%s\n\n\n\n\n' % (date_magic.get_next_day('quarterly', dte), s.next_sched_date)
    print get_scheduled_reps(dte)
    assert len(get_scheduled_reps(dte)) == 0
    end = datetime.datetime(2011, 7, 1).date()
    dte = dte + one_day
    while dte != end:
        assert len(get_scheduled_reps(dte)) == 0
        dte += one_day
    assert len(get_scheduled_reps(dte)) == 1

    #set next sched date to be in the past
    s.next_sched_date = NOW - one_day 
    s.put()
    return

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

