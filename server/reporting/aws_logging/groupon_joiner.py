import bisect
import csv
import os
import sys
import time
import traceback
import logging

from datetime import datetime
from optparse import OptionParser

# add mopub root to path, for run_jobflow.sh
sys.path.append(os.getcwd()+'/../../')

# for ubuntu EC2
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/mopub/server/reporting')
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')


from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()


import utils
from parse_utils import parse_logline

from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub
from account.query_managers import AccountQueryManager, UserQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager
from userstore.query_managers import ClickEventManager


    

STATS_DICT = {}  # key=k:adunit_id:creative_id:date_hour, value=StatsModel()
        
open_udid_set = []
clk_udid_set = []

clk_udid_time = {}
clk_time_cid = {}

def process_clk_line(line):
    logline_dict = parse_logline(line, False)

    if logline_dict:
        param_dict = logline_dict.get('params')
        aid = param_dict.get('id')
        cid = param_dict.get('cid')
        udid = param_dict.get('udid')
        clk_udid_set.append(udid)
        
        log_date = logline_dict.get('date')
        log_time = logline_dict.get('time')
        date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')
        
        if udid not in clk_udid_time:
            clk_udid_time[udid] = []
        clk_udid_time[udid] += [date_hour]
        clk_time_cid[date_hour] = (aid, cid)
    
    for udid in clk_udid_time.keys():
        clk_udid_time[udid].sort()
        
    


open_udid_time = {}

def process_open_line(line):
    logline_dict = parse_logline(line, False)

    if logline_dict:
        param_dict = logline_dict.get('params')
        udid = param_dict.get('udid')
        open_udid_set.append(udid)
        
        log_date = logline_dict.get('date')
        log_time = logline_dict.get('time')
        date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')
        
        if udid not in open_udid_time or date_hour < open_udid_time[udid]:
            open_udid_time[udid] = date_hour
    
    
output_table = {}

def do_the_fucking_join():
    for udid, open_time in open_udid_time.iteritems():
        if udid not in clk_udid_time: continue
        clk_times = clk_udid_time[udid]
        index = bisect.bisect(clk_times, open_time)-1
        if index < 0: continue
        clk_time = clk_times[index]
        (aid, cid) = clk_time_cid[clk_time]
        if (aid,cid,open_time) not in output_table:
            output_table[(aid,cid,open_time)] = []
        output_table[(aid,cid,open_time)] += [udid]
 
 
                                
def process_files(clk_file, open_file):
    with open(clk_file) as f:
        for line in f:
            parts = line.split('\t', 1)
            # if len(parts) != 2: continue
            process_clk_line(parts[0])
            
    with open(open_file) as f:
        for line in f:
            parts = line.split('\t', 1)
            # if len(parts) != 2: continue
            process_open_line(parts[0])
    

def update_clk_line_userstore(ce_manager, line):
    logline_dict = parse_logline(line, False)

    if logline_dict:
        param_dict = logline_dict.get('params')
        aid = param_dict.get('id')
        cid = param_dict.get('cid')
        udid = param_dict.get('udid')
        
        log_date = logline_dict.get('date')
        log_time = logline_dict.get('time')
        date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')

        success = False
        while not success:
            try:
                ce_manager.log_click_event(udid, '352683833', date_hour, aid, cid)
                print "%s %s %s %s" % (udid, date_hour, aid, cid)
                success = True
            except:
                print 'retry...'
                time.sleep(10)
            

    
def update_clk_in_userstore(clk_file):
    ce_manager = ClickEventManager()
    
    with open(clk_file) as f:
        for line in f:
            parts = line.split('\t', 1)
            # if len(parts) != 2: continue
            update_clk_line_userstore(ce_manager, parts[0])
    

def update_datastore():
    user = UserQueryManager.get_by_email('joel@grindr.com')
    account = AccountQueryManager.get_current_account(user=user)
    
    for (aid, cid, open_time), uniq_users in output_table.iteritems():
        num_conversions = len(uniq_users)
        key = StatsModel.get_key_name(publisher=aid, advertiser=cid, date_hour=open_time)

        if not key in STATS_DICT:
            STATS_DICT[key] = StatsModel(publisher=aid,
                                         advertiser=cid,
                                         date_hour=open_time)
        STATS_DICT[key].conversion_count += num_conversions
    
    StatsModelQueryManager(account=account).put_stats(STATS_DICT.values())
    
    for stat in STATS_DICT.values():
        print stat.key().name(), stat.conversion_count
    
            
def auth_func():
    return "olp@mopub.com", "N47935N47935"
    
                    
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-c', '--click_file', dest='click_file')
    parser.add_option('-o', '--open_file', dest='open_file')
    
    (options, args) = parser.parse_args()
    
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)
            
    update_clk_in_userstore(options.click_file)

    # process_files(options.click_file, options.open_file)
    # do_the_fucking_join()
    # 
    #    
    # print
    # print 'clk udid', len(clk_udid_set)
    # print 'open udid', len(open_udid_set)
    # print 'clk udid set', len(set(clk_udid_set))
    # print 'open udid set', len(set(open_udid_set))
    # intersection = set(clk_udid_set) & set(open_udid_set)
    # print len(intersection)
    # 
    # update_datastore()
   
    elapsed = time.time() - start
    print "took %i minutes and %i seconds" % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
    
    
