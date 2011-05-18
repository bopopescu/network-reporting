# !/usr/bin/env python
from appengine_django import LoadDjango
LoadDjango()
import os
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None


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
from publisher.models import Site
from reporting.models import StatsModel, Pacific_tzinfo
from reporting.query_managers import StatsModelQueryManager



account_cache = {}
stats_qm_cache = {}


def clear_cache():
    global account_cache
    account_cache = {}
    global stats_qm_cache
    stats_qm_cache = {}


def put_models():
    for qm in stats_qm_cache.values():
        print "putting models for account", qm.account.name()
        qm.put_stats(offline=True)
    clear_cache()
           
           
def update_model(adunit_key=None, creative_key=None, 
                 country_code=None, brand_name=None, marketing_name=None, device_os=None, device_os_version=None, 
                 counts=None, date_hour=None, date=None):    
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
            
            # get or insert account from account_cache
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
                
            stats = StatsModel(publisher=adunit_key, 
                               advertiser=creative_key, 
                               country=country_code,
                               brand_name=brand_name,
                               marketing_name=marketing_name,
                               device_os=device_os,
                               device_os_version=device_os_version,
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
        # traceback.print_exc()
        print 'EXCEPTION on adunit key %s -> %s' %(adunit_key, e)
        return False
             
    
def parse_and_update_models(input_file):
    with open(input_file, 'r') as f:
        for line in f:
            try:
                # handles un-escaping by mrjob local testing
                if '\\' in line:
                    line = line.replace(r'\'', '')
                
                # k = k:adunit_id:creative_id:country_code:brand_name:marketing_name:device_os:device_os_version:time
                # v = [req_count, imp_count, clk_count, conv_count, user_count]
                key_name, counts = line.split('\t', 1)

                # parse out key_name
                parts = key_name.split(':')
                if len(parts) != 9: continue 
                adunit_key = parts[1]
                creative_key = parts[2]

                country_code = parts[3]            
                brand_name = parts[4] 
                marketing_name = parts[5]            
                device_os = parts[6]
                device_os_version = parts[7]

                time_str = parts[8]
                year = int('20'+time_str[:2])
                month = int(time_str[2:4])
                day = int(time_str[4:6])
            
                # eval counts as list of ints
                counts = eval(counts)

                if len(time_str) == 8:  # resolution to hour
                    hour = int(time_str[6:8])
                    date_hour = datetime(year, month, day, hour, tzinfo=Pacific_tzinfo())
                    update_model(adunit_key=adunit_key, creative_key=creative_key, 
                                 country_code=country_code, brand_name=brand_name, marketing_name=marketing_name, device_os=device_os, device_os_version=device_os_version,
                                 counts=counts, date_hour=date_hour)
                else:   # resolution to day
                    date = datetime(year, month, day)
                    update_model(adunit_key=adunit_key, creative_key=creative_key, 
                                 country_code=country_code, brand_name=brand_name, marketing_name=marketing_name, device_os=device_os, device_os_version=device_os_version, 
                                 counts=counts, date=date)
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
    
    print "processing %s for GAE datastore..." %options.input_file
    parse_and_update_models(options.input_file)
    put_models()
   
    elapsed = time.time() - start
    print "updating GAE datastore took %i minutes and %i seconds" % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
    