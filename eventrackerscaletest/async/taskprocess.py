import logging
import datetime
import traceback
import sys

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task
from event.models import db

from counters.models import Counter

from async.main import LogEventOne
from async.main import LOG_KEY_FORMAT,INDEX_KEY_FORMAT
                       
from userstore.models import MobileUser

MAX_KEYS = 100

def increment_counter(counter,time_bucket):
    # datastore get
    key_name = counter.key().name()
    obj = Counter.get_by_key_name(key_name)
    if obj:
        obj += counter
    else:
        obj = counter    
    # datastore put
    logging.info("putting in key_name: %s value: %s,%s"%(key_name,counter.count_one,counter.count_two))
    logging.info("putting in key_name: %s NEW value: %s,%s"%(key_name,obj.count_one,obj.count_two))
    obj.put()


def update_count(counter_dict,dimension_one,dimension_two,date_hour,attribute,req=None,incr=1):
    # logging.info("update_count %s %s"%(dimension_one,dimension_two))
    dimension_one = dimension_one or None
    dimension_two = dimension_two or None
    key = Counter.get_key_name(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
    
    if not key in counter_dict:
      counter_dict[key] = Counter(dimension_one=dimension_one,dimension_two=dimension_two,date_hour=date_hour)
    
    if attribute:
      setattr(counter_dict[key],attribute,getattr(counter_dict[key],attribute)+incr) # counter[key].attribute += incr
    if req:      
      counter_dict[key].reqs.append(req)

class LogTaskHandler(webapp.RequestHandler):
    def get(self):
        # logging.info("I AM PROCESSING A TASK")
        # update a list of counters across the various dimensions
        account_name = self.request.get("account_name")
        time_bucket = int(self.request.get("time"))

        head_index = 1 # starts at one
        
        # get the last index for a given time bucket
        tail_key = INDEX_KEY_FORMAT%dict(account_name=account_name,time=time_bucket)
        tail_index = int(memcache.get(tail_key))
        
        logging.info("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
        
        counter_dict = {}      
        start = head_index
        # paginate the keys
        while start <= tail_index: 
            # get another MAX_KEYS or go to the end
            stop = start + MAX_KEYS - 1 if (start+MAX_KEYS-1) < tail_index else tail_index
            keys = [LOG_KEY_FORMAT%dict(account_name=account_name,time=time_bucket,log_index=i) 
                     for i in range(start,stop+1)]
    
            logging.info("we have %d keys (start:%s stop:%s)"%(len(keys),start,stop))
            # grab logs from memcache         
            data_dicts = memcache.get_multi(keys)   
            data_values = [v['req'] for v in data_dicts.values()]
            logging.info("data: %s"%data_values)
            
            logging.info("Memcache misses: %d"%(len(keys)-len(data_dicts)))
            
            for k,d in data_dicts.iteritems():
                if d:
                    uid = d['uid']
                    dim2l1 = d['dim2l1']
                    dim1l1 = d.get('dim1l1',None)
                
                    req = d.get('req',None)
                    req = int(req) if req else None
                    
                    inst = d.get('inst',None)
                    inst = int(inst) if inst else None
                
                    req = "%s.%s.%s"%(req,inst,time_bucket)
                    
                    appid = d.get('appid',None)
                
                    clk = d.get('clk',None)
                    conv = d.get('conv',None)
                    
                    t = int(float(d['t']))
                    hour = t-t%3600
                    date_hour = datetime.datetime.fromtimestamp(hour)
                
                    # attach on teh request id once per log line
                    # update_count(counter_dict,dim1l1,dim2l1,date_hour,None,req)
                    # update_count(counter_dict,None,dim2l1,date_hour,None,req)
                    # update_count(counter_dict,dim1l1,None,date_hour,None,req)
                    
                    
                    if clk:
                        # increment click count
                        update_count(counter_dict,dim1l1,dim2l1,date_hour,'count_three',None)
                        update_count(counter_dict,None,dim2l1,date_hour,'count_three',None)
                        update_count(counter_dict,dim1l1,None,date_hour,'count_three',None)
                    elif conv: 
                        # increment conv count
                        update_count(counter_dict,dim1l1,dim2l1,date_hour,'count_four',None)
                        update_count(counter_dict,None,dim2l1,date_hour,'count_four',None)
                        update_count(counter_dict,dim1l1,None,date_hour,'count_four',None)
                    else:
                        # increment impresssions
                        if dim1l1:
                            # adunit-creative impression
                            update_count(counter_dict,dim1l1,dim2l1,date_hour,'count_two',None)
                            # creative impression
                            update_count(counter_dict,dim1l1,None,date_hour,'count_two',None)
                            # adunit impression
                            update_count(counter_dict,None,dim2l1,date_hour,'count_two',None)
                        
                        # increment request for adunit
                        update_count(counter_dict,None,dim2l1,date_hour,'count_one',None)
                        update_count(counter_dict,dim1l1,dim2l1,date_hour,'count_one',None)
                        
                else:
                    logging.error("NO value for key %s exists"%k)    
        
            start += MAX_KEYS # update the next "page"    

        total_counters = len(counter_dict)  
        i = 0  
        for key_name, counter in counter_dict.iteritems():
            try:
                db.run_in_transaction(increment_counter, counter, time_bucket)
            except:
                exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
                mail.send_mail(sender="appenginescaletest@gmail.com",
                              to="nafis@mopub.com",
                              subject="Logging error",
                              body="Succeeded %s of %s\n\n%s"%(i,total_counters,exception_traceback))
                logging.error(exception_traceback)
                raise Exception("need to try transaction again")
            i += 1    
        

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