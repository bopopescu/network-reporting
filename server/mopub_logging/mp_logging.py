import logging
import time
import datetime
import random

from common.utils import helpers 
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from publisher.query_managers import AdUnitContextQueryManager
from reporting import models as reporting_models

REQ_EVENT = 0
IMP_EVENT = 1
CLK_EVENT = 2
CONV_EVENT = 3
INAPP_EVENT = 4

TASK_QUEUE_NAME = 'bulk-log-processor'
TASK_QUEUE_NAME_FORMAT = 'bulk-log-processor-%02d'
NUM_TASK_QUEUES = 10

LOG_KEY_FORMAT_OLD = 'k:%(account_name)s:%(time)s:%(log_index)02d'
INDEX_KEY_FORMAT_OLD = 'k:%(account_name)s:%(time)s'


LOG_KEY_FORMAT = 'k:%(account_name)s:%(account_shard)02d:%(time)s:%(log_index)02d'
INDEX_KEY_FORMAT = 'k:%(account_name)s:%(account_shard)02d:%(time)s'
TASK_NAME = 't-%(account_name)s-%(account_shard)02d-%(time)s' # note time will be bucketed

TIME_BUCKET = 100
TIME_BUFFER = 10
SHARD_INTERVAL = 10
MEMCACHE_ALIVE_TIME = 0#6*TIME_BUCKET

REQ_QUEUE_NAME = "network-request-%02d"
NUM_REQ_QUEUES = 10


INAPP_QUEUE_NAME = 'inapp-recorder-%02d'
NUM_INAPP_QUEUS = 1

MAX_TASK_ADDS = 100

def log(request,event,adunit=None,creative=None,manager=None,adunit_id=None,creative_id=None,udid=None,user_agent=None,testing=False):
    # if this is the second request because of a 
    # native failure we just bail in order to 
    # Note if logging an adnetwork request, we pass
    # in request = None.
    if request:
        exclude_creatives = request.get_all("exclude")
        if exclude_creatives:
            return    

    # get parameters from the request or args
    adunit_id = adunit_id 
    if adunit:
        adunit_id = adunit_id or str(adunit.key())
    creative_id = creative_id 
    if creative:
        creative_id = creative_id or str(creative.key()) 
    
    if request:
        adunit_id = adunit_id or request.get('id', None)
        creative_id = creative_id or request.get('cid', None)
        udid = udid or request.get('udid', None)
        request_id = request.get('reqcnt',None)
        instance_id = request.get('inst',None)
        country_code = helpers.get_country_code(user_agent=request.headers['User-Agent'])            
        revenue = request.get('rev',None)
    else:
        request_id = None
        instance_id = None
        country_code = helpers.get_country_code(user_agent=user_agent)
        revenue = None
    
    # if trying to record the request of a adunit and creative
    # i.e. request of a network creative
    # we add a "fire-and-forget" taskqueue entry so that the
    # data shows up in the apache-style request logs    
    if adunit_id and creative_id and event == REQ_EVENT:
        logging.info("fire and forget--adunit: %s creative:%s"%(adunit_id,creative_id))
        task = taskqueue.Task(params=dict(id=adunit_id, cid=creative_id, udid=udid or '', ua=user_agent),
                              method='GET',
                              url='/m/req')
        queue_num = random.randint(0,NUM_REQ_QUEUES-1)                      
        queue_name = REQ_QUEUE_NAME%queue_num

        try:
            task.add(queue_name)
        except Exception, e:
            logging.warning(e)
                
        
    # get account name from the adunit
    if not adunit:
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)
        adunit = adunit_context.adunit
    
    account = adunit.account
    account_name = str(account.key())
        
    account_shard = _get_shard_num(account,adunit_id,creative_id)
    
    # calculate time bucket
    now = time.time()
    time_bucket = int(now)/TIME_BUCKET # maybe divide by 10 for every second
    
    
    # get the new index for this account and time bucket
    index_key = INDEX_KEY_FORMAT%dict(account_name=account_name,account_shard=account_shard,time=time_bucket)
    log_index = memcache.incr(index_key,initial_value=0) # starts at 1
    
    logging_data = dict(event=event,
                        adunit=adunit_id.replace(r"\'",""), # cleanup for mobile web
                        creative=creative_id,
                        country=country_code,
                        revenue=revenue,
                        now=now,
                        udid=udid,
                        req=request_id,
                        inst=instance_id)
    
    # bail early if the memcache increment failed
    if log_index is None or log_index == '': 
        return
    
    # put the log data into appropriate place
    log_key = LOG_KEY_FORMAT%dict(account_name=account_name,account_shard=account_shard,time=time_bucket,log_index=log_index)
    memcache.set(log_key,logging_data,time=MEMCACHE_ALIVE_TIME)
    
    # send to appropriately named task_queue
    task_name = TASK_NAME%dict(account_name=account_name.replace('_','1X--X1'), # must escape '_' regex: [a-zA-Z0-9-]{1,500}$   
                               account_shard=account_shard,
                               time=time_bucket)

    # because we have limited task queue API calls we only try adding
    # to the queue up to MAX_TASK_ADDS time, most are dupes anyway                           
    if log_index > MAX_TASK_ADDS:
        return
        
    try:
        account_bucket = hash(account_name)%NUM_TASK_QUEUES
        task_queue_name = TASK_QUEUE_NAME_FORMAT%account_bucket
        logging.info('\n\ntask: %s\n queue: %s eta:%s\n\n'%(task_name,
                                                    task_queue_name,
                                                    _get_execution_datetime(account_shard,time_bucket)))
        t = taskqueue.Task(name=task_name,params={'account_name':account_name,
                                                  'time':time_bucket,
                                                  'account_shard':account_shard},
                                          eta=_get_execution_datetime(account_shard,time_bucket),
                                          method='GET')
        if not testing:
            t.add(task_queue_name)
    except taskqueue.TaskAlreadyExistsError:
        logging.info("task %s already exists"%task_name)
    except Exception, e:    
        logging.warning(e)
        
def _get_time_bucket_start(time_bucket):
    # time_bucket = the current time bucket
    # TIME_BUCKET = the time size of a bucket
    return time_bucket*TIME_BUCKET       
    
def _get_execution_datetime(account_shard,time_bucket):
    time_bucket_start = _get_time_bucket_start(time_bucket)
    execution_time = time_bucket_start + TIME_BUCKET + TIME_BUFFER + SHARD_INTERVAL*account_shard
    return datetime.datetime.fromtimestamp(execution_time)
        

def _get_shard_num(account,adunit_id,creative_id):
    """
        Returns the 0 indexed shard number for the account based on 
        the adunit and creative combo
    """
    account_num_shards = account.number_shards or 1
    # simply return 0 if there is only one shard
    if account_num_shards == 1: return 0
    # otherwise do a mod on the hash of (adunit_id+creative_id)
    hash_string = '%s:%s'%(adunit_id or '',creative_id or '')
    return hash(hash_string)%account_num_shards

# seperated for cleanliness temporarily
def log_inapp_purchase(request, event, udid, receipt, mobile_appid=None):
    """simply a wrapper for placing in a queue"""
    task = taskqueue.Task(params=dict(udid=udid, receipt=receipt, mobile_appid=mobile_appid, time=time.time()),
                          method='POST',
                          url='/m/purchase_txn')
    queue_num = random.randint(0,NUM_INAPP_QUEUS-1)                      
    queue_name = INAPP_QUEUE_NAME%queue_num
    
    try:
        task.add(queue_name)
    except Exception, e:
        logging.error(e)
    