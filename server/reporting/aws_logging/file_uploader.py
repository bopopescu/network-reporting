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


def start_blob_processing_request(blob_key, blob_type='log_counts'):    
    url = HOST + UPDATE_STATS_HANDLER_PATH + '?blob_key=%s&blob_type=%s' % (blob_key, blob_type)
    print
    print 'pinging %s ...' % (url)
    process_blob_request = urllib2.Request(url)
    response = urllib2.urlopen(process_blob_request).read() 
    # urllib2.urlopen(process_blob_request)
    print
    print response
        

def main():
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    parser.add_option('-b', '--blobstore', action='store_true', dest='blobstore', default=False)
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n') 


    blob_key = upload_stats_file(options.input_file)


    start = time.time()
    
    if options.input_file.endswith('.uu.stats'):
        if options.blobstore:   # run stats_updater on GAE backend
            start_blob_processing_request(blob_key, 'uniq_user')
        else:
            uniq_user_stats_updater.process_blob_stats_file(blob_key)
    else:   # run stats_updater on local machine
        if options.blobstore:
            start_blob_processing_request(blob_key, 'log_counts')
        else:
            stats_updater.process_blob_stats_file(blob_key)
    
    elapsed = time.time() - start
    print
    print 'updating GAE datastore with blob %s took %i minutes and %i seconds' % (blob_key, elapsed/60, elapsed%60)
    
    

if __name__ == '__main__':
  main()