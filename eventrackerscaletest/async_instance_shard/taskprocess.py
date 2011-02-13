import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task
from event.models import db

from counters.models import Counter

from async.main import KEY_FORMAT

 # ['uid','dim2l1','t','req','dim1l1','imp']    
 # adunit dim2l1
 # creative dim1l1

class LogTaskHandler(webapp.RequestHandler):
    def get(self):
        # logging.info("I AM PROCESSING A TASK")
        # update a list of counters across the various dimensions
        start = int(self.request.get("start"))
        length = int(self.request.get("length"))
        instance_id = int(self.request.get("instance_id"))
        
        keys = [KEY_FORMAT%dict(instance_id=instance_id,log_index=i) 
                 for i in range(start,length+start)]
        
        # logging.info("we have %d keys %s"%(len(keys),keys))
        
        # grab logs from memecache         
        data_dicts = memcache.get_multi(keys)   
        
        logging.info("%s"%[k for k,d in data_dicts.iteritems() if d])
        
        counter_dict = {}      
        def update_count(dimension_one,dimension_two,date_hour,attribute,req,incr=1):
            # logging.info("update_count %s %s"%(dimension_one,dimension_two))
            key = Counter.get_key_name(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
            # logging.info("key: %s"%key)
            if key in counter_dict:
                setattr(counter_dict[key],attribute,getattr(counter_dict[key],attribute)+incr) # counter[key].attribute += incr
            else:
                counter_dict[key] = Counter(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
                setattr(counter_dict[key],attribute,incr) # counter_dict[key] = incr
            counter_dict[key].reqs.append(req)
                
            
        # iterate through log lines and update appropriate counters
        # logging.info("data: %s"%data_dicts)
        # logging.info("we have %d log lines"%len(data_dicts))    
        
        for k,d in data_dicts.iteritems():
            if d:
                dim2l1 = d['dim2l1']
                dim1l1 = d.get('dim1l1',None)
                req = int(d.get('req'))
                t = int(float(d['t']))
                hour = t-t%3600
                date_hour = datetime.datetime.fromtimestamp(hour)
                # increment impresssions
                if dim1l1:
                    # adunit-creative impression
                    update_count(dim1l1,dim2l1,date_hour,'count_two',req)
                    # creative impression
                    update_count(dim1l1,None,date_hour,'count_two',req)
                    # adunit impression
                    update_count(None,dim2l1,date_hour,'count_two',req)
                # increment request for adunit
                update_count(None,dim2l1,date_hour,'count_one',req)
            else:
                logging.error("NO value for key %s exists"%k)    
        
        logging.info("we have %d counters"%len(counter_dict))    
            
        # datastore put        
        def increment_counter(counter):
            # datastore get
            key_name = counter.key().name()
            counter.reqs = [] #list(set(counter.reqs))
            obj = Counter.get_by_key_name(key_name)
            if obj:
                # update
                obj += counter
            else:
                counter.reqs = counter.reqs
                obj = counter
                
            # datastore put
            logging.info("putting in key_name: %s value: %s,%s"%(key_name,counter.count_one,counter.count_two))
            obj.put()
        
        failed_writes = []
        for key_name, counter in counter_dict.iteritems():
            # logging.info("putting %s into datastore"%key_name)
            # increment_counter(counter)
            try:
                db.run_in_transaction(increment_counter, counter)
            except db.TransactionFailedError:
                failed_writes.append(counter)
        
        while failed_writes:
            logging.info("trying failed ones again: %s"%failed_writes)
            counter = failed_writes[0]
            try:
                db.run_in_transaction(increment_counter, counter)
                failed_writes.remove(counter)
            except db.TransactionFailedError:
                # rotate the counters
                failed_writes = failed_writes[1:] + [counter]        

application = webapp.WSGIApplication([('/_ah/queue/bulk-log-processor', LogTaskHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()