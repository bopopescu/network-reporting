import datetime
import logging
import sys
import time
import traceback
import urllib

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

# from appengine_django import LoadDjango
# LoadDjango()

from google.appengine.datastore import entity_pb
from google.appengine.ext import db
from google.appengine.api import files
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp
from google.appengine.ext.blobstore import BlobInfo
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp.util import run_wsgi_app

from common.utils import helpers
from common.utils import simplejson

from mopub_logging import mp_logging
from mopub_logging import log_service

from reporting import models as r_models
from reporting import query_managers


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
      
      if retry_count > 6: return # bail early
      
      
      task_name = self.request.headers.get('X-AppEngine-TaskName',None)
      queue_name = self.request.headers.get('X-AppEngine-QueueName',None)
      
      memcache_stats_start = memcache.get_stats()
      memcache_stats = None
      # grab parameters from the message of the task
      account_name = self.request.get("account_name")
      account_shard = self.request.get("account_shard")
      time_bucket = int(self.request.get("time"))
      

      head_index = 1 # starts at one for a particular time_bucket

      # get the last index for a given time bucket
      
      # for a brief moment there will be tasks that were put in without an associated shard
      if account_shard is None or account_shard == '':
          tail_key = mp_logging.INDEX_KEY_FORMAT_OLD%dict(account_name=account_name,time=time_bucket)
      else:
          tail_key = mp_logging.INDEX_KEY_FORMAT%dict(account_name=account_name,
                                                      account_shard=int(account_shard),
                                                      time=time_bucket)
      tail_index_str = memcache.get(tail_key)
      if not tail_index_str:
          memcache_stats = memcache_stats or memcache.get_stats()
      tail_index = int(tail_index_str or MAX_TAIL)


      if account_name == "agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww":
          logging.error("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
          logging.error("MEMCACHE STATS: %s"%memcache_stats_start)
      else:
          logging.info("account: %s time: %s start: %s stop: %s"%(account_name,time_bucket,head_index,tail_index))
          logging.info("MEMCACHE STATS: %s"%memcache_stats_start)
           

      stats_dict = {}      
      start = head_index
      # paginate the keys
      memcache_misses = 0
      
      while start <= tail_index: 
          # get another MAX_KEYS or go to the end
          stop = start + MAX_KEYS - 1 if (start+MAX_KEYS-1) < tail_index else tail_index
          
          # if this is an old task we don't use the shard to make the keys
          if account_shard is None or account_shard == '':
              keys = [mp_logging.LOG_KEY_FORMAT_OLD%dict(account_name=account_name,time=time_bucket,log_index=i) 
                       for i in range(start,stop+1)]
          else:
              keys = [mp_logging.LOG_KEY_FORMAT%dict(account_name=account_name,account_shard=int(account_shard),time=time_bucket,log_index=i) 
                       for i in range(start,stop+1)]

          logging.info("we have %d keys (start:%s stop:%s)"%(len(keys),start,stop))
          
          # grab logs from memcache         
          data_dicts = memcache.get_multi(keys) 
          current_memcache_misses = (stop - start+1) - len(data_dicts)  
          memcache_misses += current_memcache_misses
          if memcache_misses:
              memcache_stats = memcache_stats or memcache.get_stats()
          # logging.info("Memcache misses: %d"%current_memcache_misses)

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
          stats_to_put = stats_dict.values()
          
          if account_name == "agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww":
              try:
                  mail.send_mail_to_admins(sender="olp@mopub.com",
                                           subject="WTF",
                                           body="len: %s\n%s"%(len(stats_to_put), 
                                                [(str(s._advertiser), str(s._publisher), s.country, s.impression_count) for s in stats_to_put if str(s.country) == 'US']))
              except Exception, e:
                  logging.error("MAIL ERROR: %s",e)
                                                 
          query_manager.put_stats(stats_to_put)
          total_stats = query_manager.all_stats_deltas
      # if the transaction is too large then we split it up and try again    
      # except db.BadRequestError:
      #     async_put_models(account_name,stats_dict.values(),MAX_PUT_SIZE)
      except:
          if retry_count > -1:
              exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
              base_number_of_stats = len(stats_dict.values())
              total_stats = query_manager.all_stats_deltas
              number_of_stats = len(total_stats)
              max_countries = max([len(stat.get_countries()) for stat in total_stats])
              
              mail.send_mail_to_admins(sender="olp@mopub.com",
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
          
          mail.send_mail_to_admins(sender="olp@mopub.com",
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
    
class FinalizeHandler(webapp.RequestHandler):
    def post(self):
        return self.get(self)

    def get(self):
        file_name = self.request.get('file_name')
        files.finalize(file_name)

class DownloadLogsHandler(webapp.RequestHandler):
    def post(self):
        return self.get(self)
    
    def get(self, LIMIT=100):
        date_hour_string = self.request.get('dh')
        limit = int(self.request.get('limit', LIMIT))
        start_time_stamp = self.request.get('start_time', None)
        start_key = self.request.get('start_key', None)
        
        # date_hour_string = YYYYMMDDHH
        year = int(date_hour_string[:4])
        month = int(date_hour_string[4:6])
        day = int(date_hour_string[6:8])
        hour = int(date_hour_string[8:10])
        
        date_hour = datetime.datetime(year=year, 
                                      month=month,
                                      day=day,
                                      hour=hour)
        
        filename = log_service.get_blob_name_for_time(date_hour) + '.log'
        blob_infos = BlobInfo.all().filter('filename =',filename)
        if start_time_stamp:
            start_time = datetime.datetime.fromtimestamp(float(start_time_stamp))
            blob_infos = blob_infos.filter('creation >=', start_time).order('creation')

        if start_key:
            blob_infos = blob_infos.filter('__key__ >=', db.Key(start_key))
            
        
        # fetch the objects from DB
        blob_infos = blob_infos.fetch(limit+1)
        
        blob_keys = [bi.key() for bi in blob_infos]
        
        # if there are limit + 1 entries returned
        # notify the API user where to start next
        if len(blob_infos) > limit:
            next_creation_time_stamp = time.mktime(blob_infos[-1].creation.timetuple())
            next_key_name = blob_infos[-1].key()
        else:
            next_creation_time_stamp = None
            next_key_name = None
        
        response_dict = dict(urls=['/files/serve/%s'%urllib.quote(str(bk)) for bk in blob_keys[:-1]])
        if next_creation_time_stamp:
            response_dict.update(start_time=str(next_creation_time_stamp))
        if next_key_name:
            # makes pseudo BlobInfo key
            # next_key is actually a BlobKey which is the key_name for the BlobInfo
            next_key = db.Key.from_path(BlobInfo.kind(), str(next_key_name), namespace='')
            response_dict.update(start_key=str(next_key))
        
        self.response.out.write(simplejson.dumps(response_dict))

class ServeLogHandler(blobstore_handlers.BlobstoreDownloadHandler):
    """Actually serves the file"""
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = BlobInfo.get(resource)
        self.send_blob(blob_info)
        
        
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
                                      ('/files/finalize', FinalizeHandler),
                                      ('/files/download', DownloadLogsHandler),
                                      ('/files/serve/([^/]+)?', ServeLogHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
