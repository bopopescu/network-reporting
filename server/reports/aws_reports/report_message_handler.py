import time
import sys
import os
import urllib2
from datetime import datetime
import traceback

sys.path.append("..")
sys.path.append("../..")

sys.path.append("/home/ubuntu/mopub/server")
sys.path.append("/home/ubuntu/mopub/server/reports")
sys.path.append("/home/ubuntu/google_appengine")
sys.path.append("/home/ubuntu/google_appengine/lib/fancy_urllib")
sys.path.append("/home/ubuntu/google_appengine/lib/webob")
sys.path.append("/home/ubuntu/google_appengine/lib/ipaddr")
sys.path.append("/home/ubuntu/google_appengine/lib/antlr3")
sys.path.append("/home/ubuntu/google_appengine/lib/django_1_2")
sys.path.append("/home/ubuntu/google_appengine/lib/yaml/lib")


from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

############### Boto Imports ############### 
from boto.emr.connection import EmrConnection
from boto.sqs.connection import SQSConnection
from boto.emr.step import StreamingStep
from boto.sqs.message import Message
from boto.s3.connection import S3Connection as s3

############### Poster Imports ############### 
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

############### GAE Imports ############### 
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.remote_api import remote_api_stub

############### Mopub Imports ############### 
from reports.aws_reports.messages import Message, MessageHandler
from reports.aws_reports.parse_utils import gen_report_fname, parse_msg
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY
from reports.models import Report
from reports.aws_reports.report_exceptions import (ReportParseError, 
                                                   BlobUploadError,
                                                   S3Error,
                                                   ReportPutError,
                                                   ReportNotifyError,
                                                   ReportException,
                                                   NoDataError,
                                                   MRSubmitError,
                                                   )
from reports.aws_reports.helpers import (upload_file, setup_remote_api, log, build_puts, get_waiting_jobflow, JOBFLOW_NAME)

# Setup the remote API
setup_remote_api()

S3_CONN = s3(AWS_ACCESS_KEY, AWS_SECRET_KEY)
BUCK = S3_CONN.get_bucket('mopub-aws-logging')

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs/AAreports'  

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/%s_%s_%s_report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'
SHORT_ACCT_DIR = 'account_data'

NUM_INSTANCES = 1
MASTER_INSTANCE_TYPE = 'm1.large'
SLAVE_INSTANCE_TYPE = 'm1.large'
KEEP_ALIVE = True

MAX_RETRIES = 3
FINISHED_FILE = '/home/ubuntu/mopub/server/reports/aws_reports/reports/finished_%s.rep'

STEP_NAME = "Generate_report_%s-%s-%s-%s"

MAX_MSGS = 5

def default_exc_handle(e):
    log("Encountered exception: %s" % e)
    tb_file = open('/home/ubuntu/tb.log', 'a')
    tb_file.write("\nERROR---\n%s" % time.time())
    traceback.print_exc(file=tb_file)
    tb_file.close()

class ReportMessage(object):

    def __init__(self, msg):
        self.msg = msg
        self.d1, self.d2, self.d3, self.start, self.end, self.report_key, self.account, self.ts = parse_msg(msg)
        self.start_str = self.start.strftime('%y%m%d')
        self.end_str = self.end.strftime('%y%m%d')
        self.fname = gen_report_fname(self.d1, self.d2, self.d3, self.start, self.end)
        self.step_name = STEP_NAME % (self.d1, self.d2, self.d3, self.ts)

