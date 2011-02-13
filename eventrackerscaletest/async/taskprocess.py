import logging
import datetime
import sys
import traceback

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import memcache
from google.appengine.api.taskqueue import Task
from google.appengine.api import mail

from event.models import db

from counters.models import Counter

from async.main import LogEventOne
from async.main import ACCOUNT_KEY_FORMAT,\
                       REQ_KEY_FORMAT,\
                       IMP_KEY_FORMAT,\
                       CLK_KEY_FORMAT,\
                       CNV_KEY_FORMAT,\
                       BASE_KEY_FORMAT
                       
from async.main import TIME_BUCKET                       
                       
from userstore.models import MobileUser   

MAX_KEYS = 100

def increment_counter(counter,time_bucket):
    # datastore get
    counter.reqs = [time_bucket]
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
        time_bucket = self.request.get("time_bucket")

        logging.info('account name: %s'%account_name)
        
        account_key = ACCOUNT_KEY_FORMAT%dict(account_name=account_name)
        
        logging.info('account key: %s'%account_key)
        
        
        counter_keys = memcache.get(account_key)
        
        counter_dict = {}    
        type_dict = dict(R='count_one',I='count_two',C='count_three',A='count_four')
          
        for dim2l1_dim1l1 in counter_keys:
            dim2l1,dim1l1 = dim2l1_dim1l1.split(':') # adunit, creative
            keys = []
            for type_ in type_dict:
              for one,two in [(dim1l1,dim2l1),('',dim2l1),(dim1l1,'')]:
                  key = BASE_KEY_FORMAT%dict(type=type_,
                                              dim_one_level_one=one,
                                              dim_two_level_one=two,
                                              time_bucket=time_bucket)
                  keys.append(key)
        logging.info("keys: %s"%keys) # should be 12 keys   
        delta_dict = memcache.get_multi(keys)
        for k,v in delta_dict.iteritems():
          logging.info("get key: %s"%k)
          if v:
            v = int(v)
            type_,dimension_one,dimension_two,time_bucket = k.split(':')
            t = int(time_bucket)*TIME_BUCKET # seconds
            hour = t-t%3600 
            date_hour = datetime.datetime.fromtimestamp(hour)
            attribute = type_dict[type_]
            update_count(counter_dict,dimension_one,dimension_two,date_hour,attribute,req=None,incr=v)
        
        
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
                logging.error()
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