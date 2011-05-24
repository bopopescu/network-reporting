import os, sys
import pprint

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
    STATS_FOR_DAYS = 2
else:
    APP_CT = 2
    AU_CT = 2 # per app
    CAMP_CT = 3
    CRTV_CT = 2 #per campaign
    STATS_FOR_DAYS = 5 
#hours per day
HPD = 24
STATS = ('request_count', 'impression_count', 'click_count', 'conversion_count', 'revenue')

if QUICK:
    CAMP_TARGETING = (((True,True), (False, True)),)
else:
    CAMP_TARGETING = (((True, True, False), (True, False, False)), ((False, True, True), (False, False, True))) 

# len(CAMP_TARGETING) = APP_CT 
# len(Each entry in CAMP_TARGETING) = AU_CT 
# len(each entry in each entry of CAMP_TARGETING) = CAMP_CT 
# Basically, for each adunit in each app, which campaigns should target it 

class TestReports():

    #Generate a bunch of psuedo-random (deterministically, same every time) stat values
    # and make the stats models for them.  What fun
    def gen_stats(self):
        self.gen_nums()
        stats = []
        for au in self.adunits:
            au_key = au.key()
            for adgroup in self.adgroups:
                if au_key in adgroup.site_keys:
                    for crtv in adgroup.creatives:
                        c_key = crtv.key()
                        for day in range(STATS_FOR_DAYS):
                            for hour in range(HPD):
                                dte = self.dte + datetime.timedelta(days=day, hours=hour)
                                model = StatsModel(publisher=au, advertiser=crtv, date_hour=dte)
                                for stat in STATS:
                                    setattr(model, stat, self.nums[au_key][c_key][day][hour][stat])
                                stats.append(model)
        self.smqm.put_stats(stats)



    #Generate all the numbers for the stats objects we're gonna make.  AWESSOOMMEEE
    #Seed the random number generator with the same seed so the sequenece is the same every time
    def gen_nums(self):
        random.seed(RANDOM_SEED)
        self.nums = {}
        #Best nested set of for loops ever
        for au in self.adunits:
            au_key = au.key()
            self.nums[au_key] = {}
            for adgroup in self.adgroups:
                if au_key in adgroup.site_keys:
                    for crtv in adgroup.creatives:
                        c_key = crtv.key()
                        self.nums[au_key][c_key] = {} 
                        for day in range(STATS_FOR_DAYS):
                            self.nums[au_key][c_key][day] = {} 
                            for hour in range(HPD):
                                self.nums[au_key][c_key][day][hour] = {}
                                last_int = 400 
                                for stat in STATS:
                                    if stat == 'revenue':
                                        last_int = 40
                                    rand_num = random.randint(1,last_int)
                                    if stat == 'revenue':
                                        rand_num = float(rand_num)
                                    self.nums[au_key][c_key][day][hour][stat] = rand_num
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

def simple_mptest():
    return
    rep1 = Report(d1='app', start=DATE, end=DATE+datetime.timedelta(days=1), account=tester.account)
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

NOW = datetime.datetime(2011, 1, 1).date()
one_day = datetime.timedelta(days=1)

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

