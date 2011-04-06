import os
import sys
import time
import traceback

from datetime import datetime
from optparse import OptionParser

sys.path.append("/home/ubuntu/mopub/server")
sys.path.append("/home/ubuntu/mopub/server/reporting")
sys.path.append("/home/ubuntu/google_appengine")
sys.path.append("/home/ubuntu/google_appengine/lib/django")
sys.path.append("/home/ubuntu/google_appengine/lib/webob")
sys.path.append("/home/ubuntu/google_appengine/lib/yaml/lib")
sys.path.append("/home/ubuntu/google_appengine/lib/fancy_urllib")

from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

# for run_jobflow.sh
sys.path.append(os.getcwd()+'/../../')

import utils
from log_parser import AD, IMP, CLK, OPEN, REQ
from publisher.models import Site
from reporting.models import StatsModel, Pacific_tzinfo


# maximum number of objects per batch put
LIMIT = 400

account_cache = {}
stats_model_cache = {}
counts_cache = {}


def update_counts(current, delta):
    return map(sum, zip(current, delta))
    

def update_models():             
    def txn(account_stats, stats_key_names):
        put_list = []
    
        stats_models = StatsModel.get_by_key_name(stats_key_names, parent=account_stats)
        for stats_key_name, stats_model in zip(stats_key_names, stats_models):
            if stats_model:
                stats_model.user_count, stats_model.request_user_count, stats_model.impression_user_count, stats_model.click_user_count = counts_cache[stats_key_name]
                put_list.append(stats_model)
            else:
                print 'stats_model should not be None: %s'%stats_key_name
        
        print "uniq user: putting %i models..." % (len(put_list))
        put_keys = db.put(put_list)
        fail_count = len(put_list) - len(put_keys)
        if fail_count > 0:
            print "uniq user: %i models failed on batch put" %fail_count
    
    
    for account_stats, stats_key_names in stats_model_cache.iteritems():
        print
        print "uniq user: putting models for account %s ..." % (repr(account_stats.key()))
        while stats_key_names:
            db.run_in_transaction(txn, account_stats, stats_key_names[:LIMIT])
            stats_key_names = stats_key_names[LIMIT:]
            
                    
    
def parse_file(input_file):
    global account_cache
    global stats_model_cache
    global counts_cache
    
    with open(input_file, 'r') as f:
        for line in f:
            if '\\' in line:
                line = line.replace(r'\'', '')
            mr_key, uniq_count = line.split('\t', 1)

            uniq_count = int(uniq_count)
            parts = mr_key.split(':')
            if len(parts) != 6: continue # only interested in [k:handler:account:pub_id:adv_id:date_hour]
            handler = parts[1]
            account = parts[2]
            pub_key = parts[3]
            adv_key = parts[4]
            time_str = parts[5]
            year = int('20'+time_str[:2])
            month = int(time_str[2:4])
            day = int(time_str[4:6])

            # get key_name of stats_model
            if len(time_str) == 8:  # resolution to hour
                hour = int(time_str[6:8])
                date_hour = datetime(year, month, day, hour, tzinfo=Pacific_tzinfo())
                stats_key_name = StatsModel.get_key_name(publisher=pub_key, 
                                                         advertiser=adv_key,
                                                         date_hour=date_hour,
                                                         account=account)
            else:   # resolution to day
                date = datetime(year, month, day)
                stats_key_name = StatsModel.get_key_name(publisher=pub_key, 
                                                         advertiser=adv_key,
                                                         date=date,
                                                         account=account)
            
            account_stats_realtime_kn = StatsModel.get_key_name(account=account)
            account_stats_offline_kn = StatsModel.get_key_name(account=account, offline=True)
            account_stats_kns = [account_stats_realtime_kn, account_stats_offline_kn]
            
            for account_stats_kn in account_stats_kns:
                # try to retrieve account_stats from cache
                if account_stats_kn in account_cache:
                    account_stats = account_cache[account_stats_kn]
                else:
                    account_stats = StatsModel.get_by_key_name(account_stats_kn)
                    if account_stats:
                        account_cache[account_stats_kn] = account_stats
            
                if account_stats:
                    # stats_model_cache format: {account_stats: [stats_key_name]}
                    if account_stats in stats_model_cache:
                        stats_model_cache[account_stats].append(stats_key_name)
                    else:
                        stats_model_cache[account_stats] = [stats_key_name]
               
                    
            # initialize uniq_user_counts array
            if stats_key_name in counts_cache:
                uniq_user_counts = counts_cache[stats_key_name]
            else: 
                uniq_user_counts = [0, 0, 0, 0] # [user_count, request_user_count, impression_user_count, click_user_count]
        
            if handler == '':
                uniq_user_counts = update_counts(uniq_user_counts, [uniq_count, 0, 0, 0])                
            if handler == AD:
                uniq_user_counts = update_counts(uniq_user_counts, [0, uniq_count, 0, 0])
            elif handler == IMP:
                uniq_user_counts = update_counts(uniq_user_counts, [0, 0, uniq_count, 0])
            elif handler == CLK:
                uniq_user_counts = update_counts(uniq_user_counts, [0, 0, 0, uniq_count])
            elif handler == REQ:
                uniq_user_counts = update_counts(uniq_user_counts, [0, uniq_count, 0, 0])
            counts_cache[stats_key_name] = uniq_user_counts
                
                

def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)
    
    print "uniq user: processing %s for GAE datastore..." %options.input_file
    parse_file(options.input_file)
    update_models()
   
    elapsed = time.time() - start
    print "uniq user: updating GAE datastore took %i minutes and %i seconds" % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
