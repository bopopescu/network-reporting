import logging
import os
import pickle
import sys
import time
import traceback
try:
    import json
except:
    import simplejson as json

from datetime import datetime, timedelta

try:
    from multiprocessing import Process, Pipe
except:
    pass

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

############### Boto Imports ###############
from boto.emr.connection import EmrConnection
from boto.emr.step import StreamingStep
from boto.s3.connection import S3Connection as s3
from boto.s3.key import Key

############### Mopub Imports ###############
from reports.aws_reports.helpers import (upload_file,
                                         setup_remote_api,
                                         build_puts,
                                         get_waiting_jobflow,
                                         default_exc_handle,
                                         gen_random_fname,
                                         JOBFLOW_NAME,
                                         LOG_URI,
                                         log,
                                         )
from reports.aws_reports.report_mapper import MAPPER_P1, MAPPER_P2
from reports.aws_reports.messages import MessageHandler
from reports.aws_reports.parse_utils import gen_report_fname, parse_msg
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY
from reports.aws_reports.report_exceptions import (ReportParseError,
                                                   BlobUploadError,
                                                   S3Error,
                                                   ReportPutError,
                                                   ReportNotifyError,
                                                   ReportException,
                                                   NoDataError,
                                                   MRSubmitError,
                                                   )
from reports.models import Report
MY_DIR = os.path.split(os.path.abspath(__file__))[0]
TEST_DATA_DIR = os.path.join(MY_DIR, 'tests/test_data')
TEST_PARTS_DIR = os.path.join(MY_DIR, 'tests/test_data/parts')

############### set up S3 stuff ###############
S3_CONN = s3(AWS_ACCESS_KEY, AWS_SECRET_KEY)
BUCK = S3_CONN.get_bucket('mopub-aws-logging')

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs/AAreports'

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/%s_%s_%s_report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'
PARSE_UTILS = '/parse_utils.py#parse_utils.py'

MAPPER_DIR = 'reports_code0'
MAPPER_NAME = 'mapper_%s_%s_%s--%s-%s.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'
SHORT_ACCT_DIR = 'account_data'

NUM_INSTANCES = 1
MASTER_INSTANCE_TYPE = 'm1.large'
SLAVE_INSTANCE_TYPE = 'm1.xlarge'
KEEP_ALIVE = True

MAX_RETRIES = 3
FINISHED_FILE = '/mnt/finished_reports/finished_%s.rep'
FINISHED_FILE_JSON = '/mnt/finished_reports/finished_%s.json'

STEP_NAME = "Generate_report_%s-%s-%s-%s"

MAX_MSGS = 5
########### SET UP COMPLETION STATUS ########
CSTEP_NAME = 'CSTEP%s'
UPLOAD = CSTEP_NAME % 0
BLOB_KEY_PUT = CSTEP_NAME % 1
PARSE = CSTEP_NAME % 2
POST_PARSE_BLOB_PUT = CSTEP_NAME % 3
POST_PARSE_PUT = CSTEP_NAME % 4 # I wanted to call this P3 but I took pity
NOTIFY = CSTEP_NAME % 5

######## FAILURE REASONS ########
FAILURE = 'REPFAIL%s'
NODAT = FAILURE % 0
MRFAILURE = FAILURE % 1
# I'll do it later
OTHER = FAILURE % 2

PARSING = 'parsing'
PARSE_ERROR = 'parsingerror'

# All steps must be completed to do things
MESSAGE_COMPLETION_STEPS = [UPLOAD, BLOB_KEY_PUT, PARSE, POST_PARSE_BLOB_PUT, POST_PARSE_PUT, NOTIFY]

TEST_FAIL_TIMEOUT = 2
DEFAULT_TIMEOUT = 15
PARSE_TIMEOUT = 15

############## PIPELINES!!!! ########
MSG = '%s|%s'
########### Message Types ############
OBJ = 'OBJECT'
STEP_STATUS_CHANGE = 'SSCHG'
MSG_DATA = 'MSGDATA'

VALID_TYPES = (OBJ, STEP_STATUS_CHANGE, MSG_DATA)
############## Constants ###################
BACKOFF_FACTOR = 2

