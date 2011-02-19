import logging
import random
import time

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app


from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.api.taskqueue import Task


LOG_KEY_FORMAT = 'k:%(account_name)s:%(time)s:%(log_index)02d'
INDEX_KEY_FORMAT = 'k:%(account_name)s:%(time)s'
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
    account_name = kwargs.get('dim2l1')
    
    # calculate time bucke
    now = time.time()
    time_bucket = int(now)/TIME_BUCKET # maybe divide by 10 for every second
    
    
    # get the new index for this account and time bucket
    index_key = INDEX_KEY_FORMAT%dict(account_name=account_name,time=time_bucket)
    log_index = memcache.incr(index_key,initial_value=0) # starts at 1
    
    # put the log data into appropriate place
    log_key = LOG_KEY_FORMAT%dict(account_name=account_name,time=time_bucket,log_index=log_index)
    memcache.set(log_key,kwargs)
    logging.info("just put %s=%s"%(log_key,kwargs))
    
    # send of appropriately named task_queue
    task_name = TASK_NAME%dict(account_name=account_name,time=time_bucket)
    logging.info('task: %s'%task_name)
    
    try:
        t = Task(name=task_name,params={'account_name':account_name,'time':time_bucket},countdown=TIME_BUCKET+TIME_BUCKET,method='GET')
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