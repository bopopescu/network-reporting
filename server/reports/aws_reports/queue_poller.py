#!/usr/bin/python
import time, sys, os, time, urllib2
from datetime import datetime

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
from parse_utils import gen_report_fname, parse_msg
from parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY
from report_mr_submitter import submit_job

from reports.models import Report


################### S3 Stuff ######################
S3_CONN = s3(AWS_ACCESS_KEY, AWS_SECRET_KEY)
BUCK = S3_CONN.get_bucket('mopub-aws-logging')

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs/AAreports'

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'

SHORT_ACCT_DIR = 'account_data'

################## Other AWS Stuff ###################
MAX_MSGS = 10
SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
EMR_CONN = EmrConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

################## GAE Uploading Stuff ##############
BACKEND = 'stats-updater'
APP = 'mopub-inc'
HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)
URL_HANDLER_PATH = '/offline/get_upload_url'
UPDATE_STATS_HANDLER_PATH = '/offline/update_stats'

################## Constants ###################
LOG_FORMAT = "%s:\t%s\n"

def log(mesg):
    my_log = open('/home/ubuntu/poller.log', 'a')
    my_log.write(LOG_FORMAT % (int(time.time()), mesg))
    my_log.close()

def auth_func():
    return 'olp@mopub.com', 'N47935'

def setup_remote_api():
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)


def job_failed(state):
    if state == u'FAILED':
        return True
    else:
        return False

def job_succeeded(state):
    if state in [u'COMPLETED', u'WAITING']:#, u'TERMINATED', u'WAITING']:
        return True
    else:
        return False

def upload_file(fd):

    register_openers()
    datagen, headers = multipart_encode({'file' : fd})

    upload_url_req = urllib2.Request(HOST + URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_req).read()

    file_upload_req = urllib2.Request(upload_url, datagen, headers)
    blob_key = urllib2.urlopen(file_upload_req).read()
    return blob_key


def finalize_report(rep):
    log("Finalizing %s" % rep)
    report = Report.get(rep)
    report.report_blob = blob_key
    data = report.parse_report_blob(report.report_blob.open())
    report.data = data
    report.completed_at = datetime.now()
    report.put()
    report.notify_complete()
    sys.exit(0)

def notify_appengine(fname, msg):
    d1, d2, d3, start, end, rep, acct = parse_msg(msg)
    report_dir = SHORT_ACCT_DIR + '/%s/reports/'
    report_dir = report_dir % acct
    file = report_dir + fname
    files = BUCK.list(prefix = file + '/part')
    f = open('reports/finished_%s.rep' % rep, 'a')
    for ent in files:
        ent.get_contents_to_file(f)
    f.close()
    f = open('reports/finished_%s.rep' % rep)
    blob_key = upload_file(f)
    # Fork this shit because I don't like to wait
    pid = os.fork()
    # Fork is hot shit, look up what it does, but basically pid == True means parent, otherwise child
    if pid:
        return
    else:
        finalize_report(rep)
    


def main_loop():
    report_queue = SQS_CONN.create_queue('report_queue')
    job_msg_map = {}
    fail_dict = {}
    to_del = []
    setup_remote_api()
    while True:
        if report_queue.count() > 0:
            msgs = report_queue.get_messages(MAX_MSGS, visibility_timeout = 0)
            for msg in msgs:
                log("Processing %s" % msg.get_body())
                if msg in to_del:
                    continue
                # Start the MR job
                job_id, fname = submit_job(*parse_msg(msg))
                if not fail_dict.has_key(msg.get_body()):
                    fail_dict[msg.get_body()] = 0
                # Save the msg w/ the job id
                job_msg_map[job_id] = (fname, msg)
                # Remove the msg from the Q
                to_del.append(msg)
        else:
            log("No Messages")

        for i in range(len(to_del)):
            msg = to_del.pop(0)
            if not report_queue.delete_message(msg):
                to_del.append(msg)
             
        processed_jobs = []
        if job_msg_map.keys():
            try:
                statuses = EMR_CONN.describe_jobflows(jobflow_ids = job_msg_map.keys())
            except Exception, e:
                # Prob a rate limit issue, just sleep and start the loop over
                time.sleep(15)
                continue
            for job in statuses:
                log("Job: %s in state: %s" % (job.jobid, job.state))
                fname, msg = job_msg_map[str(job.jobflowid)]
                if job_failed(job.state):
                    fail_dict[msg.get_body()] += 1
                    report_queue.write(msg)
                    if fail_dict[msg.get_body()] <= 3:
                        processed_jobs.append(job.jobflowid)
            # Notify GAE when a report is finished
                elif job_succeeded(job.state):
                    notify_appengine(fname, msg)
                    processed_jobs.append(job.jobflowid)



        # Remove Completed/Failed jobs from the map so we don't
        # Repeatedly notify GAE//Continuously add a job that 
        # failed once
        for job_id in processed_jobs:
            del(job_msg_map[job_id])
        time.sleep(10)


if __name__ == '__main__':
    main_loop()
