#!/usr/bin/python
import time
import sys
import os
import time
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
from reports.models import Report
from reports.aws_reports.report_exceptions import (ReportParseError, 
                                                   BlobUploadError,
                                                   S3Error,
                                                   ReportPutError,
                                                   ReportNotifyError,
                                                   ReportException,
                                                   NoDataError,
                                                   )
from reports.aws_reports.report_message_handler import ReportMessageHandler
from reports.aws_reports.helpers import log


################## PID Stuff ######################
f = open("/tmp/poller.pid", 'w')
f.write('%s' % os.getpid())
f.close()


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
REPORT_QUEUE = 'report_queue'

def default_exc_handle(e):
    log("Encountered exception: %s" % e)
    tb_file = open('/home/ubuntu/tb.log', 'a')
    tb_file.write("\nERROR---\n%s" % time.time())
    traceback.print_exc(file=tb_file)
    tb_file.close()

def main_loop():
    report_queue = SQS_CONN.create_queue(REPORT_QUEUE)
    rep_handler = ReportMessageHandler(report_queue)
    # Links jobs to messages
    job_msg_map = {}
    # Links jobs to previous steps completed, useful for waiting jobflows
    job_step_map = {}
    # Count for a job as to how many times it has failed
    fail_dict = {}
    # List of messages to delete from SQS
    to_del = []
    setup_remote_api()
    while True:
        try:
            # Throws no unhandled errors
            rep_handler.handle_messages()
            # Throws some errors if BlobStore is busy//down
            rep_handler.handle_working_jobs()
            # Maybe Throws something
            rep_handler.kill_waiting_jobflows()
            time.sleep(10)
        except ReportException, e:
            report_failed(e.report_key)
            default_exc_handle(e)
        except Exception, e:
            default_exc_handle(e)

if __name__ == '__main__':
    main_loop()
