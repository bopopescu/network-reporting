from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message
from report_mr_submitter import submit_job

from parse_utils import gen_report_fname, parse_msg
from parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY

S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs'  

REPORTING_S3_CODE_DIR = S3_BUCKET + '/reports_code0'

REPORT_MAPPER = REPORTING_S3_CODE_DIR + '/report_mapper.py'
LOG_REDUCER = REPORTING_S3_CODE_DIR + '/log_reducer.py'

ACCOUNT_DIR = S3_BUCKET + '/account_data'

MAX_MSGS = 10

def notify_appengine(msg):
    d1, d2, d3, start, end, rep, acct = parse_msg(msg)
    report_file = gen_report_fname(d1, d2, d3, start, end)
    report_dir = ACCOUNT_DIR + '/%s/reports/' + report_file
    report_dir = report_dir % acct


def main_loop():
    conn = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
    report_queue = conn.create_queue('report_queue')
    job_msg_map = {}
    while True:
        if report_queue.count() > 0:
            msgs = report_queue.get_messages(MAX_MSGS)
            for msg in msgs:
                # Start the MR job
                job_id = submit_job(*parse_msg(msg))
                # Save the msg w/ the job id
                job_msg_map[job_id] = msg
                # Remove the msg from the Q
                report_queue.delete_message(msg)

        processed_jobs = []
        for job_id, msg in job_msg_map.iteritems():
            # Add failed jobs back to the queue
            if job_failed(job_id):
                report_queue.write(msg)
                processed_jobs.append(job_id)
            # Notify GAE when a report is finished
            elif job_succeeded(job_id):
                notify_appengine(msg)
                processed_jobs.append(job_id)

        # Remove Completed/Failed jobs from the map so we don't
        # Repeatedly notify GAE//Continuously add a job that 
        # failed once
        for job_id in processed_jobs:
            del(job_msg_map[job_id])


if __name__ == '__main__':
    main_loop()
