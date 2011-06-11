import os
import sys
import time
import traceback
import logging
import multiprocessing

from datetime import datetime
from multiprocessing import Pool
from multiprocessing.pool import ThreadPool
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

from google.appengine.ext import db


import utils
from publisher.models import Site
from reporting.models import StatsModel, Pacific_tzinfo


# maximum number of objects per batch put
LIMIT = 50

account_cache = {}  # account_cache[account_stats_kn] = account_stats_SM
stats_model_cache = {}  # {account_stats_SM: set([stats_key_name|account])}
counts_cache = {}


def update_counts(array1, array2):
    return map(sum, zip(array1, array2))


def txn(account_name, account_stats, stats_key_names):
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
    
    # print 'uniq user: putting %i models...' % (len(put_list))
    print ('%s: %i models' % ((account_name or 'None').rjust(30), len(put_list)))
    put_keys = db.put(put_list)
    put_fail_count = len(put_list) - len(put_keys)
    if put_fail_count > 0:
        print 'uniq user: %i models failed on batch put' %put_fail_count    


def update_models_by_account(pair_arg):
    try:
        account_stats, stats_key_names = pair_arg
        txn_fail_count = 0
        stats_key_names = list(stats_key_names)
        account_name = account_stats.account.key().name()
        print 'uniq user: putting models for account %s' %(account_name)
        while stats_key_names:
            try:
                db.run_in_transaction(txn, account_name, account_stats, stats_key_names[:LIMIT])
            except:
                traceback.print_exc()
                txn_fail_count += 1
                print 'uniq user: failed %i times' % (txn_fail_count)
                if txn_fail_count <= 2:
                    print 'uniq user: sleeping for 60 seconds...'
                    time.sleep(60) # sleep for a minute and try again
                    continue
                else:
                    print 'uniq user: phuket...moving on to next account'
                    break # if failed 3 times, break the while loop
            stats_key_names = stats_key_names[LIMIT:]
            txn_fail_count = 0
        return 'uniq user: success: account %s' %(account_stats.account.key().name())
    except KeyboardInterrupt:
        print 'uniq user: child process received control-c'
        pass
    except:
        traceback.print_exc()
        return 'uniq user: failed: account %s' %(account_stats.account.key().name())
        

def update_models(pool):
    async_results = pool.map_async(update_models_by_account, stats_model_cache.items())
    results = async_results.get(0xFFFF) # set maximum timeout (seconds) to return result when it arrives

    # print status message from each process
    print
    print
    for i in results:
        print i
    print
    print
                    

def single_thread_update_models():             
    for account_stats, stats_key_names in stats_model_cache.iteritems():   
        account_name = account_stats.account.key().name()
        stats_key_names = list(stats_key_names)
        print "uniq user: putting models for account", account_name
        while stats_key_names:
            db.run_in_transaction(txn, account_name, account_stats, stats_key_names[:LIMIT])
            stats_key_names = stats_key_names[LIMIT:]
                                            
                    
def parse_line(line):
    global account_cache
    global stats_model_cache
    global counts_cache
    
    try:
        if '\\' in line:
            line = line.replace(r'\'', '')
        mr_key, uniq_count = line.split('\t', 1)

        uniq_count = int(uniq_count)
        parts = mr_key.split(':')
        if len(parts) != 6: return # only interested in [k:handler:account:pub_id:adv_id:date_hour]
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
                # stats_model_cache format: {account_stats: set([stats_key_name|account])}
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
                

                    
def process_input_file(input_file, num_workers):
    print 'uniq user: processing stats file %s with %i workers...' % (input_file, num_workers)
    pool = ThreadPool(processes=num_workers)
    line_count = 0

    with open(input_file, 'r') as f:
        for line in f:
            parse_line(line)
            line_count += 1

            if line_count % 100 == 0: 
                print "\nuniq user: MARKER: %i lines\n" %line_count
                try:
                    update_models(pool)
                except KeyboardInterrupt:
                    print 'controller received control-c'
                    break
                except:
                    traceback.print_exc()
                    


def single_thread_process_input_file(input_file):
    print 'uniq user: processing stats file %s single thread...' % (input_file)

    with open(input_file, 'r') as f:
        for line in f:
            parse_line(line)
    single_thread_update_models()
                                
        
def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)
        
                    
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    parser.add_option("-s", '--single_thread', action='store_true', dest='single_thread', default=False)
    parser.add_option('-n', '--num_workers', type='int', dest='num_workers', default=multiprocessing.cpu_count())

    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n')
        
    setup_remote_api()    
    
    if options.single_thread:
        single_thread_process_input_file(options.input_file)
    else:
        process_input_file(options.input_file, options.num_workers)

    elapsed = time.time() - start
    print 'uniq user: updating GAE datastore took %i minutes and %i seconds' % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
