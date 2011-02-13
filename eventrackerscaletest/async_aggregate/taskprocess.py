import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task
from event.models import db

from counters.models import Counter

from async.main import KEY_FORMAT2

 # ['uid','dim2l1','t','req','dim1l1','imp']    
 # adunit dim2l1
 # creative dim1l1

class LogTaskHandler(webapp.RequestHandler):
    def post(self):
        # logging.info("I AM PROCESSING A TASK")
        # update a list of counters across the various dimensions
        batch_id = int(self.request.get("batch_id"))
        instance_id = int(self.request.get("instance_id"))
        tracked = self.request.get("tracked").split(',')
        
        keys = [KEY_FORMAT2%dict(instance_id=instance_id,batch_id=batch_id,adunit_creative=adunit_creative) 
                 for adunit_creative in tracked]
        
        logging.info("we have %d keys %s"%(len(keys),keys))
        
        
        # datastore put        
        def increment_counter(key_name, value, adunit_id, creative_id, date_hour):
            # datastore get
            # logging.info("KEY_NAME: %s"%key_name)
            obj = Counter.get_by_key_name(key_name)
            if obj:
                # update
                obj.count_one += value
            else:
                obj = Counter(dimension_one=creative_id,dimension_two=adunit_id,date_hour=date_hour,count_one=value)
            # datastore put
            obj.put()
        
       
        # grab logs from memecache         
        data_dicts = memcache.get_multi(keys)   
        
        
        for k,v in data_dicts.iteritems():
            
            logging.info(k)
            parts = k.split(':')
            adunit_id = parts[2]
            creative_id = parts[3]
            hour = int(parts[4])
            
            date_hour = datetime.datetime.fromtimestamp(hour)
        
        
            key_name = Counter.get_key_name(None,adunit_id,date_hour)
            
            increment_counter(key_name, int(v), adunit_id, None, date_hour)
          
            if creative_id:
                key_name = Counter.get_key_name(creative_id,None,date_hour)

                db.run_in_transaction(increment_counter, key_name, int(v), None, creative_id, date_hour)
                
                key_name = Counter.get_key_name(creative_id,adunit_id,date_hour)

                db.run_in_transaction(increment_counter, key_name, int(v), adunit_id, creative_id, date_hour)
        
        
       
            
        
        

application = webapp.WSGIApplication([('/_ah/queue/bulk-log-processor', LogTaskHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()