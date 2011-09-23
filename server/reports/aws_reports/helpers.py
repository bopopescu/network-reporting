import logging
import os
import time
import traceback


from optparse import OptionParser

from boto.emr.connection import EmrConnection
from boto.emr.step import StreamingStep
from boto.s3.connection import S3Connection

from parse_utils import gen_days, gen_report_fname, get_waiting_jobflow
from parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY, JOBFLOW_NAME
from reports.aws_reports.report_exceptions import (MRSubmitError, ReportException, NoDataError)

############### Poster Imports ############### 
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

############### GAE Imports ############### 
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.remote_api import remote_api_stub

S3_CONN = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
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
    my_log.write(LOG_FORMAT % (time.time(), mesg))
    my_log.close()

def build_puts(start, end, account):
    input_dir = ACCOUNT_DIR + ('/%s/daily_logs' % account)
    output_dir = ACCOUNT_DIR + ('/%s/reports' % account)

    days = gen_days(start, end)
    input_files = verify_inputs(['log+%s+%s+.adv.lc.stats' % (day.strftime('%y%m%d'), account) for day in days], account)
    log("Cleaned inputs: %s" % input_files)
    inputs = [input_dir + '/' + file for file in input_files]
    return (inputs, output_dir)

def verify_inputs(inputs, account):
    log("Dirtayy inputs: %s" % inputs)
    input_dir = SHORT_ACCT_DIR + '/%s/daily_logs' % account
    return [file for file in inputs if BUCK.get_key(input_dir + '/' + file) is not None]

def upload_file(fd):

    register_openers()
    datagen, headers = multipart_encode({'file' : fd})

    upload_url_req = urllib2.Request(HOST + URL_HANDLER_PATH)
    log(HOST+URL_HANDLER_PATH)
    upload_url = urllib2.urlopen(upload_url_req).read()

    file_upload_req = urllib2.Request(upload_url, datagen, headers)
    blob_key = urllib2.urlopen(file_upload_req).read()
    return blob_key

def auth_func():
    return 'olp@mopub.com', 'N47935'

def setup_remote_api():
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)
