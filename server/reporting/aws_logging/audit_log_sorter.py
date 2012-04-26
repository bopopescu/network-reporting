import json
import os
import sys
import time
import traceback
import urllib
import urllib2

import datetime
from optparse import OptionParser

import multiprocessing
from multiprocessing.pool import ThreadPool

##Upload stuff
# add mopub root to path
sys.path.append(os.path.dirname(os.path.abspath( __file__ ))+'/../../')

from common.utils.timezones import Pacific_tzinfo

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

from poster.encode import multipart_encode, MultipartParam
from poster.streaminghttp import register_openers

import utils

BACKEND = 'stats-updater'
APP = 'mopub-inc'     
UPLOAD_HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)

URL_HANDLER_PATH = '/offline/get_upload_url'
UPDATE_STATS_HANDLER_PATH = '/offline/update_stats'

MAX_TRY_COUNT = 3

##Downlaod stuff
ROOT_DIR = '~/aws_logs/'
HOST = 'http://%s.latest.mopub-inc.appspot.com'
MAX_TRIES = 3
SLEEP_DELAY = 10

def get_json_for_hour(timestamp, loc, start_key=None, filename=None):
    if start_key:
        if filename:
            url = '%s/files/download?dh=%s&start_key=%s&filename=%s' % (HOST%loc, timestamp, start_key, filename)
        else:
            url = '%s/files/download?dh=%s&start_key=%s' % (HOST%loc, timestamp, start_key)
    else:
        if filename:
            url = '%s/files/download?dh=%s&filename=%s' % (HOST%loc, timestamp, filename)
        else:
            url = '%s/files/download?dh=%s' % (HOST%loc, timestamp)
        
    request = urllib2.Request(url)
    
    tries = 0
    while True:
        try:
            json = urllib2.urlopen(request).read()
            info = eval(json)
            print len(info['urls'])
            return info
        except KeyboardInterrupt:
            sys.exit('received control-c while getting json for hour')
        except:
            traceback.print_exc()
            tries += 1
            print 'try count:', tries
            if tries < MAX_TRIES:
                print 'sleeping for %i seconds...' % (SLEEP_DELAY)
                time.sleep(SLEEP_DELAY) # sleep 10 secs
            else:
                sys.exit('cannot download json: %s' %(e))
    
    
def download_blob_by_url(blob_url, dir_path, year, month_day, hour, loc, filename, paths):
    tries = 0
    output = ''
    while True:
        try:
            url = HOST%loc + blob_url
            blob = urllib.urlopen(url).readlines()
            for line in blob:
                info = json.loads(line)
                email = info.get('account_email')
                if email:
                    file_name = '-'.join([email.replace('@',"_at_").replace('.','_dot_'), year, month_day, hour]) + '.blog'
                else:
                    file_name = '-'.join(['no_email', year, month_day, hour]) + '.blog'

                abs_file_path = os.path.join(dir_path, file_name)
                if abs_file_path in paths:
                    with open(abs_file_path, 'a') as f:
                        f.write(line)
                else:
                    with open(abs_file_path, 'w') as f:
                        f.write(line)
                    paths.append(abs_file_path)
                   
                output += 'written to %s\n\turl: %s\n' % (abs_file_path, blob_url)
            return output    
        except KeyboardInterrupt:
            sys.exit('thread received control-c')
        except:
            traceback.print_exc()
            tries += 1
            print 'try count: %i, url: %s' % (tries, blob_url)
            if tries < MAX_TRIES:
                print 'sleeping for %i seconds...' % (SLEEP_DELAY)
                time.sleep(SLEEP_DELAY) # sleep 10 secs
            else:
                return 'error for %s-%s-%s\n\turl: %s' % (year, month_day, hour, blob_url)
    

