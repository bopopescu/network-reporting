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

from google.appengine.ext import blobstore
from google.appengine.ext.remote_api import remote_api_stub


from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

import stats_updater
import uniq_user_stats_updater
import utils
from blob_server import URL_HANDLER_PATH, UPDATE_STATS_HANDLER_PATH
from reporting.query_managers import BlobLogQueryManager


BACKEND = 'stats-updater'
APP = 'mopub-inc'     
HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)
# HOST = 'http://localhost:8003'


def upload_stats_file(stats_file):
    start = time.time()
    
    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the input file
    # "file" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"file": open(stats_file)})
    print headers

    # GET request to get secret upload url
    print
    print
    print 'pinging %s ...' % (HOST + URL_HANDLER_PATH)
    upload_url_request = urllib2.Request(HOST + URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_request).read()

    print 
    print 'returning secret upload url:'
    print upload_url
    
    # POST request to upload input file
    file_upload_request = urllib2.Request(upload_url, datagen, headers)
    blob_key = urllib2.urlopen(file_upload_request).read()
    
    print
    print 'blob key:'
    print blob_key
    
    elapsed = time.time() - start
    print
    print 'uploading %s to GAE blobstore took %i minutes and %i seconds' % (stats_file, elapsed/60, elapsed%60)
    
    return blob_key


def queue_process_blob_request(blob_key, uniq_user=False):
    if uniq_user:
        blob_type = 'uniq_user'
    else:
        blob_type = 'log_counts'
        
    # url to add process task to a taskqueue
    url = HOST + UPDATE_STATS_HANDLER_PATH + '?blob_key=%s&blob_type=%s' % (blob_key, blob_type)
    print
    print 'pinging %s ...' % (url)
    process_blob_request = urllib2.Request(url)
    response = urllib2.urlopen(process_blob_request).read() 
    print
    print response
        

def update_bloblog_model(date_str, blob_key):
    qm = BlobLogQueryManager()
    dt = datetime.strptime(date_str, '%y%m%d').date()
    put_result = qm.put_bloblog(date=dt, blob_key=blob_key)
    print put_result
    

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)



def main():
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n') 

    date_str = options.input_file.split('-')[2]
    date_str = date_str.split('.')[0]
    print date_str
    
    setup_remote_api()
    blob_key = upload_stats_file(options.input_file)
    update_bloblog_model(date_str, blob_key)
    
    # start = time.time()
    # 
    # if options.input_file.endswith('.uu.stats'):
    #     queue_process_blob_request(blob_key, True)
    # else:   
    #     queue_process_blob_request(blob_key)
    #     
    # elapsed = time.time() - start
    # print
    # print 'uploading blob %s and queueing processing task took %i minutes and %i seconds' % (blob_key, elapsed/60, elapsed%60)
    
    

if __name__ == '__main__':
  main()