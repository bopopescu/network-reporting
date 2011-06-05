import logging
import datetime
import traceback
import sys

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

# from appengine_django import LoadDjango
# LoadDjango()

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import mail
from google.appengine.api import memcache

from reporting import models as r_models
from reporting import query_managers

from mopub_logging import mp_logging

from common.utils import helpers

from google.appengine.api import taskqueue
from google.appengine.datastore import entity_pb

OVERFLOW_TASK_QUEUE_NAME_FORMAT = "bulk-log-processor-overflow-%02d"
NUM_OVERFLOW_TASK_QUEUES = 3

MAX_KEYS = 100
MAX_TAIL = 1000 # implies max 100 qps

# soft limit
MAX_PUT_SIZE = 8

STATS_MODEL_QUERY_KEY = "sm"

def increment_stats(stats):
    # datastore get
    key_name = stats.key()
    stats_obj = Counter.get_by_key(key_name)
    if stats_obj:
        stats_obj += stats
    else:
        stats_obj = stats    

    # datastore put
    logging.info("putting in key_name: %s value: %s,%s"%(key_name,stats.request_count,stats.impression_count))
    logging.info("putting in key_name: %s NEW value: %s,%s"%(key_name,stats_obj.request_count,stats_obj.impression_count))
    stats_obj.put()
    
def update_stats(stats_dict,publisher,advertiser,date_hour,country,attribute,req=None,revenue=None,incr=1):
    publisher = publisher or None
    advertiser = advertiser or None
    try:
        key = r_models.StatsModel.get_key_name(publisher=publisher,
                                               advertiser=advertiser,
                                               date_hour=date_hour,
                                               country=country)
        if not key in stats_dict:
          stats_dict[key] = r_models.StatsModel(publisher=publisher,
                                                advertiser=advertiser,
                                                date_hour=date_hour,
                                                country=country)

        if attribute:
          # stats_dict[key].attribute += incr
          setattr(stats_dict[key],attribute,getattr(stats_dict[key],attribute)+incr) 
      
          if revenue:
              stats_dict[key].revenue += revenue
        if req:      
          stats_dict[key].reqs.append(req)
    except Exception, e:
        logging.warning("Error in update_stats: %s"%e)      
    
class LogTaskHandler(webapp.RequestHandler):
  def get(self):
      # inspect headers of the task
      retry_count = int(self.request.headers.get('X-AppEngine-TaskRetryCount',"0"))
      task_name = self.request.headers.get('X-AppEngine-TaskName',None)
      queue_name = self.request.headers.get('X-AppEngine-QueueName',None)
      
      memcache_stats_start = memcache.get_stats()
      memcache_stats = None
      # grab parameters from the message of the task
      account_name = self.request.get("account_name")
      time_bucket = int(self.request.get("time"))

      head_index = 1 # starts at one for a particular time_bucket

      # get the last index for a given time bucket
      tail_key = mp_logging.INDEX_KEY_FORMAT%dict(account_name=account_name,time=time_bucket)
      tail_index_str = memcache.get(tail_key)
      if not tail_index_str:
          memcache_stats = memcache_stats or memcache.get_stats()
      tail_index = int(tail_index_str or MAX_TAIL)

      logging.info("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
      logging.info("MEMCACHE STATS: %s"%memcache_stats_start)

      stats_dict = {}      
      start = head_index
      # paginate the keys
      memcache_misses = 0
      
      while start <= tail_index: 
          # get another MAX_KEYS or go to the end
          stop = start + MAX_KEYS - 1 if (start+MAX_KEYS-1) < tail_index else tail_index
          keys = [mp_logging.LOG_KEY_FORMAT%dict(account_name=account_name,time=time_bucket,log_index=i) 
                   for i in range(start,stop+1)]

          logging.info("we have %d keys (start:%s stop:%s)"%(len(keys),start,stop))
          
          # grab logs from memcache         
          data_dicts = memcache.get_multi(keys) 
          current_memcache_misses = (stop - start+1) - len(data_dicts)  
          memcache_misses += current_memcache_misses
          if memcache_misses:
              memcache_stats = memcache_stats or memcache.get_stats()
          logging.info("Memcache misses: %d"%current_memcache_misses)

          for k,d in data_dicts.iteritems():
              if d:
                  uid = d.get('udid',None)
                  adunit = d.get('adunit',None)
                  creative = d.get('creative',None)
                  event = d.get('event',None)

                  req = d.get('req',None)
                  req = int(req) if req else None
                  
                  revenue = d.get('revenue',None)
                  revenue = float(revenue) if revenue else None

                  inst = d.get('inst',None)
                  inst = int(inst) if inst else None

                  req = "%s.%s.%s"%(req,inst,time_bucket)

                  appid = d.get('appid',None)
                  
                  country = d.get('country',None)
                  
                  # calculate the datetime object to hour precision
                  now = int(float(d['now']))
                  hour = now-now%3600
                  date_hour = datetime.datetime.fromtimestamp(hour,
                                                              tz=r_models.Pacific_tzinfo())
                  # attach on the request id once per log line
                  # update_stats(stats_dict,
                  #              publisher=adunit,
                  #              advertiser=None,
                  #              date_hour=date_hour,
                  #              attribute=None,
                  #              req=req)

                  if event == mp_logging.REQ_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,                                   
                                   attribute='request_count')
                  elif event == mp_logging.IMP_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='impression_count',
                                   revenue=revenue)

                  if event == mp_logging.CLK_EVENT:
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='click_count',
                                   revenue=revenue)

                  elif event == mp_logging.CONV_EVENT: 
                      update_stats(stats_dict,
                                   publisher=adunit,
                                   advertiser=creative,
                                   date_hour=date_hour,
                                   country=country,
                                   attribute='conversion_count',
                                   revenue=revenue)

              else:
                  logging.error("NO value for key %s exists"%k)    

          start += MAX_KEYS # proceed to the next "page"    

      query_manager = query_managers.StatsModelQueryManager(account_name)
      try:
          # raise db.BadRequestError('asdf')
          query_manager.put_stats(stats_dict.values())
      # if the transaction is too large then we split it up and try again    
      # except db.BadRequestError:
      #     async_put_models(account_name,stats_dict.values(),MAX_PUT_SIZE)
      except:
          if retry_count > 0:
              exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
              base_number_of_stats = len(stats_dict.values())
              total_stats = query_manager.all_stats_deltas
              number_of_stats = len(total_stats)
              max_countries = max([len(stat.get_countries()) for stat in total_stats])
              
              mail.send_mail(sender="olp@mopub.com",
                            to="bugs@mopub.com",
                            subject="Logging error",
                            body="account: %s retries: %s task name: %s queue name: %s base stats: %s total number of stats: %s max countries: %s \n\n%s"%(account_name,
                                                                                             retry_count,
                                                                                             task_name,
                                                                                             queue_name,
                                                                                             base_number_of_stats,
                                                                                             number_of_stats,
                                                                                             max_countries,
                                                                                             exception_traceback))
              logging.error(exception_traceback)
              raise Exception("need to try transaction again")
      
      # only email if we miss alot (more than .1% or more than 1)      
      if not tail_index_str or (memcache_misses > 1 and float(memcache_misses)/float(tail_index) > 0.001):
          message = "Account: %s time: %s tail: %s misses: %s retry: %s\nmemcache_stats_starts:%s\nmemcache_stats:%s"%(account_name,time_bucket,
                                                                                  tail_index_str,memcache_misses,retry_count,
                                                                                  memcache_stats_start,memcache_stats)
          
          mail.send_mail(sender="olp@mopub.com",
                        to="bugs@mopub.com",
                        subject="Logging error (cache miss)",
                        body=message)
          logging.error(message)
          
