import logging
import random

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task

KEY_FORMAT = 'k:%(instance_id)s:%(log_index)02d'
BATCH_SIZE = 100

class LogEventOne(webapp.RequestHandler):
    def get(self):
        attributes = ['uid','dim2l1','t','req','dim1l1','imp']    
        params = {}
        for attr in attributes:
            params.update({attr:self.request.get(attr,None)})
        log(**params)
        self.response.out.write('I AM LOGGING')

class LogEventTwo(webapp.RequestHandler):
    def get(self):
        instance_ids = memcache.get("instances") or []
        clean_instances = []
        for inst_id in instance_ids:
            idx = memcache.get("last:%s"%inst_id) or 0
            t = Task(params={'start':idx+1,'length':BATCH_SIZE, 'instance_id':inst_id},method='GET')
            t.add('bulk-log-processor')
            clean_instances.append(inst_id)
        self.response.out.write("Cleaned up instances: %s"%clean_instances)
        
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
    add_inst = kwargs.pop('add_inst',False)
    if add_inst:
        add_instance()
     
    global index
    global instance_id

    # logging.info("I AM LOGGING: %s"%kwargs)
    
    # Put the logging info into memecache
    # The key should be based on a incrementing the index for this instance
    # k<instance_id><index>
    # the index value can either be stored as a global for the instance 
    # or as a entry in memecache with key k<instance_id>
    index += 1
    
    key = KEY_FORMAT%dict(instance_id=instance_id,log_index=index)
    success = memcache.set(key,kwargs)
    # logging.info("key: %s %s"%(key,success))
    # After N writes to memecache we should sent out a Task like this
    logging.info("req: %s",kwargs.get('req'))
    logging.info("instance: %s index: %s"%(instance_id,index))
    if (index % BATCH_SIZE) == 0:
        logging.info("sending out task")
        t = Task(params={'start':index-BATCH_SIZE+1,'length':BATCH_SIZE, 'instance_id':instance_id},method='GET')
        t.add('bulk-log-processor')
        memcache.set("last:%s"%instance_id,index)

application = webapp.WSGIApplication([('/log/one', LogEventOne),
                                      ('/log/two', LogEventTwo), 
                                      ('/log/three',LogEventThree), 
                                     ],
                                     debug=True)

def main():
    add_instance()
    run_wsgi_app(application)


# TODO: This should be moved to inside the if statement above
# add instance id to the list of instances in memecache
def add_instance():
    pid = globals().get("instance_id",None)
    if not pid:
        globals()["instance_id"] = random.randint(1,1e6) # one in a million
        logging.info("adding instance")
        lock_success = False
        while not lock_success:
            logging.info("trying to set instance id")
            lock_success = memcache.add("instances_lock","1") # should likely have an agressive short lived time
            if lock_success:
                instances = memcache.get("instances") or set()
                instances.add(instance_id)
                memcache.set("instances",instances)
                logging.info("set instances: %s"%instances)
                memcache.delete("instances_lock") # release lock

index = globals().get("index",None)
if not index:
    globals()["index"] = 0

if __name__ == "__main__":
    main()