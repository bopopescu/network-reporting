import logging
import time

from google.appengine.api import memcache
from google.appengine.api import taskqueue

from publisher.query_managers import AdUnitQueryManager

REQ_EVENT = 0
IMP_EVENT = 1
CLK_EVENT = 2
CONV_EVENT = 3

TASK_QUEUE_NAME = 'bulk-log-processor'

LOG_KEY_FORMAT = 'k:%(account_name)s:%(time)s:%(log_index)02d'
INDEX_KEY_FORMAT = 'k:%(account_name)s:%(time)s'
TASK_NAME = 't-%(account_name)s-%(time)s' # note time will be bucketed

TIME_BUCKET = 10
MEMCACHE_ALIVE_TIME = 6*TIME_BUCKET

def log(request,event,adunit=None,manager=None):

    # get parameters from the request
    adunit_id = request.get('id',None)
    creative_id = request.get('cid',None)
    udid = request.get('udid',None)
    request_id = request.get('reqcnt',None)
    instance_id = request.get('inst',None)

    # get account name from the adunit
    adunit_qmanager = manager or AdUnitQueryManager(adunit_id)
    adunit = adunit or adunit_qmanager.get_adunit()
    
    account_name = str(adunit.account.key())
    
    # calculate time bucket
    now = time.time()
    time_bucket = int(now)/TIME_BUCKET # maybe divide by 10 for every second
    
    
    # get the new index for this account and time bucket
    index_key = INDEX_KEY_FORMAT%dict(account_name=account_name,time=time_bucket)
    log_index = memcache.incr(index_key,initial_value=0) # starts at 1
    
    logging_data = dict(event=event,
                        adunit=adunit_id,
                        creative=creative_id,
                        now=now,
                        udid=udid,
                        req=request_id,
                        inst=instance_id)
    
    # put the log data into appropriate place
    log_key = LOG_KEY_FORMAT%dict(account_name=account_name,time=time_bucket,log_index=log_index)
    memcache.set(log_key,logging_data,time=MEMCACHE_ALIVE_TIME)
    logging.info("just put %s=%s"%(log_key,logging_data))
    
    # send of appropriately named task_queue
    task_name = TASK_NAME%dict(account_name=account_name,time=time_bucket)
    logging.info('task: %s'%task_name)
    
    try:
        t = taskqueue.Task(name=task_name,params={'account_name':account_name,'time':time_bucket},countdown=TIME_BUCKET*2,method='GET')
        t.add(TASK_QUEUE_NAME)
    except taskqueue.TaskAlreadyExistsError:
        logging.info("task %s already exists"%task_name)