############ SETUP LOGGING SHIT ##############
# Suppress non-critical boto messages
logging.getLogger('boto').setLevel(logging.CRITICAL)

class ReportMessage(object):

    def __init__(self, msg):
        self.msg = msg
        self.dim1, self.dim2, self.dim3, self.start, self.end, self.report_key, self.account, self.timestamp = parse_msg(msg)
        self.step_name = STEP_NAME % (self.dim1, self.dim2, self.dim3, self.timestamp)

        self.fname = '%s' % gen_report_fname(self.dim1, self.dim2, self.dim3, self.start, self.end)
        self.mapper_name = MAPPER_NAME % (self.dim1, self.dim2, self.dim3, self.start_str, self.end_str)


    def get_mapper(self):
        """ Builds a mapper for this message if need be.
        Returns True if mapper previously existed, False otherwise """
        if BUCK.get_key(MAPPER_DIR + '/' + self.mapper_name) is None:
            mapper_args = dict(dim1 = self.dim1,
                               dim2 = self.dim2,
                               dim3 = self.dim3,
                               start = self.start_str,
                               end = self.end_str,
                               )
            map_key = Key(BUCK)
            map_key.key = MAPPER_DIR + '/' + self.mapper_name
            map_str = (MAPPER_P1 % mapper_args + MAPPER_P2)
            map_key.set_contents_from_string(map_str)
            map_key.close()
            return False
        else:
            return True


    def __key(self):
        return (self.dim1, self.dim2, self.dim3, self.start, self.end, self.report_key, self.account, self.timestamp)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        if not type(self) == type(other):
            return False
        else:
            return self.__key() == other.__key()

    def __cmp__(self, other):
        return cmp(str(self), str(other))

    def __repr__(self):
        repr_str = 'ReportMessage(Dims:(%s, %s, %s), Range(%s, %s), Report(%s), Account(%s), %s)'
        keys = self.__key()
        new_keys = []
        for key in keys:
            if isinstance(key, datetime):
                new_keys.append(key.strftime('%y%m%d'))
            else:
                new_keys.append(key)
        return repr_str % tuple(new_keys)

    @property
    def dims(self):
        return (self.dim1, self.dim2, self.dim3)

    @property
    def start_str(self):
        return self.start.strftime('%y%m%d')
    @property
    def end_str(self):
        return self.end.strftime('%y%m%d')