class StatsModelPutTaskHandler(webapp.RequestHandler):
    def get(self):
        logging.info("ASDF: %s"%"ASdf")
        return self.post()
    
    def post(self):
        # get the account name
        account_name = self.request.get("account_name")
        next_bucket_size = self.request.get("next_size", MAX_PUT_SIZE)
        query_manager = query_managers.StatsModelQueryManager(account_name)
        
        # get the list of protobufs from the post
        # stats_model_protobufs = self.request.get_all(STATS_MODEL_QUERY_KEY)
        stats_model_json_strings = self.request.get_all(STATS_MODEL_QUERY_KEY)
        # decode the objects
        # logging.info("length: %s"%len(stats_model_protobufs))
        # logging.info("try: %s"%stats_model_protobufs[0])
        
        # stats_models = [db.model_from_protobuf(entity_pb.EntityProto(pb)) 
        #                         for pb in stats_model_protobufs]
        stats_models = [r_models.StatsModel.from_json(jstr) for jstr in stats_model_json_strings]
        try:
            logging.info('trying to put %d models'%len(stats_models))
            query_manager.put_stats(stats_models)
        # if the transaction is too large then we split it up and try again    
        except db.BadRequestError:
            async_put_models(account_name,stats_models,next_bucket_size)

def async_put_models(account_name,stats_models,bucket_size):
    account_bucket = hash(account_name)%NUM_OVERFLOW_TASK_QUEUES
    task_queue_name = OVERFLOW_TASK_QUEUE_NAME_FORMAT%account_bucket
    logging.info('queue: %s'%task_queue_name)
    
    next_bucket_size = bucket_size/2 if bucket_size > 1 else 1
    
    # run in transaction so we atomically "put" all the data chunks
    logging.info('splitting %d models into %d sized chunks'%(len(stats_models),bucket_size))
    
    def _txn():
        for sub_stats in helpers.chunks(stats_models, bucket_size):
            # add sub_stats to the key
            stats_model_json_strings = [sm.to_json() for sm in sub_stats]
            
            t = taskqueue.Task(params={'account_name': account_name,
                                       'next_size': next_bucket_size,
                                       STATS_MODEL_QUERY_KEY: stats_model_json_strings,
                                       },
                               url='/_ah/queue/bulk-log-processor/put',           
                               method='POST',
                               countdown=5)
            t.add(task_queue_name, transactional=False)
    db.run_in_transaction(_txn)        
        
application = webapp.WSGIApplication([('/_ah/queue/bulk-log-processor', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-00', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-01', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-02', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-03', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-04', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-05', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-06', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-07', LogTaskHandler),    
                                      ('/_ah/queue/bulk-log-processor-08', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor-09', LogTaskHandler),
                                      ('/_ah/queue/bulk-log-processor/put', StatsModelPutTaskHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
