import os
import sys
import time
import traceback

from datetime import datetime
from optparse import OptionParser


# add mopub root to path
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


from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

import utils
from publisher.models import Site
from reporting.models import StatsModel, Pacific_tzinfo


# maximum number of objects per batch put
LIMIT = 50

account_cache = {}
stats_model_cache = {}
counts_cache = {}


def update_counts(array1, array2):
    return map(sum, zip(array1, array2))
    

def update_models():             
    def txn(account_stats, stats_key_names):
        put_list = []

        for s in stats_key_names:
            try:
                stats_key_name = s.split('|')[0]
                stats_model = StatsModel.get_by_key_name(stats_key_name, parent=account_stats)
                if stats_model:
                    stats_model.user_count, stats_model.request_user_count, stats_model.impression_user_count, stats_model.click_user_count = counts_cache[s]
                    put_list.append(stats_model)
                else:
                    print 'stats_model should not be None: %s'%stats_key_name
            except Exception, e:
                # traceback.print_exc()
                print 'exception on %s -> %s' % (stats_key_name, e)
                continue

        
        print 'uniq user: putting %i models...' % (len(put_list))
        put_keys = db.put(put_list)
        put_fail_count = len(put_list) - len(put_keys)
        if put_fail_count > 0:
            print 'uniq user: %i models failed on batch put' %put_fail_count
    
    
    for account_stats, stats_key_names in stats_model_cache.iteritems():   
        txn_fail_count = 0
        stats_key_names = list(stats_key_names)
        print 'uniq user: putting models for account', account_stats.account.key().name() 
        while stats_key_names:
            try:
                db.run_in_transaction(txn, account_stats, stats_key_names[:LIMIT])
            except:
                traceback.print_exc()
                txn_fail_count += 1
                print 'failed %i times' % (txn_fail_count)
                if txn_fail_count <= 2:
                    print 'sleeping for 60 seconds...'
                    time.sleep(60) # sleep for a minute and try again
                    continue
                else:
                    print 'phuket...moving on to next account'
                    break # if failed 3 times, break the while loop
            stats_key_names = stats_key_names[LIMIT:]
            txn_fail_count = 0
            
                    
    
def parse_file(input_file):
    global account_cache
    global stats_model_cache
    global counts_cache
    
    with open(input_file, 'r') as f:
        for line in f:
            try:
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
                        # stats_model_cache format: {account_stats: [stats_key_name|account]}
                        if account_stats in stats_model_cache:
                            stats_model_cache[account_stats].add(stats_key_name+'|'+account)
                        else:
                            stats_model_cache[account_stats] = set([stats_key_name+'|'+account])
               
                    
                # initialize uniq_user_counts array
                if stats_key_name+'|'+account in counts_cache:
                    uniq_user_counts = counts_cache[stats_key_name+'|'+account]
                else: 
                    uniq_user_counts = [0, 0, 0, 0] # [user_count, request_user_count, impression_user_count, click_user_count]
        
                if handler == '':
                    uniq_user_counts = update_counts(uniq_user_counts, [uniq_count, 0, 0, 0])                
                elif handler == utils.AD:
                    uniq_user_counts = update_counts(uniq_user_counts, [0, uniq_count, 0, 0])
                elif handler == utils.IMP:
                    uniq_user_counts = update_counts(uniq_user_counts, [0, 0, uniq_count, 0])
                elif handler == utils.CLK:
                    uniq_user_counts = update_counts(uniq_user_counts, [0, 0, 0, uniq_count])
                elif handler == utils.REQ:
                    uniq_user_counts = update_counts(uniq_user_counts, [0, uniq_count, 0, 0])
                counts_cache[stats_key_name+'|'+account] = uniq_user_counts
            except Exception, e:
                # traceback.print_exc()
                print 'EXCEPTION on line %s -> %s' %(line, e)
                continue
                

def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)
    
    print 'uniq user: processing %s for GAE datastore...' %options.input_file
    parse_file(options.input_file)
    update_models()
   
    elapsed = time.time() - start
    print 'uniq user: updating GAE datastore took %i minutes and %i seconds' % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
