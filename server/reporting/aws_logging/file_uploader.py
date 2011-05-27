import os
import sys
import time
import urllib2

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
from blob_server import URL_HANDLER_PATH

    

HOST = 'http://38-aws.latest.mopub-inc.appspot.com'
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
    print
    
    return blob_key


def process_stats_file(blob_key, uniq_user=False):
    blob_reader = blobstore.BlobReader(blob_key)
    
    # Read one line (up to and including a '\n' character) at a time.
    for line in blob_reader:
        if uniq_user:
            uniq_user_stats_updater.parse_line(line)
        else:
            stats_updater.parse_line(line)

    if uniq_user:
        uniq_user_stats_updater.update_models()
    else:
        stats_updater.put_models()

    

def main():
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n') 


    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)


    blob_key = upload_stats_file(options.input_file)

    if options.input_file.endswith('.uu.stats'):
        process_stats_file(blob_key, uniq_user=True)
    else:
        process_stats_file(blob_key)
    
    

if __name__ == '__main__':
  main()