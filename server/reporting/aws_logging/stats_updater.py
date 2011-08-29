from __future__ import with_statement
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
from reporting.query_managers import StatsModelQueryManager


BATCH_LINE_COUNT = 1000
account_cache = {}
stats_qm_cache = {}


# used by reporting.tests.stats_updater_mptests
def single_thread_put_models():
    for qm in stats_qm_cache.values():
        print "putting models for account", qm.account.name()
        qm.put_stats(offline=True)           


def put_models_by_qm(qm): 
    try:    
        qm.put_stats(offline=True)
        qm.stats = []
        return 'success: account %s' %(qm.account.name())
    except KeyboardInterrupt:
        print 'child process received control-c'
        pass
    except:
        traceback.print_exc()
        return 'failed: account %s' %(qm.account.name())
    

def _has_stats(qm):
    if len(qm.stats) > 0:
        return True
    else:
        return False


def put_models(pool):
    # filter out qm's with empty stats lists
    qm_with_stats = filter(_has_stats, stats_qm_cache.values())
    
    async_results = pool.map_async(put_models_by_qm, qm_with_stats)
    results = async_results.get(0xFFFF) # set maximum timeout (seconds) to return result when it arrives
    
    print
    print 'success for %i accounts' % (len(results))

    # print status message from each process
    # print
    # print
    # for i in results:
    #   print i
    # print
    # print
    
           
def update_model(adunit_key=None, creative_key=None, country_code=None, counts=None, date=None, date_hour=None):    
    global stats_qm_cache
    global account_cache
            
    try:
        if adunit_key and counts:
            # convert encoded str of keys into real key objects
            adunit_key = db.Key(adunit_key)
            if creative_key:
                creative_key = db.Key(creative_key)
            else:
                creative_key = None
    
            if adunit_key in account_cache:
                account = account_cache[adunit_key]
            else:
                adunit = Site.get(adunit_key)
                account = adunit.account
                if account is None:
                    print 'adunit %s has no account' % (adunit_key)
                    return False
                account_cache[adunit_key] = account 
                
            # get or insert stats_qm from stats_qm_cache          
            if str(account.key()) in stats_qm_cache:
                stats_qm = stats_qm_cache[str(account.key())]
            else:
                stats_qm = StatsModelQueryManager(account)
                stats_qm_cache[str(account.key())] = stats_qm
                    
            # create stats model
            stats = StatsModel(publisher=adunit_key, 
                               advertiser=creative_key, 
                               country=country_code,                               
                               date=date, 
                               date_hour=date_hour, 
                               offline=True)

            stats.request_count = counts[0]
            stats.impression_count = counts[1]
            stats.click_count = counts[2]
            stats.conversion_count = counts[3]
            
            stats_qm.accumulate_stats(stats)
            return True
        else:
            print 'adunit_key and counts should not be None'
            return False
    except Exception, e:
        #traceback.print_exc()
        print 'EXCEPTION on adunit key %s: %s' %(adunit_key, e)
        return False
             
    
def parse_line(line):
    try:
        # handles un-escaping by mrjob local testing
        if '\\' in line:
            line = line.replace(r'\'', '')
            
        # k = k:adunit_id:creative_id:country_code:time
        # v = [req_count, imp_count, clk_count, conv_count, user_count]
        key_name, counts = line.split('\t', 1)

        # parse out key_name
        parts = key_name.split(':')
        if len(parts) != 5: return # only interested in [k:pub_id:adv_id:country_code:date_hour]
        adunit_key = parts[1]
        creative_key = parts[2]
        country_code = parts[3]
        time_str = parts[4]
        year = int('20'+time_str[:2])
        month = int(time_str[2:4])
        day = int(time_str[4:6])

        # eval counts as list of ints
        counts = eval(counts)
        
        if len(time_str) == 8:  # resolution to hour
            hour = int(time_str[6:8])
            date_hour = datetime(year, month, day, hour, tzinfo=Pacific_tzinfo())
            update_model(adunit_key=adunit_key, creative_key=creative_key, country_code=country_code,
                         counts=counts, date_hour=date_hour)
        else:   # resolution to day
            date = datetime(year, month, day)
            update_model(adunit_key=adunit_key, creative_key=creative_key, country_code=country_code,
                         counts=counts, date=date)
    except Exception, e:
        # traceback.print_exc()
        print 'EXCEPTION on line %s -> %s' %(line, e)
        


def process_input_file(input_file, num_workers):
    print 'processing stats file %s with %i workers...' % (input_file, num_workers)
    # pool = Pool(processes=num_workers)
    pool = ThreadPool(processes=num_workers)
    line_count = 0

    with open(input_file, 'r') as f:
        for line in f:
            parse_line(line)
            line_count += 1

            if line_count % BATCH_LINE_COUNT == 0: 
                print "\nMARKER: %i lines\n" %line_count
                try:
                    put_models(pool)
                except KeyboardInterrupt:
                    print 'controller received control-c'
                    break
                except:
                    traceback.print_exc()
                                                                                    
                                
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    parser.add_option('-n', '--num_workers', type='int', dest='num_workers', default=multiprocessing.cpu_count())
    
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n')
        
    utils.setup_remote_api()
    process_input_file(options.input_file, options.num_workers)
   
    elapsed = time.time() - start
    print "updating GAE datastore took %i minutes and %i seconds" % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
    
