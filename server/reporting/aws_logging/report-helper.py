from __future__ import with_statement

import os
import sys
import time
import traceback
import logging
# import multiprocessing

from datetime import datetime
# from multiprocessing import Pool
# from multiprocessing.pool import ThreadPool
from optparse import OptionParser

# # add mopub root to path
# sys.path.append(os.getcwd()+'/../../')
# 
# 
# # for ubuntu EC2
# sys.path.append('/home/ubuntu/mopub/server')
# sys.path.append('/home/ubuntu/mopub/server/reporting')
# sys.path.append('/home/ubuntu/google_appengine')
# sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
# sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
# sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
# sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
# sys.path.append('/home/ubuntu/google_appengine/lib/webob')
# sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')
# 
# from appengine_django import InstallAppengineHelperForDjango
# InstallAppengineHelperForDjango()
# 
# from google.appengine.ext import blobstore
# from google.appengine.ext import db
# from google.appengine.api import logservice
# 
# import utils
# from publisher.models import Site
# from reporting.models import StatsModel, Pacific_tzinfo
# from reporting.query_managers import StatsModelQueryManager


                        
def parse_line(line):
    try:
        # k = k:adunit_id:creative_id:country_code:brand_name:marketing_name:device_os:device_os_version:time
        # v = [req_count, imp_count, clk_count, conv_count, user_count]
        key_name, counts = line.split('\t', 1)

        # parse out key_name
        parts = key_name.split(':')
        if len(parts) != 9: return 
        time_str = parts[8]

        if len(time_str) == 8:  # resolution to hour
            return line
        else:   # resolution to day
            return None
    except Exception, e:
        # traceback.print_exc()
        print 'EXCEPTION on line %s -> %s' %(line, e)
        return None

    
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-i', '--input_file', dest='input_file')
    parser.add_option('-o', '--output_file', dest='output_file')
    (options, args) = parser.parse_args()
    
    print 'parsing %s to %s' % (options.input_file, options.output_file)
    
    with open(options.input_file, 'r') as in_stream:
        with open(options.output_file, 'w') as out_stream:
            for line in in_stream:
                result = parse_line(line)
                if result:
                    out_stream.write(result)
            

if __name__ == '__main__':
    main()
