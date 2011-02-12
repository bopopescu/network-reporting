import logging
import random

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task

KEY_FORMAT = 'k:%(instance_id)s:%(adunit_id)s:%(creative_id)s:%(date_hour)s:%(batch_id)s'
KEY_FORMAT2 = 'k:%(instance_id)s:%(adunit_creative)s:%(batch_id)s'

COUNT_SIZE = 10

class LogEventOne(webapp.RequestHandler):
    def get(self):
        attributes = ['uid','dim2l1','t','req','dim1l1','imp']    
        params = {}
        for attr in attributes:
            params.update({attr:self.request.get(attr,None)})
        log(**params)
        self.response.out.write('I AM LOGGING')
        
class LogEventThree(webapp.RequestHandler):
    def get(self):
        pass

# THIS IS WHERE ALL THE HEAVY LIFTING IS DONE        
def log(**kwargs): 
    global index
    global batch_id
    global instance_id
    global tracked
    
    adunit_id = kwargs['dim2l1']
    creative_id = kwargs['dim1l1']
    
    t = int(float(kwargs['t']))
    date_hour = t-t%3600
    
    #instance_id:ad_unit_id:creative_id:index

    # logging.info("I AM LOGGING: %s"%kwargs)
    
    # Put the logging info into memecache
    # The key should be based on a incrementing the index for this instance
    # k<instance_id><index>
    # the index value can either be stored as a global for the instance 
    # or as a entry in memecache with key k<instance_id>
    index += 1
    
    key = KEY_FORMAT%dict(instance_id=instance_id,adunit_id=adunit_id,creative_id=creative_id,date_hour=date_hour,batch_id=batch_id)
    
    tracked.add("%s:%s:%s"%(adunit_id,creative_id,date_hour))
    
    success = memcache.incr(key,1,None,0)
    # logging.info("key: %s %s"%(key,success))
    # After N writes to memecache we should sent out a Task like this
    # logging.info("index: %s"%index)
    if (index % COUNT_SIZE) == 0:
        t = Task(params={'batch_id':batch_id,'instance_id':instance_id,'tracked':','.join(tracked)},method='POST')
        t.add('bulk-log-processor')
        batch_id += 1
        tracked.clear()

application = webapp.WSGIApplication([('/log/one', LogEventOne),
                                      ('/log/three',LogEventThree), 
                                     ],
                                     debug=True)

def main():
    # attaches a process id to the instance
    # TODO: make sure this is unique, probably with a memcache list or counter    
    run_wsgi_app(application)

pid = globals().get("instance_id",None)
if not pid:
    globals()["instance_id"] = random.randint(1,1e6) # one in a million

index = globals().get("index",None)
if not index:
    globals()["index"] = 0

batch_id = globals().get("batch_id",None)
if not batch_id:
    globals()["batch_id"] = 0
    
tracked = globals().get("tracked",None)
if not tracked:
    globals()["tracked"] = set()

if __name__ == "__main__":
    main()