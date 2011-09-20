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
from reports.aws_reports.report_exceptions import (MRSubmitError, ReportException)


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


def submit_job(d1, d2, d3, start, end, report_key, account):
    """ Returns Jobid, steps completed, and output name if job is added properly
    returns False for all values if there are no valid input files """
    conn = EmrConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

    inputs, output_dir = build_puts(start, end, account)
    if len(inputs) == 0:
        raise MRSubmitError('No inputs', report_key)
    instances = 10
    output_name = gen_report_fname(d1, d2, d3, start, end)
    start = start.strftime('%y%m%d')
    end = end.strftime('%y%m%d')

    output = output_dir + '/' + output_name

    gen_report_step = StreamingStep(
            name = 'Generate Report Step',
            mapper = REPORT_MAPPER % (d1, d2, d3),
            reducer = LOG_REDUCER,
            cache_files = [REPORTING_S3_CODE_DIR + '/parse_utils.py#parse_utils.py'],
            input = inputs,
            output = output,
            )

    steps_to_add = [gen_report_step]
    jobid, steps = get_waiting_jobflow(conn)
    try:
        if jobid:
            conn.add_jobflow_steps(jobid, steps_to_add)
        else:
            jobid = conn.run_jobflow(
                    name = JOBFLOW_NAME,
                    steps = steps_to_add,
                    log_uri = LOG_URI,
                    num_instances = instances,
                    master_instance_type = MASTER_INSTANCE_TYPE,
                    slave_instance_type = SLAVE_INSTANCE_TYPE,
                    keep_alive=KEEP_ALIVE,
                    enable_debugging=True,
                    )
    except Exception:
        raise MRSubmitError('No valid Job ID', report_key)
    return jobid, steps, output_name
