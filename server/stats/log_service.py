from __future__ import with_statement

import datetime
import logging
import random
import sys
import traceback
import uuid

from google.appengine.api import files
from google.appengine.api import taskqueue
from google.appengine.runtime import apiproxy_errors

from common.utils import simplejson
from common.utils.helpers import to_uni, to_ascii
from common.utils.timezones import Pacific_tzinfo


INSTANCE_ID = str(uuid.uuid1())

# flushes either after MAX_LINES_BEFORE_FLUSH or
# MAX_TIME_BEFORE_FLUSH has elapsed since last flush
# whichever is the first

MAX_LINES_BEFORE_FLUSH = 100
MAX_TIME_BEFORE_FLUSH = 60 # seconds

FILE_QUEUE_NAME = 'file-finalizer-%02d'
NUM_FILE_QUEUES = 10


class LogService(object):
    def __init__(self, blob_file_name="apache", flush_lines=MAX_LINES_BEFORE_FLUSH, flush_time=MAX_TIME_BEFORE_FLUSH):
        self.blob_file_name = blob_file_name
        self.flush_lines = flush_lines
        self.flush_timer = flush_time
        self.lines = []
        self.last_flush = datetime.datetime.now()

    def log(self, line):
        # some lines contain non-UTF-8 encoded chars or have invalid bytes
        # clean those by converting all non-unicode lines into unicode with UTF-8 encoding and with invalid bytes replaced
        try:
            line = to_uni(line)
        except Exception, e:
            pass
            # logging.error('%s: %s' % (e, line))

        self.lines.append(line)

        if self._should_flush():
            try:
                self.schedule_flush()
            except apiproxy_errors.OverQuotaError:
                logging.error("Over quota a bit")
            except:
                exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
                # logging.error(exception_traceback)

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


    def schedule_flush(self):
        """Schedules the flushing of log lines to a blobstore file via task queue"""

        # creates the current time in PST
        current_time = datetime.datetime.now(Pacific_tzinfo())

        # create human-readable file name in blobstore based on current time
        blob_file_name = get_blob_name_for_time(current_time, self.blob_file_name)

        self._put_flush_task_on_q(blob_file_name, current_time)


    def _put_flush_task_on_q(self, blob_file_name, current_time):
        """
        Schedule the flushing of lines to file and then finalize it at the beginning of the next hour (with a buffer)
        """

        try:
            # post data is a dict containing the file name in blobstore and its content: the log lines
            post_data = {'blob_file_name': blob_file_name, 'log_lines': self.lines}
            post_data_serialized = simplejson.dumps(post_data)

            task = taskqueue.Task(name=None,
                                  method='POST',
                                  url='/files/finalize',
                                  payload=post_data_serialized)

            # get the appropriate queue shard
            queue_num = random.randint(0, NUM_FILE_QUEUES-1)
            queue_name = FILE_QUEUE_NAME % queue_num

            # put task on queue
            task.add(queue_name)

            # clear cache of lines
            self.lines = []
            # update last flush
            self.last_flush = datetime.datetime.now()
        except taskqueue.TaskAlreadyExistsError:
            logging.info("task %s already exists"%task_name)

        except UnicodeDecodeError, e:
            logging.warning(e)
        except Exception, e:
            exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
            # logging.error(exception_traceback)

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