def download_blob_logs(pool, timestamp, url_list, location, filename=None):
    root_dir = ROOT_DIR.replace('~', os.path.expanduser('~'))
    year = timestamp[:4]
    month_day = timestamp[4:8]
    hour = timestamp[-2:] + '00'
    
    day_dir = 'audit-day-' + year + '-' + month_day
    hour_dir = 'hour-' + year + '-' + month_day + '-' + hour
    dir_path = os.path.join(root_dir, day_dir, hour_dir)
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)
    
    paths = []
    async_results = [pool.apply_async(download_blob_by_url, (url, dir_path, year, month_day, hour, location, filename, paths)) for url in url_list]
    
    # print status message from each process
    print
    print
    for ar in async_results:
        print ar.get(0xFFFF)
    print
    print
    
    return paths

def process_hour(timestamp, num_workers, filename, location):
    url_list = []
    
    info = get_json_for_hour(timestamp, location, filename=filename)
    url_list.extend(info['urls'])
    
    while 'start_key' in info:
        info = get_json_for_hour(timestamp, location, info['start_key'], filename=filename)
        url_list.extend(info['urls'])
    print 'retrieved %i urls for hour %s' % (len(url_list), timestamp)
    
    pool = ThreadPool(processes=num_workers)
    try:
        paths = download_blob_logs(pool, timestamp, url_list, location, filename=filename)
    except KeyboardInterrupt:
        sys.exit('controller received control-c')
    except:
        traceback.print_exc()
    else:
        return paths

def upload_audit_file(audit_file):
    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the input file
    # "file" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.

    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    
    mp = MultipartParam("file", filename=os.path.basename(audit_file), fileobj=open(audit_file))
    
    datagen, headers = multipart_encode([mp])

    # GET request to get secret upload url
    print
    print 'pinging %s ...' % (UPLOAD_HOST + URL_HANDLER_PATH)
    upload_url_request = urllib2.Request(UPLOAD_HOST + URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_request).read()

    print 
    print 'returning secret upload url:'
    print upload_url

    # POST request to upload input file
    try_count = 0
    while True:
        try:
            file_upload_request = urllib2.Request(upload_url, datagen, headers)
            blob_key = urllib2.urlopen(file_upload_request).read()
            break
        except:
            try_count += 1
            print 'failed %i times...' %(try_count)
            traceback.print_exc()            
            if try_count < 3:
                time.sleep(10)
            else:
                break

    print
    print 'returning blob key:'
    print blob_key    
    #return blob_key

def main():
    start = time.time()

    parser = OptionParser()
    parser.add_option('-t', '--timestamp (YYYYMMDD or YYYYMMDDHH)', dest='timestamp')
    parser.add_option('-n', '--num_workers', type='int', dest='num_workers', default=multiprocessing.cpu_count())
    parser.add_option('-f', '--filename', type='str', dest='filename', default='audit' )
    parser.add_option('-l', '--location', type='str', dest='location', default='38')
    (options, args) = parser.parse_args()
    
    if options.timestamp:
        ts = options.timestamp
    else:
        ts = (datetime.datetime.now(Pacific_tzinfo())-datetime.timedelta(hours=1)).strftime("%Y%m%d%H")
    if len(ts) == 10: # hour
        print 'processing hour %s with %i threads' % (ts, options.num_workers)
        paths = process_hour(ts, options.num_workers, options.filename, options.location)
    elif len(ts) == 8: # day
        print 'processing day %s with %i threads' % (ts, options.num_workers)
        for h in range(24): # simulate hours 00-23
            hour_ts = ts + '0' + str(h) if h < 10 else ts + str(h)
            paths = process_hour(hour_ts, options.num_workers, options.filename, options.location)
    else:
        sys.exit('timestamp format invalid; either YYYYMMDD or YYYYMMDDHH')
    
    elapsed = time.time() - start
    
    print "parallelized download of logs from blobstore for %s took %i minutes and %i seconds" % (ts, elapsed/60, elapsed%60)
        
    utils.setup_remote_api()
    
    for path in paths:
        upload_audit_file(path)
    
        
if __name__ == '__main__':
    main()
