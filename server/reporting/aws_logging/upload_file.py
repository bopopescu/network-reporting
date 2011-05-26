import os
import sys
import time
import traceback
import urllib
import urllib2

from datetime import datetime
from optparse import OptionParser


# add mopub root to path
sys.path.append(os.getcwd()+'/../../')


from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from poster.encode import multipart_encode
from poster.streaminghttp import register_openers



def main():
    # start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()    

    # Register the streaming http handlers with urllib2
    register_openers()

    # Start the multipart/form-data encoding of the file "DSC0001.jpg"
    # "image1" is the name of the parameter, which is normally set
    # via the "name" parameter of the HTML <input> tag.

    # headers contains the necessary Content-Type and Content-Length
    # datagen is a generator object that yields the encoded parameters
    datagen, headers = multipart_encode({"file": open(options.input_file)})

    # Create the Request object
    request = urllib2.Request('http://localhost:8002/offline/', datagen, headers)

    # print request

    # Actually do the request, and get the response
    print urllib2.urlopen(request).read()
    
           
    # elapsed = time.time() - start
    # print 'uploading %s to GAE blobstore took %i minutes and %i seconds' % (options.input_file, elapsed/60, elapsed%60)
    


if __name__ == '__main__':
  main()