class ReportMessageHandler(MessageHandler):
    """ Usage:
        rmh = ReportMessageHandler(<report_messgae_queue>)
        while True:
            rmh.handle_messages()
            rmh.handle_working_jobs()
            rmh.kill_waiting_jobflows()
            rmh.cleanup()
            time.sleep(10)
            """


    def __init__(self, queue, testing=False):

        if not testing:
            setup_remote_api()
        self.queue = queue
        self.testing = testing
        self.to_del = []
        self.jobid_message_map = {}
        self.msg_failures = {}
        self.jobid_creations = {}
        self.emr_conn = EmrConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

        # Map of how far completed this Message is
        self.message_completion_statuses = {}
        # Map of timeouts for each step
        self.message_step_timeouts = {}
        # Map of blobs for messages that failed after blob uploading
        self.message_blob_keys = {}
        # Map of blobs of the HTML data for reports
        self.message_html_blob_keys = {}
        # Map of datas for messages that failed after parsing
        self.message_data = {}
        # Map of messages to reports
        self.message_report = {}
        # Map of messages to their parse pipes
        self.message_parse_pipe = {}
        # Map of messages to the time until they should be retried
        self.message_mr_backoff = {}

    def init_message(self, message):
        """ When starting to process a message, init its steps
        and timers for when it's done"""
        self.message_completion_statuses[message] = {}
        self.message_step_timeouts[message] = {}
        self.message_blob_keys[message] = None
        self.message_html_blob_keys[message] = None
        self.message_data[message] = None
        self.message_report[message] = None
        self.message_parse_pipe[message] = None

        for step in MESSAGE_COMPLETION_STEPS:
            self.message_completion_statuses[message][step] = False
            self.message_step_timeouts[message][step] = None
        # Try/except because it's possible that there were no failures
        # and the dict entry doesn't exist
        try:
            # MR job added, don't need this anymore
            del(self.message_mr_backoff[message])
        except Exception:
            pass

    def init_message_pipe(self, message):
        p_pipe, c_pipe = Pipe()
        self.set_message_parse_pipe(message, p_pipe)
        return c_pipe



    def backoff_message(self, message):
        secs = 10 * (BACKOFF_FACTOR ** self.msg_failures[message])
        self.message_mr_backoff[message] = datetime.now() + timedelta(seconds = secs)

    def backed_off(self, message):
        # This is going to throw a key error if it hasn't failed yet, instead
        # of checking if it's in the dict, just know that if this errors
        # it's because it hasn't failed so just return True
        try:
            return datetime.now() < self.message_mr_backoff[message]
        except Exception:
            return True

    @property
    def message_maps(self):
        return (self.message_completion_statuses,
                self.message_step_timeouts,
                self.message_blob_keys,
                self.message_html_blob_keys,
                self.message_data,
                self.message_report,
                )

    def message_completion_cleanup(self, message):
        """ dels all the dict entries, leaks suck"""
        if self.testing and self.message_blob_keys[message]:
            os.remove(os.path.join(TEST_DATA_DIR, self.message_blob_keys[message]))
        if self.testing and self.message_html_blob_keys[message]:
            os.remove(os.path.join(TEST_DATA_DIR, self.message_html_blob_keys[message]))
        del(self.message_completion_statuses[message])
        del(self.message_step_timeouts[message])
        del(self.message_blob_keys[message])
        del(self.message_html_blob_keys[message])
        del(self.message_data[message])
        del(self.message_report[message])
        del(self.message_parse_pipe[message])

    def set_message_parse_pipe(self, message, p_conn):
        self.message_parse_pipe[message] = p_conn

    def get_message_parse_pipe(self, message):
        return self.message_parse_pipe[message]

    def listen_to_parse_pipe(self, message, step, i):
        pipe_conn = self.get_message_parse_pipe(message)
        # There is data
        while pipe_conn.poll():
            msg_type = pipe_conn.recv()
            data = pipe_conn.recv()
            self.handle_pipe_message(message, msg_type, data, i)


    def handle_pipe_message(self, message, msg_type, data, i):
        if msg_type == STEP_STATUS_CHANGE:
            step, state = data
            # If the state is "True" and we're completed, then
            # do the default completion handling
            if state in (True, 'True'):
                self.mark_completed(message, step, i)
            else:
                self.set_completed(message, step, state)
        elif msg_type == MSG_DATA:
            self.message_data[message] = data


    def get_message_report(self, message):
        """ Gets a report for a message locally if we have it,
        otherwise go to GAE """

        if message not in self.message_report or self.message_report[message] is None:
            rep = Report.get(message.report_key)
            self.message_report[message] = rep

        return self.message_report[message]

    def set_message_report(self, message, val):
        """ sets the value of a message report """
        self.message_report[message] = val

    def completed(self, message, step):
        """Message step completion getter"""
        if step == PARSE:
            val = self.message_completion_statuses[message][step]
            if val == PARSING or val == PARSE_ERROR:
                return False
            else:
                return val
        else:
            return self.message_completion_statuses[message][step]

    def set_completed(self, message, step, cmpltd):
        """Message step completion setter"""
        self.message_completion_statuses[message][step] = cmpltd


    def parsing_message(self, message):
        return self.message_completion_statuses[message][PARSE] == PARSING

    def parse_error(self, message):
        return self.message_completion_statuses[message][PARSE] == PARSE_ERROR

    def step_timeout(self, message, step):
        """Message step timeout getter"""
        return self.message_step_timeouts[message][step]

    def set_step_timeout(self, message, step, timeout):
        """Message step timeout setter"""
        self.message_step_timeouts[message][step] = timeout

    def step_timedout(self, message, steps):
        if not isinstance(steps, list):
            steps = [steps]
        for step in steps:
            if self.completed(message, step):
                continue
            elif self.step_timeout(message, step) and self.step_timeout(message, step) < datetime.now():
                return True
        #logger.info("Timeout: %s" % self.message_step_timeouts[message][step])
        #logger.info("now: %s" % datetime.now())
        return False

    @property
    def working_jobids(self):
        """ Jobflowids that have messages being EMR'd """
        return self.jobid_message_map.keys()


    def cleanup(self):
        """ Removes all pointers to empty lists, deletes all dict entries
        that point to things no longer in use, etc. """
        pass

    def upload_and_get_key(self, message):

        if self.testing:
            fname = gen_random_fname(suffix='.dat')
            final = open(TEST_DATA_DIR + '/' + fname, 'w')
            for file in os.listdir(TEST_PARTS_DIR):
                try:
                    name, ext = file.split('.')
                except:
                    continue
                if ext == 'part':
                    open_file = open(TEST_PARTS_DIR + '/' + file, 'r')
                    for line in open_file:
                        final.write(line)
                    open_file.close()
            final.close()
            return fname

        report_dir = SHORT_ACCT_DIR + '/%s/reports/'
        report_dir = report_dir % message.account
        out_file = report_dir + message.fname
        log("Output file: %s" % out_file)
        files = BUCK.list(prefix = out_file + '/part')
        finished_file = open(FINISHED_FILE % message.report_key, 'w')
        for ent in files:
            ent.get_contents_to_file(finished_file)
        finished_file.close()
        finished_file = open(FINISHED_FILE % message.report_key)
        try:
            blob_key = upload_file(finished_file)
        except:
            raise BlobUploadError(message = message)
        finished_file.close()
        return blob_key

    def upload_html_blob_and_get_key(self, message):
        report = self.get_message_report(message)
        json_blob = json.dumps(dict(data=report.html_data))

        if self.testing:
            fname = gen_random_fname(suffix='.dat')
            final = open(TEST_DATA_DIR + '/' + fname, 'w')
            final.write(json_blob)
            final.close()
            return fname

        finished_json_file = open(FINISHED_FILE_JSON % message.report_key, 'w')
        finished_json_file.write(json_blob)
        finished_json_file.close()
        finished_json_file = open(FINISHED_FILE_JSON % message.report_key)
        try:
            blob_key = upload_file(finished_json_file)
        except:
            raise BlobUploadError(message = message)
        finished_json_file.close()
        os.remove(FINISHED_FILE_JSON % message.report_key)
        return blob_key


    def notify_failure(self, message, reason):
        if reason == NODAT:
            fail_text = 'No Data'
        else:
            fail_text = 'Failed'

        try:
            rep = self.get_message_report(message)
            rep.status = fail_text
            rep.put()
            rep.notify_failure(reason)
        except Exception:
            log("Report notify failed", level = 'exception')
            return
        if reason not in [NODAT, MRFAILURE]:
            self.message_completion_cleanup(message)

    def test_finalize(self, message):
        report = self.get_message_report(message)
        report.status = 'Success'
        report.put()


    def kill_waiting_jobflows(self):
        """ For the jobflows in the creation map, kill those that have been idle for just nearly an hour """
        jobflows = self.get_jobflow_statuses(self.existing_jobflows)
        if jobflows is None:
            return
        for jobflow in jobflows:
            jobid = jobflow.jobflowid
            dt = datetime.now() - self.jobid_creations[str(jobid)]
            minutes = (dt.seconds/60)
            # Waiting and almost 1 hour since creation
            if jobflow.state == u'WAITING' and minutes % 60 >= 50:
                self.emr_conn.terminate_jobflow(jobid)
                del(self.jobid_creations[str(jobid)])

    @property
    def existing_jobflows(self):
        return self.jobid_creations.keys()


    def handle_messages(self, force_no_data=False, force_submit_error=False, force_delete_error=False):
        """
        Args: None
        Rets: True if messages were handled, False if no messages handled
        Throws: None
        """
        # Don't allowing testing stuff if not testing (Just in case)
        if not self.testing:
            force_no_data = force_submit_error = force_delete_error = False
            timeout = 10
        else:
            timeout = 1
        if self.queue.count() > 0:
            logging.warning("Messages!")
            msgs = self.queue.get_messages(MAX_MSGS, visibility_timeout = timeout)
            if len(msgs) == 0:
                # Actually no messages, return False
                return False
            for msg in msgs:
                log("Message from Queue:%s" % msg.get_body())
                message = ReportMessage(msg)

                if not self.backed_off(message):
                    continue

                try:
                    self.handle_message(message,
                                        force_no_data = force_no_data,
                                        force_submit_error = force_submit_error)

                # Commence Robust Exception Handling
                except NoDataError, e:
                    # No data, can't retry
                    log("No Data Error on %s", e.report_message)
                    self.to_del.append(e.report_message)
                    self.notify_failure(e.report_message, NODAT)
                    if not self.testing:
                        default_exc_handle(e)

                except MRSubmitError, e:
                    # Failed too many times, stop retrying (delete from the queue)
                    log("Submit Error on %s" % e.report_message)
                    if self.msg_failures[e.report_message] >= MAX_RETRIES:
                        log("Message %s has failed the maximum number of times" % e.report_message)
                        self.to_del.append(e.report_message)
                        self.notify_failure(e.report_message, MRFAILURE)

                    self.msg_failures[e.report_message] += 1
                    self.backoff_message(e.report_message)
                    if not self.testing:
                        default_exc_handle(e)

                # Successfully added to EMR, init it for completion
                self.init_message(message)

            # Delete handled messages from the queue
            for i in range(len(self.to_del)):
                msg = self.to_del.pop(0)
                log("Deleting: %s" % msg)
                if force_delete_error or not self.queue.delete_message(msg.msg):
                    log("Failed to delete message")
                    self.to_del.append(msg)
        else:
            return False
        return True

    def get_jobflow_statuses(self, ids):
        if not ids:
            return None
        retry = 0
        while retry < 5:
            try:
                jobflows = self.emr_conn.describe_jobflows(jobflow_ids = ids)
                return jobflows
            except Exception:
                # Probs just a rate limit issue, sleep and try again
                retry += 1
                time.sleep(5 + (2 * retry))
        return None

    def handle_working_jobs(self, jobflows = None, force_failure = False, fail_step=None, fail_msg=None):
        """
            For all jobs that have messages being handled, see if they're done.  If they are,
            process them

            Args: jobflows - list of jobflows to handle, only if testing
            Rets: None
            Throws: None
            """
        # Get the status of the jobflows we are using
        if not self.testing:
            force_failure = False
            fail_step = None
            fail_msg = None
            jobflows = self.get_jobflow_statuses(self.working_jobids)

        if jobflows is None:
            return
        # Each jobflow can have multiple steps.  Ideally we only ever have one jobflow
        # but it's conceivable that we have two
        for jobflow in jobflows:
            log("Handling: %s" % jobflow.jobflowid)
            self.handle_jobflow(jobflow,
                                force_failure = force_failure,
                                fail_step=fail_step,
                                fail_msg=fail_msg)

    def handle_jobflow(self, jobflow, force_failure = False, fail_step=None, fail_msg=None):

        jobid = jobflow.jobflowid
        if not self.jobid_message_map.has_key(jobid):
            return
        messages = self.jobid_message_map[jobid]
        log("Messages for this jobid: %s" % messages)
        completed_steps = [step.name for step in jobflow.steps if step.state == u'COMPLETED']
        failed_steps = [step.name for step in jobflow.steps if step.state == u'FAILED']
        finished_messages = [msg for msg in messages if msg.step_name in completed_steps]
        failed_messages = [msg for msg in messages if msg.step_name in failed_steps]

        # Finished messages is a list of messages that correspond to the FINISHED
        # EMR jobs for this jobflow
        for message in finished_messages:
            try:
                self.on_success(message, jobid, force_failure, fail_step, fail_msg)

            except BlobUploadError, e:
                message = e.report_message
                log("Blob upload error for %s" % message)
                jobflowid = e.jobflowid
                #logger.warning("Message: %s  JobFlowID: %s had a BlobUploadError" % (message, jobflowid))
                self.set_message_report(message, None)
                if self.step_timedout(message, [UPLOAD, POST_PARSE_BLOB_PUT]):
                    log("TIMED OUT ON UPLOAD")
                    self.mark_failed(message, jobflowid)

            except ReportPutError, e:
                # Put failed.
                message = e.report_message
                log("Report Put error for %s" % message)
                jobflowid = e.jobflowid
                #logger.warning("Message: %s  JobFlowID: %s had a ReportPutError" % (message, jobflowid))
                self.set_message_report(message, None)
                if self.step_timedout(message, [BLOB_KEY_PUT, POST_PARSE_PUT]):
                    log("TIMED OUT ON PUT")
                    self.mark_failed(message, jobflowid)

            # This is a child process that has failed
            # THE ONLY THING THAT THROWS THESE ARE CHILD PROCESSES!!!!!
            except ReportParseError, e:
                message = e.report_message
                log("Parse error for %s" % message)
                jobflowid = e.jobflowid
                #logger.warning("Message: %s  JobFlowID: %s had a ReportParseError" % (message, jobflowid))
                self.set_message_report(message, None)
                # No longer parsing, and it failed
                self.set_completed(message, PARSE, False)
                log("Should be resetting stuff to parse again")
                log("Step completion statuses for message %s\t%s" % (message, self.message_completion_statuses[message]))
                if self.step_timedout(message, PARSE):
                    log("TIMED OUT ON PARSE")
                    self.mark_failed(message, jobflowid)
                # Super kill child process

            except ReportNotifyError, e:
                # Notifying Failed
                message = e.report_message
                log("Notify error for %s" % message)
                jobflowid = e.jobflowid
                #logger.warning("Message: %s  JobFlowID: %s had a ReportNotifyError" % (message, jobflowid))
                self.set_message_report(message, None)
                if self.step_timedout(message, NOTIFY):
                    log("TIMED OUT ON NOTIFY")
                    self.mark_failed(message, jobflowid)

        for message in failed_messages:
            self.on_failure(message, jobid)

        if len(self.jobid_message_map[jobid]) == 0:
            del(self.jobid_message_map[jobid])

    def on_failure(self, message, jobid):
        # Failed too many times, notify
        if self.msg_failures[message] > MAX_RETRIES:
            self.notify_failure(message, 'Failed')
        # Try again
        else:
            self.queue.write(message.msg)
            self.msg_failures[message] += 1

        self.jobid_message_map[jobid] = [msg for msg in self.jobid_message_map[jobid] if msg != message]

    def mark_failed(self, message, jobid):
        self.notify_failure(message, 'Failed')
        self.jobid_message_map[jobid] = [msg for msg in self.jobid_message_map[jobid] if msg != message]

    def on_success(self, message, jobid, force_failure = False, fail_step=None, fail_msg=None):
        #logger.info("Message: %s success, handling" % message)
        # Set the timeout for the first step
        if self.step_timeout(message, MESSAGE_COMPLETION_STEPS[0]) is None:
            dt = timedelta(minutes = 15)
            if self.testing:
                dt = timedelta(seconds = TEST_FAIL_TIMEOUT)
            self.set_step_timeout(message, MESSAGE_COMPLETION_STEPS[0], datetime.now() + dt)

        if not self.testing:
            force_failure = False
            fail_step = None
            fail_msg = None

        # There are 5 distinct steps to finalizing, all of which can fail.  If any one fails
        # the on_success is retried.  There is no reason to try to do something again that
        # has succeeded, so don't
        log("Step completion statuses for message %s\t%s" % (message, self.message_completion_statuses[message]))
        log("Now:%s\nStep timeouts for message %s\t%s" % (time.time(), message, self.message_step_timeouts[message]))
        for i, step in enumerate(MESSAGE_COMPLETION_STEPS):
            if step == PARSE:
                if self.parsing_message(message):
                    self.listen_to_parse_pipe(message, step, i)
                    log("Parsing message")
                    return
                elif self.parse_error(message):
                    log("Parsing error")
                    raise ReportParseError(message = message, jobflowid = jobid)

            if self.completed(message, step):
                continue
            else:
                #logger.info("Handling step %s for message %s" % (step, message))
                # If the handling succeeds mark it as such and do the next one
                # Otherwise stop processing this message
                if self.handle_completion_step(message, step, jobid, force_failure, fail_step, fail_msg):
                    self.mark_completed(message, step, i)
                    # The child is the only one that will return True, kill it after we've
                    # marked the step as completed
                else:
                    return

        # Cleanup since we're done!
        # I realize we're iterating for every one, but this is the right way.
        self.jobid_message_map[jobid] = [msg for msg in self.jobid_message_map[jobid] if not msg == message]
        self.message_completion_cleanup(message)


    def handle_completion_step(self, message, step, jobflowid, force_failure=False, fail_step=None, fail_msg=None):
        """ Do what is needed for the specified step.

        THIS IS WHERE ERRORS (should be) ARE THROWN """
        # Upload step, throws BlobUploadErrors
        if step == UPLOAD:
            log("Handling upload for %s" % message)
            # This guy throws
            blob_key = self.upload_and_get_key(message)

            if force_failure and fail_step == step:
                # Cleanup before we throw otherwise it'll never get cleaned
                os.remove(os.path.join(TEST_DATA_DIR, blob_key))
                raise BlobUploadError(message = message, jobflowid = jobflowid)
            self.message_blob_keys[message] = blob_key
            return True

        # First put, throws ReportPutErrors
        elif step == BLOB_KEY_PUT:
            log("Handling first put for %s" % message)
            try:
                rep = self.get_message_report(message)
                if  self.testing:
                    rep.test_report_blob = open(os.path.join(TEST_DATA_DIR, self.message_blob_keys[message]), 'r').read()
                else:
                    rep.report_blob = self.message_blob_keys[message]

                if force_failure and fail_step == step:
                    raise ReportPutError(message = message, jobflowid = jobflowid)

                rep.put()
            except:
                raise ReportPutError(message = message, jobflowid = jobflowid)
            return True

        # Parse error, throws ReportParseErrors
        # SPAWNS CHILD THREAD (because it takes so damn long)
        elif step == PARSE:
            log("Handling parse for %s" % message)

            if self.testing:
                rep = self.get_message_report(message)
                data = rep.parse_report_blob(rep.test_report_blob, {}, testing = self.testing)
                if force_failure and fail_step == step:
                    raise ReportParseError(message = message, jobflowid = jobflowid)
                self.message_data[message] = data
                return True

            # Indicate that we are currently working on this step
            self.set_completed(message, step, PARSING)
            rep = self.get_message_report(message)
            c_conn = self.init_message_pipe(message)

            sub_proc = Process(target = parse_process, args=(rep, message, c_conn))
            sub_proc.start()

            return False

        elif step == POST_PARSE_BLOB_PUT:
            log("Handling data blob put for %s" % message)
            blob_key = self.upload_html_blob_and_get_key(message)
            if force_failure and fail_step == step:
                os.remove(os.path.join(TEST_DATA_DIR, blob_key))
                raise BlobUploadError(message = message, jobflowid = jobflowid)

            self.message_html_blob_keys[message] = blob_key
            return True

        # Second put, throws ReportPutErrors
        elif step == POST_PARSE_PUT:
            log("Handling second put for %s" % message)
            try:
                rep = self.get_message_report(message)

                if force_failure and fail_step == step:
                    if fail_msg is not None:
                        if fail_msg == message:
                            raise ReportPutError(message = message, jobflowid = jobflowid)
                    else:
                        raise ReportPutError(message = message, jobflowid = jobflowid)

                rep.data = self.message_data[message]
                rep.html_data_blob = self.message_html_blob_keys[message]
                rep.completed_at = datetime.now()
                rep.status = 'Completed'
                rep.put()
            except Exception, e:
                raise ReportPutError(message = message, jobflowid = jobflowid)
            return True

        # Notify, throws ReportNotifyErrors
        elif step == NOTIFY:
            log("Handling notify for %s" % message)
            try:
                rep = self.get_message_report(message)
                if self.testing:
                    if force_failure and fail_step == step:
                        raise ReportNotifyError(message = message, jobflowid = jobflowid)
                else:
                    rep.notify_complete()
            except Exception, e:
                logging.warning(e)
                raise ReportNotifyError(message = message, jobflowid = jobflowid)

            return True


    def mark_completed(self, message, step, i):
        """ Mark the specified step for the given message as completed,
        set the timeout for the next step """
        self.set_completed(message, step, True)
        # Last step, don't set a new timeout
        if i+1 == len(MESSAGE_COMPLETION_STEPS):
            return
        # Not last step, set timeout for next step
        else:
            next_step = MESSAGE_COMPLETION_STEPS[i+1]
            now = datetime.now()
            dt = timedelta(minutes = DEFAULT_TIMEOUT)
            if next_step == PARSE:
                dt = timedelta(minutes = PARSE_TIMEOUT)
            if self.testing:
                dt = timedelta(seconds = TEST_FAIL_TIMEOUT)
            timeout = now + dt
            self.set_step_timeout(message, next_step, timeout)

    def handle_message(self, message, force_no_data = False, force_submit_error = False):
        # Add a failure dict. This must be done before any possible failures
        if not self.msg_failures.has_key(message):
            self.msg_failures[message] = 0
        # If processed don't do anything with it
        if message in self.to_del:
            return
        # For testing
        if force_no_data:
            raise NoDataError('No inputs', message)
        if force_submit_error:
            raise MRSubmitError("Error adding job to EMR", message)

        #logger.info("Handling %s" % message.msg.get_body())
        if message.get_mapper():
            log("Reusing previously generated mapper for %s" % message)
        else:
            log("Generating mapper for %s" % message)

        if not self.testing:
            # Submit the job
            jobid = self.submit_job(message)

            # List of messages being handled by this jobflow
            if not self.jobid_message_map.has_key(jobid):
                self.jobid_message_map[jobid] = []
            self.jobid_message_map[jobid].append(message)

        # Notify that it has been handled
        self.to_del.append(message)





    def submit_job(self, message):
        input_dir, relevant_inputs, output_dir = build_puts(message.start, message.end, message.account)
        if len(relevant_inputs) == 0:
            # No data, can't retry :(
            raise NoDataError('No inputs', message)
        output = output_dir + '/' + message.fname
        log("Submit output %s" % output)
        gen_report_step = StreamingStep(
                name = message.step_name,
                mapper = REPORTING_S3_CODE_DIR + '/' + message.mapper_name,
                reducer = LOG_REDUCER,
                cache_files = [REPORTING_S3_CODE_DIR + PARSE_UTILS],
                input = input_dir,
                output = output,
                )
        steps_to_add = [gen_report_step]
        success = False
        count = 0
        while success == False:
            try:
                jobid = get_waiting_jobflow(self.emr_conn, self.existing_jobflows)
                success = True
            except Exception, e:
                logging.warning(e)
                logging.warning("Trying to get waiting jobflows failed")
                time.sleep(2 ** count)
                count += 1
                success = False
        instances = 21
        try:
            if jobid:
                self.emr_conn.add_jobflow_steps(jobid, steps_to_add)
            else:
                jobid = self.emr_conn.run_jobflow(
                    name = JOBFLOW_NAME,
                    steps = steps_to_add,
                    log_uri = LOG_URI,
                    num_instances = instances,
                    main_instance_type = MASTER_INSTANCE_TYPE,
                    subordinate_instance_type = SLAVE_INSTANCE_TYPE,
                    keep_alive=KEEP_ALIVE,
                    enable_debugging=True,
                    )
                # Created a new job.  Record the time of creation
                self.jobid_creations[str(jobid)] = datetime.now()
        # Boto can fail for a few reasons, other random erorrs.
        # Catch all of them and raise a simple one
        except Exception, e:
            default_exc_handle(e)
            raise MRSubmitError('Error adding job to EMR', message)

        return jobid

def parse_process(rep, message, pipe_conn):
    try:
        obj_dimkeys = rep.batch_get_objs(rep.report_blob.open())
        log("Obj_dimkeys: %s" % obj_dimkeys)
        data = rep.parse_report_blob(rep.report_blob.open(), obj_dimkeys)
        pipe_send_message(pipe_conn, MSG_DATA, data)
        pipe_send_message(pipe_conn, STEP_STATUS_CHANGE, (PARSE, True))
    except Exception, e:
        default_exc_handle(e)
        pipe_send_message(pipe_conn, STEP_STATUS_CHANGE, (PARSE, PARSE_ERROR))
        return


def pipe_send_message(pipe, type, data):
    if type not in VALID_TYPES:
        return False
    pipe.send(type)
    pipe.send(data)
    return True

