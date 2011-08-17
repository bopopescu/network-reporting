
from boto.emr.connection import EmrConnection
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from report_mr_submitter import submit_job

from parse_utils import gen_report_fname, parse_msg
from parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs/reports'  

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'

MAX_MSGS = 10
SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
EMR_CONN = EmrConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

def job_failed(job_id):
    state = EMR_CONN.describe_jobflow(job_id).state
    if state in [u'TERMINATED', u'FAILED']:
        return True
    else:
        return False

def job_succeeded(job_id):
    state = EMR_CONN.describe_jobflow(job_id).state
    if state in [u'COMPLETED', u'WAITING']:
        return True
    else:
        return False


def notify_appengine(fname):
    report_dir = ACCOUNT_DIR + '/%s/reports/'
    report_dir = report_dir % acct
    file = report_dir + fname


def main_loop():
    report_queue = SQS_CONN.create_queue('report_queue')
    job_msg_map = {}
    to_del = []
    while True:
        if report_queue.count() > 0:
            msgs = report_queue.get_messages(MAX_MSGS)
            for msg in msgs:
                # Ignore messages being processed
                if msg in to_del:
                    continue
                # Start the MR job
                job_id, fname = submit_job(*parse_msg(msg))
                # Save the msg w/ the job id
                job_msg_map[job_id] = (fname, msg)
                # Add message to list of messages to remove from queue
                to_del.append(msg)

        for i in range(len(to_del)):
            msg = to_del.pop(0)
            # Try to remove the msg from the Q
            if not report_queue.delete_message(msg):
                # If it fails, add it to removal list
                to_del.append(msg)
        processed_jobs = []
        statuses = EMR_CONN.describe_jobflows(job_msg_map.keys())
        print statuses
        for job_id, (fname, msg) in job_msg_map.iteritems():
            # Add failed jobs back to the queue
            if job_failed(job_id):
                report_queue.write(msg)
                processed_jobs.append(job_id)
            # Notify GAE when a report is finished
            elif job_succeeded(job_id):
                notify_appengine(fname)
                processed_jobs.append(job_id)

        # Remove Completed/Failed jobs from the map so we don't
        # Repeatedly notify GAE//Continuously add a job that 
        # failed once
        for job_id in processed_jobs:
            del(job_msg_map[job_id])


if __name__ == '__main__':
    main_loop()
