#    Copyright 2009 Google Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

"""Simple web application load testing script.

This is a simple web application load
testing skeleton script. Modify the code between !!!!!
to make the requests you want load tested.
"""

import httplib2
import random
import socket
import time
import datetime
import uuid
import sys
import os

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append('/'.join(os.getcwd().split("/")[:-1]))
sys.path.append('.')

from urllib import urlencode
from advertiser.models import Campaign

from optparse import OptionParser
parser = OptionParser()
     
parser.add_option("-x", "--host", dest="HOST",type="str",
                help="HOST NAME.", default='localhost:8080')
                
parser.add_option("-a", "--adunit", dest="ADUNIT",type="str",
                help="ADUNIT KEY", default="agltb3B1Yi1pbmNyCgsSBFNpdGUYZQw")


(options, args) = parser.parse_args()

# Modify these values to control how the testing is done
HOST = options.HOST
ADUNIT = options.ADUNIT

h = httplib2.Http(timeout=30)

def simulate():
    """This function is executed by each thread."""
    try:
        # HTTP requests to exercise the server go here
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!            
        
        uid = uuid.uuid4()
        t = time.time()
        
        url = "http://%s/m/ad?id=%s&udid=%s"%(HOST,ADUNIT,uid)
        
        resp, content = h.request(url)
                    
        hour = t
        date_hour = datetime.datetime.fromtimestamp(hour) 
        
        
        creative = None
        if resp.status != 200:
            print "Response not OK (status: %s)"%resp.status
            print "FAIL URL: %s"%url
            print "FAIL content: %s"%content
        else:    
            creative = resp.get('x-creativeid', None) # creative_id

            if creative is None:
                print "creative: ", None
            else: 
                print "creative: ", creative


        # if creative:
        #        imp_url = resp['x-imptracker'].replace('ads.mopub.com', HOST)
        # 
        #        click_url = resp['x-clickthrough'].replace('ads.mopub.com', HOST)
        #        resp, content = h.request(imp_url)
        #        
        #        if resp.status != 200:
        #            print "Response not OK (status: %s)"%resp.status
        #            print "FAIL URL: %s"%imp_url
        #            print "FAIL content: %s"%content
        #        else:
        #            print "Successfully Recorded Impression"
        #            
        #        # # simulate a click 3% CTR        
        #        click = False
        #        if random.randint(0,1) < 1:
        #            resp, content = h.request(click_url)
        #            if resp.status != 200:
        #                print "Response not OK (status: %s)"%resp.status
        #                print "FAIL URL: %s"%click
        #                print "FAIL content: %s"%content
        #            else:
        #                click = True
            
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    except socket.timeout:
        print 'socket timout'


if __name__ == "__main__":
   simulate()
