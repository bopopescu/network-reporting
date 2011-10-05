from __future__ import with_statement

import datetime
import logging
import random
import uuid

from google.appengine.api import files
from google.appengine.api import taskqueue
from google.appengine.runtime import apiproxy_errors

from common.utils.timezones import Pacific_tzinfo


INSTANCE_ID = str(uuid.uuid1())

# flushes either after MAX_LINES_BEFORE_FLUSH or 
# MAX_TIME_BEFORE_FLUSH has elapsed since last flush
# whichever is the first

MAX_LINES_BEFORE_FLUSH = 10000
MAX_TIME_BEFORE_FLUSH = 60 # seconds

FILE_QUEUE_NAME = 'file-finalizer-%02d'
NUM_FILE_QUEUES = 1

class LogService(object):
    def __init__(self, blob_file_name="apache", flush_lines=MAX_LINES_BEFORE_FLUSH, flush_time=MAX_TIME_BEFORE_FLUSH):
        self.blob_file_name = blob_file_name
        self.flush_lines = flush_lines
        self.flush_timer = flush_time
        self.lines = []
        self.last_flush = datetime.datetime.now()
    
    def log(self, line):
        self.lines.append(line)
        
        if self._should_flush():
            try:
                self.flush()
            except apiproxy_errors.OverQuotaError:
                logging.error("Over quota a bit")
            except:
                logging.error("wtf")
            
    def _should_flush(self):
        """
        Logic to determine how frequently we should 
        flush to disk
        """
        enough_lines = len(self.lines) >= self.flush_lines        
        now = datetime.datetime.now()
        next_flush = self.last_flush + datetime.timedelta(seconds=MAX_TIME_BEFORE_FLUSH)
        enough_time_elapsed =  now > next_flush # bool 
        return enough_lines or enough_time_elapsed    
    
    def flush(self):
        """Flushes the log lines to a file"""
        file_name, blob_file_name, current_time = _get_file_names_and_time(self.blob_file_name)

        # open the file and append all new lines together
        with files.open(file_name, 'a') as f:
            f.write('\n'.join(self.lines)+'\n')

        self._did_flush(file_name, blob_file_name, current_time)    
    
    def _did_flush(self, file_name, blob_file_name, current_time):
        """
        Hook for all post flush behavior
        """
        # clear cache of lines
        self.lines = []
        # update last flush 
        self.last_flush = datetime.datetime.now()    
        # finalize the file so that it can be readable
        # this is an appengine specific problem
        # because files start as writeable then 
        # go on to be reable, but first must be finalized
        self._finalize_when_appriorate(file_name,
                                       blob_file_name, 
                                       current_time)
                
    def _finalize_when_appriorate(self, file_name, blob_file_name, current_time):
        """
        Schedule the file to be finalized at the beginning of the next hour (with a buffer)
        """
        # by using task_names we ensure that each file is only finalized once
        task_name = ('t-'+blob_file_name+'-'+INSTANCE_ID).replace('_','1X--X1') # must escape '_' because not allowed in task names
        execution_time = self._get_execution_time(current_time)
        task = taskqueue.Task(name=task_name, 
                              params=dict(file_name=file_name),
                              method='GET',
                              url='/files/finalize',
                              eta=execution_time,)
        # get the appropriate queue shard                      
        queue_num = random.randint(0,NUM_FILE_QUEUES-1)                      
        queue_name = FILE_QUEUE_NAME%queue_num
        try:
            task.add(queue_name)
        except taskqueue.TaskAlreadyExistsError:
            logging.info("task %s already exists"%task_name)
        except Exception, e:    
            logging.warning(e)
        
    def _get_execution_time(self, current_time):
        """
        Get's the execution time which is just the next hour
        (e.g. for both 13:03, 13:43 the execution time is 14:00)
        """
        current_hour = datetime.datetime(year=current_time.year,
                                         month=current_time.month,
                                         day=current_time.day,
                                         hour=current_time.hour,
                                         tzinfo=Pacific_tzinfo())
        
        execution_time = current_hour + datetime.timedelta(hours=1,minutes=15)                                 
        return execution_time
            
def _get_file_names_and_time(blob_file_name):
    """
    Returns the filename based on the current hour
    and the current instance ID
    """    
    # creates the current time in PST
    current_time = datetime.datetime.now(Pacific_tzinfo())
    file_name, blob_file_name = _get_file_names_for_time(current_time, blob_file_name)
    
    return file_name, blob_file_name, current_time
    
# mapping of human reable file names to 
# to appengine file names     
FILE_NAME_FROM_TIME_DICT = {}   
 
def _get_file_names_for_time(t, blob_file_name):
    """
    Returns appengine internal file name and the human 
    readable file name for the input time.
    """
    
    blob_file_name = get_blob_name_for_time(t, blob_file_name)    

    # if not in the cache put it in there
    if not blob_file_name in FILE_NAME_FROM_TIME_DICT:
        # appengine internal file name                                                  
        file_name = files.blobstore.create(
                            mime_type="text/plain",
                            _blobinfo_uploaded_filename=blob_file_name+'.log')
        FILE_NAME_FROM_TIME_DICT[blob_file_name] = file_name

    return FILE_NAME_FROM_TIME_DICT[blob_file_name], blob_file_name    
    
def get_blob_name_for_time(t, blob_file_name="apache"):
    # 2011050215 for 3pm May 2, 2011 PST
    hour_str = t.strftime('%Y%m%d%H')

    # human readable file name with timestamp
    # NOTE: all instances have the same human readable
    # file name for a given hour
    blob_file_name += "-%(hour)s"%dict(hour=hour_str)    
    return blob_file_name
        
# creates the singleton for this instance
logger = LogService()