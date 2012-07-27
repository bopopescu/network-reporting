import logging
import random
import string
import sys
import time
import traceback
import urllib2


from boto.s3.connection import S3Connection

from reports.aws_reports.parse_utils import gen_days
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY, JOBFLOW_NAME
#from reports.aws_reports.report_exceptions import (MRSubmitError, ReportException, NoDataError)

############### Poster Imports ###############
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers

############### GAE Imports ###############
from google.appengine.ext.remote_api import remote_api_stub


############# AWS Magic ###################
S3_CONN = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
BUCK = S3_CONN.get_bucket('mopub-aws-logging')

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs/AAreports'

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/%s_%s_%s_report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'
SHORT_ACCT_DIR = 'account_data'

MASTER_INSTANCE_TYPE = 'm1.large'
SLAVE_INSTANCE_TYPE = 'c1.xlarge'
KEEP_ALIVE = True

################## GAE Uploading Stuff ##############
BACKEND = 'stats-updater'
APP = 'mopub-inc'
HOST = 'http://%s.%s.appspot.com' % (BACKEND, APP)
URL_HANDLER_PATH = '/offline/get_upload_url'
UPDATE_STATS_HANDLER_PATH = '/offline/update_stats'

################## Constants ###################
LOG_FORMAT = "%s:\t%s\n"
JOBFLOW_NAME = 'generating report job'

if sys.platform == 'darwin':
    LOG_FILE = 'poller_%d.log'
else:
    LOG_FILE = '/mnt/logs/poller_%d.log'

LOGGER = logging.getLogger('aws_reports')
LOGGER.setLevel(logging.DEBUG)
FORMATTER = logging.Formatter(fmt = '%(asctime)s %(name)-12s %(levelname)-8s --- %(message)s', datefmt = '%m-%d %H:%M')

HNDLR = logging.FileHandler(LOG_FILE % time.time())
HNDLR.setFormatter(FORMATTER)
LOGGER.addHandler(HNDLR)

def rotate_logfile():
    global HNDLR
    global LOGGER
    log('Rotating logfile', level='info')
    LOGGER.removeHandler(HNDLR)
    HNDLR = logging.FileHandler(LOG_FILE % time.time())
    HNDLR.setFormatter(FORMATTER)
    LOGGER.addHandler(HNDLR)
    log('Rotated logfile', level='info')

def log(mesg, level = 'warning'):
    if level == 'info':
        LOGGER.info(mesg)
    elif level == 'debug':
        LOGGER.debug(mesg)
    elif level == 'warning':
        LOGGER.warning(mesg)
    elif level == 'error':
        LOGGER.error(mesg)
    elif level == 'critical':
        LOGGER.error(mesg)
    elif level == 'exception':
        LOGGER.exception(mesg)
    else:
        LOGGER.info(mesg)

def default_exc_handle(e):
    log("Encountered exception: %s" % e, level='exception')

    tb_file = open('/mnt/logs/tb.log', 'a')
    tb_file.write("\nERROR---\n%s" % time.time())
    traceback.print_exc(file=tb_file)
    tb_file.close()


def build_puts(start, end, account):
    input_dir = ACCOUNT_DIR + ('/%s/daily_logs' % account)
    output_dir = ACCOUNT_DIR + ('/%s/reports' % account)

    days = gen_days(start, end)
    input_files = verify_inputs(['log+%s+%s+.adv.lc.stats' % (day.strftime('%y%m%d'), account) for day in days], account)
    log("Cleaned inputs: %s" % input_files)
    inputs = [input_dir + '/' + input_file for input_file in input_files]
    return (input_dir, inputs, output_dir)

def verify_inputs(inputs, account):
    log("Dirtayy inputs: %s" % inputs)
    input_dir = SHORT_ACCT_DIR + '/%s/daily_logs' % account
    return [input_file for input_file in inputs if BUCK.get_key(input_dir + '/' + input_file) is not None]

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
    return 'olp@mopub.com', 'N47935N47935'

def setup_remote_api():
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

def get_waiting_jobflow(conn, jobflow_ids):
    waiting_jobflows = conn.describe_jobflows(jobflow_ids= jobflow_ids)
    for jobflow in waiting_jobflows:
        if jobflow.name != JOBFLOW_NAME or jobflow.state not in [u'WAITING', u'RUNNING', u'STARTING']:
            continue
        jid = jobflow.jobflowid
        num_steps = len(jobflow.steps)
        print 'found waitingjobflow %s with %i steps completed' % (jid, num_steps)
        if num_steps > 250:
            if jobflow.state != u'RUNNING':
                print 'num of steps near limit of 256: terminating jobflow %s ...' % (jid)
                conn.terminate_jobflow(jid)
                print "Only jobflow is full"
        else:
            return jid
    return None

def gen_random_fname(chars = string.letters, length=16, prefix = '', suffix = ''):
    fname = ''.join([random.choice(chars) for i in range(length)])
    fname = prefix + fname + suffix
    return fname
