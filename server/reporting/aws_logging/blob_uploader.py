import os
import sys
import time
import urllib2
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

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

import utils
from reporting.query_managers import BlobLogQueryManager


BACKEND = 'stats-updater'
APP = 'mopub-inc'     
HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)

URL_HANDLER_PATH = '/offline/get_upload_url'
UPDATE_STATS_HANDLER_PATH = '/offline/update_stats'

MAX_TRY_COUNT = 3


def upload_stats_file(stats_file):
    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the input file
    # "file" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"file": open(stats_file)})

    # GET request to get secret upload url
    print
    print 'pinging %s ...' % (HOST + URL_HANDLER_PATH)
    upload_url_request = urllib2.Request(HOST + URL_HANDLER_PATH)
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
    return blob_key


def update_bloblog_model(date_str, blob_key, account=None):
    qm = BlobLogQueryManager()
    dt = datetime.strptime(date_str, '%y%m%d').date()
    put_result = qm.put_bloblog(date=dt, blob_key=blob_key, account=account)
    print
    print 'put BlobLog model:'
    print put_result
    

def process_directory(directory):
    for file_name in os.listdir(directory):
        print
        print
        print
        abs_file_path = os.path.join(directory, file_name)
        if os.path.isfile(abs_file_path):
            # file name format:
            # log+YYMMDD+<account>+adv.lc.stats
            if file_name.startswith('log') and file_name.endswith('adv.lc.stats'):
                parts = file_name.split('+')
                date_str = parts[1]
                account = parts[2]

                blob_key = upload_stats_file(abs_file_path)
                update_bloblog_model(date_str, blob_key, account)
    

def main():
    parser = OptionParser()
    parser.add_option('-d', '--directory', dest='directory')
    (options, args) = parser.parse_args()
    
    if not options.directory:
        sys.exit('\nERROR: directory containing log blob stats files must be specified\n')   
    if not os.path.exists(options.directory):
        sys.exit('\nERROR: directory does not exist\n') 
    if not os.path.isdir(options.directory):
        sys.exit('\nERROR: not a directory\n') 

    utils.setup_remote_api()
    process_directory(options.directory)
    

if __name__ == '__main__':
    main()