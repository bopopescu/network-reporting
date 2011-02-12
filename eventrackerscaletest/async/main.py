import logging
import random
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api.taskqueue import Task

ACCOUNT_KEY_FORMAT = 'k:%(account_name)s'
BASE_KEY_FORMAT = '%(type)s:%(dim_one_level_one)s:%(dim_two_level_one)s:%(time_bucket)s'
REQ_KEY_FORMAT = 'R:%(dim_one_level_one)s:%(dim_two_level_one)s:%(time_bucket)s'
IMP_KEY_FORMAT = 'I:%(dim_one_level_one)s:%(dim_two_level_one)s:%(time_bucket)s'
CLK_KEY_FORMAT = 'C:%(dim_one_level_one)s:%(dim_two_level_one)s:%(time_bucket)s'
CNV_KEY_FORMAT = 'A:%(dim_one_level_one)s:%(dim_two_level_one)s:%(time_bucket)s'
TASK_NAME = 't-%(account_name)s-%(time)s' # note time will be bucketed

TIME_BUCKET = 10 # seconds

class LogEventOne(webapp.RequestHandler):
    def get(self):
        attributes = ['uid','dim2l1','t','req','dim1l1','imp','clk','conv','appid']    
        params = {}
        for attr in attributes:
            params.update({attr:self.request.get(attr,None)})
        log(**params)
        self.response.out.write('I AM LOGGING')

class LogEventTwo(webapp.RequestHandler):
    def get(self):
        self.response.out.write("Nothing to see here")
        
class LogEventThree(webapp.RequestHandler):
    def get(self):
        key = self.request.get('key')
        value = memcache.get(key)
        
        flush = bool(int(self.request.get('flush','0')))
        if flush:
            self.response.out.write(memcache.flush_all())
        else:
            self.response.out.write(value)

# THIS IS WHERE ALL THE HEAVY LIFTING IS DONE        
def log(**kwargs):
    account_name = kwargs.get('dim2l1') # we use the the adunit id as the account key
    now = float(kwargs.get('t'))
    time_bucket = int(now)/TIME_BUCKET # maybe divide by 10 for every second
    
    # get the new index
    # index_key = INDEX_KEY_FORMAT%dict(account_name=account_name)
    # log_index = memcache.incr(index_key,initial_value=0) # starts at 1
    
    dim1l1 = kwargs.get('dim1l1','') # creative
    dim2l1 = kwargs.get('dim2l1','') # adunit
    
    account_key = ACCOUNT_KEY_FORMAT%dict(account_name=account_name)
    # TODO: make this list real
    logging.info("putting key,value (%s,%s)"%(account_key,['%s:%s'%(dim2l1,dim1l1)]))
    
    # put a list of all creative-adunit tuples to be updated for this account and epoch
    # currently this defaults to just the one tuple. List of counters to be dumped
    memcache.set(account_key,['%s:%s'%(dim2l1,dim1l1)])
    
    # put the log data into appropriate place
    increment_dict = {}
    # if there is an impression
    if dim1l1:
      # impression for adunit-creative
      counter_key = IMP_KEY_FORMAT%dict(dim_two_level_one=dim2l1,
                                        dim_one_level_one=dim1l1,
                                        time_bucket=time_bucket)
      increment_dict[counter_key] = 1
      # impression for creative 
      counter_key = IMP_KEY_FORMAT%dict(dim_two_level_one='',
                                        dim_one_level_one=dim1l1,
                                        time_bucket=time_bucket)
      increment_dict[counter_key] = 1                                  
      # impression for adunit 
      counter_key = IMP_KEY_FORMAT%dict(dim_two_level_one=dim2l1,
                                        dim_one_level_one='',
                                        time_bucket=time_bucket)
                                        
      increment_dict[counter_key] = 1
      
      # increment request for creative 
      counter_key = REQ_KEY_FORMAT%dict(dim_two_level_one='',
                                        dim_one_level_one=dim1l1,
                                        time_bucket=time_bucket)
      increment_dict[counter_key] = 1                                  
      # increment request for adunit-creative 
      counter_key = REQ_KEY_FORMAT%dict(dim_two_level_one=dim2l1,
                                        dim_one_level_one=dim1l1,
                                        time_bucket=time_bucket)
      increment_dict[counter_key] = 1
      
    # increment request count for only the adunit 
    counter_key = REQ_KEY_FORMAT%dict(dim_two_level_one=dim2l1,
                                      dim_one_level_one='',
                                      time_bucket=time_bucket)
    increment_dict[counter_key] = 1
                                      
    count_dict = memcache.offset_multi(increment_dict,initial_value=0)
    
    # send to appropriately named task_queue
    task_name = TASK_NAME%dict(account_name=account_name,time=time_bucket)
    logging.info('task: %s'%task_name)
    try:
        t = Task(name=task_name,params={'account_name':account_name,'time_bucket':time_bucket},countdown=TIME_BUCKET,method='GET')
        t.add('bulk-log-processor')
    except taskqueue.TaskAlreadyExistsError:
        logging.info("task %s already exists"%task_name)
            
    
application = webapp.WSGIApplication([('/log/one', LogEventOne),
                                      ('/log/two', LogEventTwo), 
                                      ('/log/three',LogEventThree), 
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()