class ReportMessageHandler(MessageHandler):
    """ Usage: 
        rmh = ReportMessageHandler(<report_messgae_queue>)
        while True:
            rmh.handle_messages()
            rmh.handle_working_jobs()
            rmh.kill_waiting_jobflows()
            time.sleep(10)
            """


    def __init__(self, queue, testing=False):
        self.queue = queue
        self.testing = testing
        self.to_del = []
        self.jobid_message_map = {}
        self.msg_failures = {}
        self.jobid_creations = {}
        self.emr_conn = EmrConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

    @property
    def working_jobids(self):
        return self.jobid_message_map.keys()

    def notify_success(self, message):
        report_dir = SHORT_ACCT_DIR + '/%s/reports/'
        report_dir = report_dir % message.account
        file = report_dir + message.fname
        files = BUCK.list(prefix = file + '/part')
        f = open(FINSIHED_FILE % message.report_key, 'w')
        for ent in files:
            ent.get_contents_to_file(f)
        f.close() 
        f = open(FINISHED_FILE % message.report_key)
        blob_key = self.upload_file(f)
        pid = os.fork()
        if pid:
            return
        else:
            retry = 0
            while retry < MAX_RETRIES:
                try:
                    self.finalize_report(message, blob_key)
                    break
                except ReportException, e:
                    # Keep trying!
                    retry += 1
            if retry == MAX_RETRIES:
                self.notify_failure(message, 'Failed')
            sys.exit(0)

    def notify_failure(self, message, reason):
        try:
            rep = Report.get(message.report_key)
            rep.status = reason
            rep.put()
        except:
            return

    def finalize_report(self, message, blob_key):
        report = Report.get(message.report_key)
        report.report_blob = blob_key
        # Put before we parse just in case, this way we still got it
        report.put()
        data = report.parse_report_blob(report.report_blob.open())
        report.data = data
        report.completed_at = datetime.now()
        report.put()
        report.notify_complete()


    def kill_waiting_jobflows(self):
        """ For the jobflows in the creation map, kill those that have been idle for just nearly an hour """
        jobflows = self.get_jobflow_statuses(self.jobid_creations.keys())
        if jobflows is None:
            return
        for jobflow in jobflows:
            jobid = jobflow.jobflowid
            dt = datetime.now() - self.jobid_creations[jobid]
            minutes = (dt.seconds/60)
            # Waiting and almost 1 hour since creation
            if jobflow.state == u'WAITING' and minutes % 60 >= 50:
                self.emr_conn.terminate_jobflow(jobid)
                del(self.jobid_creations[jobid])


    def handle_messages(self, force_no_data=False, force_submit_error=False):
        """
        Args: None
        Rets: None
        Throws: None
        """ 
        # Don't allowing testing stuff if not testing (Just in case)
        if not self.testing:
            force_no_data = force_submit_error = False
        if self.queue.count() > 0:
            msgs = self.queue.get_messages(MAX_MSGS)
            for msg in msgs:
                message = ReportMessage(msg)
                try:
                    self.handle_message(msg, force_no_data = force_no_data, force_submit_error = force_submit_error)
                # Commence Robust Exception Handling 
                except NoDataError, e:
                    # No data, can't retry
                    self.to_del.append(e.message)
                    self.notify_failure(e.message, 'No Data')
                    default_exc_handle(e)
                except MRSubmitError, e:
                    # Failed too many times, stop retrying (delete from the queue)
                    if self.msg_failures[e.message] > MAX_RETRIES:
                        self.to_del.append(e.message)
                        self.notify_failure(e.message, 'Failed')
                    default_exc_handle(e)
                    self.msg_failures[e.message] += 1
                except Exception, e:
                    default_exc_handle(e)
                    continue

            # Delete handled messages from the queue
            for i in range(len(self.to_del)):
                msg = self.to_del.pop(0)
                if not self.queue.delete_message(msg.msg):
                    self.to_del.append(msg)

    def get_jobflow_statuses(self, ids):
        if not ids:
            return None
        retry = 0
        while retry < 5:
            try:
                jobflows = self.emr_conn.describe_jobflows(jobflow_ids = self.working_jobids)
                return jobflows
            except Exception:
                # Probs just a rate limit issue, sleep and try again
                retry += 1
                time.sleep(5 + (2 * retry))
        return None

    def handle_working_jobs(self):
        """ 
            Args: None
            Rets: None
            Throws: Whatever the notify's throw
            """
        # Get the status of the jobflows we are using
        jobflows = self.get_jobflow_statuses(self.working_jobids)
        # Each jobflow can have multiple steps.  Ideally we only ever have one jobflow
        # but it's conceivable that we have two
        if jobflows is None:
            return
        for jobflow in jobflows:
            self.handle_jobflow(jobflow)
    
    def handle_jobflow(self, jobflow):
        jobid = jobflow.jobflowid
        if not self.jobid_message_map.has_key(jobid):
            return
        messages = self.jobid_message_map[jobid]
        completed_steps = [step.name for step in jobflow.steps if step.state == u'COMPLETED']
        failed_steps = [step.name for step in jobflow.steps if step.state == u'FAILED']
        finished_messages = [msg for msg in messages if msg.step_name in completed_steps]
        failed_messages = [msg for msg in messages if msg.step_name in failed_steps]

        # Handle completed messages
        for message in finished_messages:
            self.on_success(message, jobid)

        # Handle failed messages
        for messge in failed_messages:
            self.on_failure(message, jobid)
        
        # This jobflow is exhausted, remove it from the list of working jobids
        if len(self.jobid_message_map[jobid]) == 0:
            del(self.jobid_message_map[jobid])
            
    def on_success(self, message, jobid):
        self.notify_success(message)
        # I realize we're iterating for every one, but this is the right way.
        self.jobid_message_map[jobid] = [msg for msg in self.jobid_message_map[jobid] if msg != message]

    def on_failure(self, message, jobid):
        # Failed too many times, notify
        if self.msg_failures[message] > MAX_RETRIES:
            self.notify_failure(message, 'Failed')
        # Try again
        else:
            self.queue.write(message.msg)
            self.msg_failures[message] += 1
        
        self.jobid_message_map[jobid] = [msg for msg in self.jobid_message_map[jobid] if msg != message]

    def handle_message(self, message, force_no_data = False, force_sumit_error = False):
        # Add a failure dict. This must be done before any possible failures
        if not self.msg_failures.has_key(message):
            self.msg_failures[message] = 0
        # For testing
        if force_no_data:
            raise NoDataError('No inputs', message)
        if force_submit_error:
            raise MRSubmitError("Error adding job to EMR", message)

        log("Handling %s" % message.msg.get_body())
        # If processed don't do anything with it
        if message in self.to_del:
            return

        # Submit the job
        jobid = self.submit_job(message)

        # List of messages being handled by this jobflow
        if not self.jobid_message_map.has_key(jobid):
            self.jobid_message_map[jobid] = []
        self.jobid_message_map[jobid].append(message)

        # Notify that it has been handled
        self.to_del.append(message)
        




    def submit_job(self, message):
        inputs, output_dir = build_puts(message.start, message.end, message.account)
        if len(inputs) == 0:
            # No data, can't retry :(
            raise NoDataError('No inputs', message)
        output = output_dir + '/' + message.fname
        gen_report_step = StreamingStep(
                name = message.step_name,
                mapper = REPORT_MAPPER % (message.d1, message.d2, message.d3),
                reducer = LOG_REDUCER,
                cache_files = [REPORTING_S3_CODE_DIR + '/parse_utils.py#parse_utils.py'],
                input = inputs,
                output = output,
                )
        steps_to_add = [gen_report_step]
        jobid = get_waiting_jobflow(self.emr_conn, self.working_jobids)
        instances = 10
        try:
            if jobid:
                self.emr_conn.add_jobflow_steps(jobid, steps_to_add)
            else:
                jobid = self.emr_conn.run_jobflow(
                    name = JOBFLOW_NAME,
                    steps = steps_to_add,
                    log_uri = LOG_URI,
                    num_instances = instances,
                    master_instance_type = MASTER_INSTANCE_TYPE,
                    slave_instance_type = SLAVE_INSTANCE_TYPE,
                    keep_alive=KEEP_ALIVE,
                    enable_debugging=True,
                    )
                # Created a new job.  Record the time of creation
                self.jobid_creations[jobid] = datetime.now()
        # Boto can fail for a few reasons, other random erorrs.  Catch all of them and raise a simple one
        except Exception, e:
            default_exc_handle(e)
            raise MRSubmitError('Error adding job to EMR', message)

        return jobid
        
