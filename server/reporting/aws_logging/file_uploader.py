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
# sys.path.append('/home/ubuntu/mopub/server/reporting')
# sys.path.append('/home/ubuntu/google_appengine')
# sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
# sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
# sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
# sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
# sys.path.append('/home/ubuntu/google_appengine/lib/webob')
# sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')


from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

from blob_server import URL_HANDLER_PATH

# HOST = 'http://localhost:8003'
HOST = 'http://38-aws.latest.mopub-inc.appspot.com'


def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    if not options.input_file:
        sys.exit('\nERROR: input file must be specified\n')   
    
    if not os.path.exists(options.input_file):
        sys.exit('\nERROR: input file does not exist\n') 

    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the input file
    # "file" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.
    
    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"file": open(options.input_file)})

    # GET request to get secret upload url
    print
    print
    print 'pinging %s ...' % (HOST + URL_HANDLER_PATH)
    upload_url_request = urllib2.Request(HOST + URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_request).read()

    print 
    print 'returning secret upload url:'
    print upload_url
    print
    
    # POST request to upload input file
    file_upload_request = urllib2.Request(upload_url, datagen, headers)
    urllib2.urlopen(file_upload_request)
    
           
    elapsed = time.time() - start
    print 'uploading %s to GAE blobstore took %i minutes and %i seconds' % (options.input_file, elapsed/60, elapsed%60)
    print
    


if __name__ == '__main__':
  main()