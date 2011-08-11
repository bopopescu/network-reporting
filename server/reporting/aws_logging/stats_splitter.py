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


<<<<<<< HEAD
from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()


import utils
import deref_cache_builder

=======
# from appengine_django import InstallAppengineHelperForDjango
# InstallAppengineHelperForDjango()

import utils
from google.appengine.ext.db import BadKeyError


DEREF_CACHE = utils.load_deref_cache()
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
account_buckets = {} # {account_str: [lines]}


def generate_split_files(dir_path, date_str):
    for account_str, lines in account_buckets.iteritems():
        # split file name format:
        # log+YYMMDD+<account>+.adv.lc.stats
        # note that we are using + as the delimiter, since - and _ can occur in the account id
        file_name = 'log+%s+%s+.adv.lc.stats' % (date_str, account_str)
        abs_file_path = os.path.join(dir_path, file_name)
        
        with open(abs_file_path, 'w') as f:
            print 'writing to %s ...' % (file_name)
            for line in lines:
                f.write(line)
    print 'split to %i stats files' % (len(account_buckets))


def process_stats_file(stats_file):
    global account_buckets
    
    with open(stats_file, 'r') as f:
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
                if len(parts) != 9: 
                    print 'split count: %s' % (line)
                    continue 
                adunit_key = parts[1]
                
                # deref account_str from adunit_key
<<<<<<< HEAD
                deref_result = deref_cache_builder.deref_adunit(adunit_key)
=======
                deref_result = _deref_adunit(adunit_key)
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
                if not deref_result: 
                    print 'no deref: %s' % (line)
                    continue
                
                # hydrate account_buckets dict
                [app_str, account_str] = deref_result
                if account_str in account_buckets:
                    account_buckets[account_str].append(line)
                else:
                    account_buckets[account_str] = [line]
            except Exception, e:
                # traceback.print_exc()
                print 'EXCEPTION on line %s -> %s' %(line, e)
                continue
    

<<<<<<< HEAD
=======

# returns [app_str, account_str]
def _deref_adunit(adunit_str):
    if adunit_str in DEREF_CACHE:
        return DEREF_CACHE[adunit_str]

    try:
        adunit_key = db.Key(adunit_str)
        adunit = AdUnit.get(adunit_key)
        app_str = str(adunit._app_key)
        account_str = str(adunit._account)
        DEREF_CACHE[adunit_str] = [app_str, account_str]
        return [app_str, account_str]
    except BadKeyError, e:
        print 'EXCEPTION on adunit %s: %s' %(adunit_str, e)
        return None
    except Exception, e:
        # print 'ADUNIT_STR:', adunit_str
        # traceback.print_exc()
        return None


>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
def main():
    start = time.time()
    
    # make sure non-empty deref cache is loaded
<<<<<<< HEAD
    if len(deref_cache_builder.DEREF_CACHE) == 0:
        sys.exit('\nERROR: deref cache is empty')
    else:
        print '%i mappings loaded in deref cache\n' % (len(deref_cache_builder.DEREF_CACHE))
=======
    if len(DEREF_CACHE) == 0:
        sys.exit('\nERROR: deref cache is empty')
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n')
<<<<<<< HEAD
        
=======
            
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
    dir_path, file_name = os.path.split(options.input_file)
    # ex file_name: aws-logfile-2011-0610-1110.adv.lc.stats
    parts = file_name.split('-')
    year = parts[2]
    month_day = parts[3]
    date_str = year[-2:] + month_day

<<<<<<< HEAD
=======
    # for dereferencing adunits in process_stats_file
    utils.setup_remote_api()
    
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
    process_stats_file(options.input_file)   
    generate_split_files(dir_path, date_str)
    
    elapsed = time.time() - start
    print "splitting %s took %i minutes and %i seconds" % (file_name, elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()