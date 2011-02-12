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

from threading import Event
from threading import Thread
from threading import current_thread
from threading import Lock
from urllib import urlencode

from event.models import DimensionTwoLevelOne
from counters.models import Counter
from event.models import db


from optparse import OptionParser
parser = OptionParser()
parser.add_option("-n", "--num_threads", dest="NUM_THREADS",type="int",
                  help="How many threads should be running at peak load.", default=20)
parser.add_option("-t", "--time_at_peak", dest="TIME_AT_PEAK_QPS",type="float",
                help="How many minutes the test should run with all threads active.", default=2)
parser.add_option("-d", "--delay", dest="DELAY_BETWEEN_THREAD_START",type="float",
                help="How many seconds to wait between starting threads.", default=10) 
parser.add_option("-l", "--logging", dest="LOGGING",type="int",
                help="Which logging scheme to use.", default=3)         
parser.add_option("-i", "--instance_id", dest="INSTANCE_ID",type="int",
                help="LABEL THE INSTANCE.", default=0)         
                               

(options, args) = parser.parse_args()


    
# Modify these values to control how the testing is done

# How many threads should be running at peak load.
NUM_THREADS = options.NUM_THREADS

# How many minutes the test should run with all threads active.
TIME_AT_PEAK_QPS = options.TIME_AT_PEAK_QPS

# How many seconds to wait between starting threads.
# Shouldn't be set below 30 seconds.
DELAY_BETWEEN_THREAD_START = options.DELAY_BETWEEN_THREAD_START # seconds

LOGGING = options.LOGGING

INSTANCE_ID = options.INSTANCE_ID

quitevent = Event()

def threadproc():
    """This function is executed by each thread."""
    global counter_dict
    global lock
    global fail_lock
    global req_cnt
    
    print "Thread started: %s" % current_thread().getName()
    h = httplib2.Http(timeout=30)
    while not quitevent.is_set():
        try:
            # HTTP requests to exercise the server go here
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!            
            req_cnt_lock.acquire()
            req_cnt += 1
            req_cnt_lock.release()
            
            
            uid = uuid.uuid4()
            key_name = "k:%02d:%02d"%(random.randint(0,1),random.randint(0,1))
            key_name = "k:00:00"
            dim_two_level_one = db.Key.from_path('DimensionTwoLevelOne',key_name,_app='eventrackerscaletest')
            t = time.time()
            
            url = "http://eventrackerscaletest.appspot.com/event/one?log=%s&nc=1&deadline=.08&uid=%s&id=%s&req=%s&inst=%s"%(LOGGING,uid,dim_two_level_one,req_cnt,INSTANCE_ID)
            
            fail_lock.acquire()
            print "URL: ",url
            fail_lock.release()
            
            resp, content = h.request(url)
            
            
            hour = t
            date_hour = datetime.datetime.fromtimestamp(hour) 

            # request data    
            key = Counter.get_key_name(None,dim_two_level_one,date_hour)
            lock.acquire()
            if not key in counter_dict:
                counter_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
            counter_dict[key]['req'] += 1
            counter_dict[key]['last_update'] = t
            lock.release()
            
            
            
            dim_one_level_one = None
            if resp.status != 200:
                fail_lock.acquire()
                print "Response not OK (status: %s)"%resp.status
                print "FAIL URL: %s"%url
                print "FAIL content: %s"%content
                fail_lock.release()
            else:    
                if content != "None":
                    dim_one_level_one = content # creative_id
                else:
                  print 'No creative'    
                    
            # simulate a click 3% CTR        
            click = False
            # if dim_one_level_one:
            #     if random.randint(0,99) < 3:
            #         url2 = "http://eventrackerscaletest.appspot.com/event/two?log=%s&nc=1&deadline=.08&uid=%s&dim2l1=%s&dim1l1=%s&appid=%s"%(LOGGING,uid,dim_two_level_one,dim_one_level_one,'asdf')
            #         resp2, content2 = h.request(url2)
            #         if resp2.status != 200:
            #             print "Response not OK"
            #         else:
            #             click = True   
            
            # simulate a 10% post click converstion
            conv = False
            # if click:
            #     if random.randint(0,99) < 10:
            #         url3 = "http://eventrackerscaletest.appspot.com/event/three?log=%s&uid=%s&appid=%s"%(LOGGING,uid,'asdf')
            #         resp3, content3 = h.request(url3)
            #         if resp3.status != 200:
            #             print "Response not OK"
            #         else:
            #             conv = True
                    
        
            # to correct for timezones
            # date_hour += datetime.timedelta(hours=8)
        
            # impression data
            if dim_one_level_one:
                keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
                        Counter.get_key_name(None,dim_two_level_one,date_hour),
                        Counter.get_key_name(dim_one_level_one,None,date_hour),]
                for key in keys:        
                    lock.acquire()
                    if not key in counter_dict:
                        counter_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
                    counter_dict[key]['imp'] += 1 
                    counter_dict[key]['last_update'] = t
                    lock.release()
                  
            # click data
            if click:
                keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
                        Counter.get_key_name(None,dim_two_level_one,date_hour),
                        Counter.get_key_name(dim_one_level_one,None,date_hour),]
                for key in keys:        
                    lock.acquire()
                    if not key in counter_dict:
                        counter_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
                    counter_dict[key]['clk'] += 1 
                    counter_dict[key]['last_update'] = t
                    lock.release()
                    
            if conv:
                keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
                        Counter.get_key_name(None,dim_two_level_one,date_hour),
                        Counter.get_key_name(dim_one_level_one,None,date_hour),]
                for key in keys:        
                    lock.acquire()
                    if not key in counter_dict:
                        counter_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
                    counter_dict[key]['conv'] += 1 
                    counter_dict[key]['last_update'] = t
                    lock.release()
                    
                
                    
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        except socket.timeout:
            print 'socket timout'

    print "Thread finished: %s" % current_thread().getName()

lock = Lock()
fail_lock = Lock()
req_cnt_lock = Lock()
req_cnt = 0
counter_dict = {}

def record_dictionary(d,file_name='counts.csv'):
    import csv
    writer = csv.writer(open(file_name, 'wb'), delimiter=' ')
    keys = d.keys()
    keys.sort(cmp=lambda x,y: cmp(d[x]['last_update'],d[y]['last_update']))
    for key in keys:
        writer.writerow([d[key]['req'],d[key]['imp'],d[key]['clk'],d[key]['conv'],key,d[key]['last_update']])
        


if __name__ == "__main__":
    runtime = (TIME_AT_PEAK_QPS * 60 + DELAY_BETWEEN_THREAD_START * NUM_THREADS)
    print "Total runtime will be: %d seconds" % runtime
    threads = []
    try:
        for i in range(NUM_THREADS):
            t = Thread(target=threadproc)
            t.start()
            threads.append(t)
            time.sleep(DELAY_BETWEEN_THREAD_START)
        print "All threads running"
        time.sleep(TIME_AT_PEAK_QPS*60)
        print "Completed full time at peak qps, shutting down threads"
    except:
        print "Exception raised, shutting down threads"

    quitevent.set()
    time.sleep(3)
    for t in threads:
        t.join(1.0)
    print "Finished %d"%req_cnt
    print "Recording File"
    record_dictionary(counter_dict)
    print "Finished"