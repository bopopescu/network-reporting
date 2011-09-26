from reports.models import Report, ScheduledReport
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message

SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
TEST_REPORT_QUEUE = 'test_report_queue'
TEST_QUEUE = SQS_CONN.create_queue(TEST_REPORT_QUEUE)
TEST_RMH = ReportMessageHandler(TEST_QUEUE, testing=True)

def queue_writer(queue):
    def writer(mesg_data):
        m = Message()
        m.set_body(mesg_data) 
        queue.write(m)
    return writer

test_queue_write = queue_writer(TEST_QUEUE)


def handle_message_no_data_mptest():
    
    

    # No data, make sure message is failed, marked as failed, and not in queue
    pass

def handle_message_mr_submit_error_mptest():
    # MR Submit Error, make sure message is readded to queue 2(3?) times, marked as failed, then not in queue
    pass

def handle_message_ignore_deleted():
    # If message in to_del but somehow being processed, ignore it
    pass

def handle_message_mptest():
    # No Errors, nothing happens to message, not in queue
    pass


def handle_jobflow_success():
    # List of jobs, one job is finished, finished job marked as finished, removed from list of finished jobs, marked as finished
    pass

def handle_jobflow_failure():
    # List of jobs, one job is failed, make sure in queue, fail again.  Do this three times, assert in the queue every time, on third failure remove from queue, don't process again, marked as failed
    pass

def on_success_blobstore_failure():
    # Blobstore fails, make sure the report isn't replicated a million times (whoops)
    pass

def on_success_finalize_failure():
    # Make sure message isnt' removed from the 'to process' list
    pass
