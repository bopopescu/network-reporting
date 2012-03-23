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

# from event.models import DimensionTwoLevelOne
# from counters.models import Counter
# from event.models import db

from reporting import models as r_models


from optparse import OptionParser
parser = OptionParser()
parser.add_option("-n", "--num_threads", dest="NUM_THREADS",type="int",
                  help="How many threads should be running at peak load.", default=3)
parser.add_option("-t", "--time_at_peak", dest="TIME_AT_PEAK_QPS",type="float",
                help="How many minutes the test should run with all threads active.", default=1.0/4.0)
parser.add_option("-d", "--delay", dest="DELAY_BETWEEN_THREAD_START",type="float",
                help="How many seconds to wait between starting threads.", default=10) 
parser.add_option("-l", "--logging", dest="LOGGING",type="int",
                help="Which logging scheme to use.", default=3)         
parser.add_option("-i", "--instance_id", dest="INSTANCE_ID",type="int",
                help="LABEL THE INSTANCE.", default=0)         
parser.add_option("-e", "--exp_id", dest="TEST_ID",type="str",
                help="LABEL THE TEST.", default='PENELOPE')         
parser.add_option("-x", "--host", dest="HOST",type="str",
                help="HOST NAME.", default='eventrackerscaletest.appspot.com')         
                               

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

TEST_ID = options.TEST_ID

HOST = options.HOST

quitevent = Event()

def update_stats(key,attribute,t):
    global lock
    global stats_dict
    
    lock.acquire()
    if not key in stats_dict:
        stats_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
    stats_dict[key][attribute] += 1
    stats_dict[key]['last_update'] = t
    lock.release()


def threadproc():
    """This function is executed by each thread."""
    global lock
    global fail_lock
    global req_cnt
    
    print "Thread started: %s" % current_thread().getName()
    h = httplib2.Http(timeout=30)
    while not quitevent.is_set():
        try:
            # HTTP requests to exercise the server go here
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!            
            
            
            uid = uuid.uuid4()
            # adunits = ["agltb3B1Yi1pbmNyDAsSBFNpdGUYkaoMDA","agltb3B1Yi1pbmNyDAsSBFNpdGUYycEMDA","agltb3B1Yi1pbmNyDAsSBFNpdGUYq-wdDA"]
            adunits = ["ahRldmVudHJhY2tlcnNjYWxldGVzdHILCxIEU2l0ZRjJZQw"]
            # adunits = ["agltb3B1Yi1pbmNyDAsSBFNpdGUYycoJDA","agltb3B1Yi1pbmNyDAsSBFNpdGUYmpUgDA"]
            random.shuffle(adunits)
            adunit = adunits[0]
            t = time.time()

            req_cnt_lock.acquire()
            req_cnt += 1
            url = "http://%s/m/ad?id=%s&udid=%s&reqcnt=%s&inst=%s&test=%s"%(HOST,adunit,uid,req_cnt,INSTANCE_ID,TEST_ID)
            req_cnt_lock.release()
            
            fail_lock.acquire()
            print "URL: ",url
            fail_lock.release()
            
            resp, content = h.request(url)
                        
            hour = t
            date_hour = datetime.datetime.fromtimestamp(hour) 

            # # request data    
            key = r_models.StatsModel.get_key_name(publisher=adunit,
                                                   advertiser=None,
                                                   date_hour=date_hour)
            
            update_stats(key,'req',t)
            
            
            creative = None
            if resp.status != 200:
                fail_lock.acquire()
                print "Response not OK (status: %s)"%resp.status
                print "FAIL URL: %s"%url
                print "FAIL content: %s"%content
                fail_lock.release()
            else:    
                creative = resp.get('x-creativeid', None) # creative_id
            

            key = r_models.StatsModel.get_key_name(publisher=adunit,
                                                   advertiser=creative,
                                                   date=date_hour)
                
            if creative:
                imp_url = resp['x-imptracker'].replace('ads.mopub.com', 'eventrackerscaletest.appspot.com')

                click_url = resp['x-clickthrough'].replace('ads.mopub.com', 'eventrackerscaletest.appspot.com')
                resp, content = h.request(imp_url)
                
                if resp.status != 200:
                    fail_lock.acquire()
                    print "Response not OK (status: %s)"%resp.status
                    print "FAIL URL: %s"%imp_url
                    print "FAIL content: %s"%content
                    fail_lock.release()
                else:
                    update_stats(key,'imp',t)
                    
                # # # simulate a click 3% CTR        
                # click = False
                # if random.randint(0,1) < 1:
                #     resp, content = h.request(click_url)
                #     if resp.status != 200:
                #         fail_lock.acquire()
                #         print "Response not OK (status: %s)"%resp.status
                #         print "FAIL URL: %s"%click
                #         print "FAIL content: %s"%content
                #         fail_lock.release()
                #     else:
                #         click = True
                #         update_stats(key,'clk',t)   
                # 
                # if click:
                #     if random.random(0,1) < 1:
                #         resp, content = h.request(click_url)
                #         if resp.status != 200:
                #             fail_lock.acquire()
                #             print "Response not OK (status: %s)"%resp.status
                #             print "FAIL URL: %s"%click
                #             print "FAIL content: %s"%content
                #             fail_lock.release()
                #         else:
                #             click = True
                #             update_stats(key,'clk',t)   
            # # simulate a 10% post click converstion
            # conv = False
            # if click:
            #     if random.randint(0,99) < 10:
            #         url3 = "http://eventrackerscaletest.appspot.com/event/three?log=%s&uid=%s&appid=%s"%(LOGGING,uid,'asdf')
            #         resp3, content3 = h.request(url3)
            #         if resp3.status != 200:
            #             print "Response not OK"
            #         else:
            #             conv = True
            #         
            # # to correct for timezones
            # # date_hour += datetime.timedelta(hours=8)
            #         
            # impression data
            # if dim_one_level_one:
            #     keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
            #             Counter.get_key_name(None,dim_two_level_one,date_hour),
            #             Counter.get_key_name(dim_one_level_one,None,date_hour),]
            #     for key in keys:        
            #         lock.acquire()
            #         if not key in stats_dict:
            #             stats_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
            #         stats_dict[key]['imp'] += 1 
            #         stats_dict[key]['last_update'] = t
            #         lock.release()
            #       
            # # click data
            # if click:
            #     keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
            #             Counter.get_key_name(None,dim_two_level_one,date_hour),
            #             Counter.get_key_name(dim_one_level_one,None,date_hour),]
            #     for key in keys:        
            #         lock.acquire()
            #         if not key in stats_dict:
            #             stats_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
            #         stats_dict[key]['clk'] += 1 
            #         stats_dict[key]['last_update'] = t
            #         lock.release()
            #         
            # if conv:
            #     keys = [Counter.get_key_name(dim_one_level_one,dim_two_level_one,date_hour),
            #             Counter.get_key_name(None,dim_two_level_one,date_hour),
            #             Counter.get_key_name(dim_one_level_one,None,date_hour),]
            #     for key in keys:        
            #         lock.acquire()
            #         if not key in stats_dict:
            #             stats_dict[key] = {'imp':0,'req':0,'clk':0,'conv':0,'last_update':t}
            #         stats_dict[key]['conv'] += 1 
            #         stats_dict[key]['last_update'] = t
            #         lock.release()
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        except socket.timeout:
            print 'socket timout'

    print "Thread finished: %s" % current_thread().getName()

lock = Lock()
fail_lock = Lock()
req_cnt_lock = Lock()
req_cnt = 0
stats_dict = {}

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
    record_dictionary(stats_dict)
    print "Finished"
