import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task
from event.models import db

from counters.models import Counter

from async.main import LogEventOne
from async.main import LOG_KEY_FORMAT,INDEX_KEY_FORMAT,\
                       HEAD_KEY_FORMAT,TAIL_KEY_FORMAT,TASK_NAME
                       
                       
from userstore.models import MobileUser                       
                       

MAX_KEYS = 100

class LogTaskHandler(webapp.RequestHandler):
    def get(self):
        # logging.info("I AM PROCESSING A TASK")
        # update a list of counters across the various dimensions
        account_name = self.request.get("account_name")

        head_key = HEAD_KEY_FORMAT%dict(account_name=account_name)
        head_index = memcache.get(head_key) or 1 # starts at 1 by default
        head_index = int(head_index)
        
        tail_key = INDEX_KEY_FORMAT%dict(account_name=account_name)
        tail_index = int(memcache.get(tail_key))
        
        logging.info("start: %s stop: %s"%(head_index,tail_index))
        
        if head_index <= tail_index:
            counter_dict = {}      
            start = head_index
            # paginate the keys
            while start <= tail_index: 
                stop = start + MAX_KEYS - 1 if (start+MAX_KEYS-1) < tail_index else tail_index
                keys = [LOG_KEY_FORMAT%dict(account_name=account_name,log_index=i) 
                         for i in range(start,stop+1)]
        
                logging.info("we have %d keys %s"%(len(keys),keys))
                # grab logs from memcache         
                data_dicts = memcache.get_multi(keys)   
        
                logging.info("%s"%[k for k,d in data_dicts.iteritems() if d])
                
                def update_count(dimension_one,dimension_two,date_hour,attribute,req=None,incr=1):
                    # logging.info("update_count %s %s"%(dimension_one,dimension_two))
                    key = Counter.get_key_name(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
                    
                    if not key in counter_dict:
                      counter_dict[key] = Counter(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
                    
                    # logging.info("key: %s"%key)
                    if attribute:
                      setattr(counter_dict[key],attribute,getattr(counter_dict[key],attribute)+incr) # counter[key].attribute += incr
                    if req:      
                      counter_dict[key].reqs.append(req)

                # iterate through log lines and update appropriate counters
                # logging.info("data: %s"%data_dicts)
                # logging.info("we have %d log lines"%len(data_dicts))    

                for k,d in data_dicts.iteritems():
                    if d:
                        uid = d['uid']
                        dim2l1 = d['dim2l1']
                        dim1l1 = d.get('dim1l1',None)
                    
                        req = d.get('req',None)
                        req = int(req) if req else None
                        
                        inst = d.get('inst',None)
                        inst = int(inst) if inst else None
                    
                        req = "%s.%s"%(req,inst)
                        
                    
                        appid = d.get('appid',None)
                    
                        clk = d.get('clk',None)
                        conv = d.get('conv',None)
                        
                        t = int(float(d['t']))
                        hour = t-t%3600
                        date_hour = datetime.datetime.fromtimestamp(hour)
                    
                        # attach on teh request id once per log line
                        update_count(dim1l1,dim2l1,date_hour,None,req)
                        update_count(None,dim2l1,date_hour,None,req)
                        update_count(dim1l1,None,date_hour,None,req)
                        
                        
                        if clk:
                            # increment click count
                            update_count(dim1l1,dim2l1,date_hour,'count_three',None)
                            update_count(None,dim2l1,date_hour,'count_three',None)
                            update_count(dim1l1,None,date_hour,'count_three',None)
                        elif conv: 
                            # increment conv count
                            update_count(dim1l1,dim2l1,date_hour,'count_four',None)
                            update_count(None,dim2l1,date_hour,'count_four',None)
                            update_count(dim1l1,None,date_hour,'count_four',None)
                        else:
                            # increment impresssions
                            if dim1l1:
                                # adunit-creative impression
                                update_count(dim1l1,dim2l1,date_hour,'count_two',None)
                                # creative impression
                                update_count(dim1l1,None,date_hour,'count_two',None)
                                # adunit impression
                                update_count(None,dim2l1,date_hour,'count_two',None)
                            
                            # increment request for adunit
                            update_count(None,dim2l1,date_hour,'count_one',None)
                            update_count(dim1l1,dim2l1,date_hour,'count_one',None)
                            
                        
                            # params = {'udid':uid,'adunit':dim2l1,'creative':dim1l1,'time':t,'appid':t}
                            # t = Task(params=params,method='GET')
                            # t.add('async-user-queue-01')
                    else:
                        logging.error("NO value for key %s exists"%k)    
            
            
                start += MAX_KEYS # update the next "page"    

            ### DO A LITTLE CLEANUP TO ENSURE WE DON'T MISS THE LAST VALUE            
            last_data = data_dicts.get(keys[-1],None)
            # if there is data that means that the last index was fully written
            if last_data:
                memcache.set(head_key,tail_index+1)
            # if there isn't data that means the next worker needs to work on it    
            else:
                memcache.set(head_key,tail_index)    
                    
        
            logging.info("we have %d counters"%len(counter_dict))    
            
            # datastore put        
            def increment_counter(counter):
                # datastore get
                key_name = counter.key().name()
                obj = Counter.get_by_key_name(key_name)
                if obj:
                    obj += counter
                else:
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
                                      ('/_ah/queue/async-log-queue-01', LogEventOne),
                                      ('/_ah/queue/async-log-queue-02', LogEventOne),
                                      ('/_ah/queue/async-log-queue-03', LogEventOne),
                                      ('/_ah/queue/async-log-queue-04', LogEventOne),
                                      ('/_ah/queue/async-log-queue-05', LogEventOne),
                                      ('/_ah/queue/async-log-queue-06', LogEventOne),
                                      ('/_ah/queue/async-log-queue-07', LogEventOne),
                                      ('/_ah/queue/async-log-queue-08', LogEventOne),
                                      ('/_ah/queue/async-log-queue-09', LogEventOne),
                                      ('/_ah/queue/async-log-queue-10', LogEventOne),                                      
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()