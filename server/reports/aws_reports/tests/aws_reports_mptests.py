import sys
import os
from datetime import datetime
import logging
sys.path.append(os.environ['PWD'])
import time

import common.utils.test.setup
import unittest

from reports.models import Report, ScheduledReport
from reports.aws_reports.helpers import AWS_ACCESS_KEY, AWS_SECRET_KEY
from reports.aws_reports.report_message_handler import (
                                            ReportMessageHandler, 
                                            ReportMessage,
                                            UPLOAD,
                                            BLOB_KEY_PUT,
                                            PARSE,
                                            POST_PARSE_BLOB_PUT,
                                            POST_PARSE_PUT,
                                            NOTIFY,
                                            MESSAGE_COMPLETION_STEPS,
                                            TEST_FAIL_TIMEOUT,
                                            )
from account.models import Account
from boto.sqs.connection import SQSConnection
from boto.sqs.message import Message

from nose.tools import with_setup
from budget import budget_service

from google.appengine.ext import testbed

TEST_FAIL_TIMEOUT += 1

SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
TEST_REPORT_QUEUE = 'test_report_queue'
MY_DIR = os.path.split(os.path.abspath(__file__))[0]
TEST_DATA_DIR = os.path.join(MY_DIR, 'test_data')

def queue_writer(queue):
    def writer(mesg_data):
        m = Message()
        m.set_body(mesg_data) 
        queue.write(m)
    return writer

############ spoofed boto shit ##############

class FakeJobFlow(object):

    def __init__(self, jobflowid, steps, state):
        self.jobflowid = jobflowid
        self.steps = steps
        self.state = state


class FakeJobFlowStep(object):
    
    def __init__(self, id, state, name):
        self.id = id
        self.state = state
        self.name = name 

############ this is why python rules #######
# (otherwise you'd actually have to implement something the right way)


class TestMessageHandler(unittest.TestCase):


    def setUp(self):
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.account = Account()
        self.account.put()
        test_queue = SQS_CONN.create_queue(TEST_REPORT_QUEUE)
        test_queue.clear()
        self.queue_write = queue_writer(test_queue)
        self.sched = ScheduledReport(account = self.account,
                                d1 = 'campaign',
                                d2 = 'adunit',
                                end = datetime.now().date(),
                                days = 1,
                                )

        self.sched2 = ScheduledReport(account = self.account,
                                d1 = 'app',
                                d2 = 'adunit',
                                end = datetime.now().date(),
                                days = 1,
                                )
        self.sched.put()
        self.sched2.put()
        logging.warning("Putting report")
        self.rep = Report(account = self.account,
                          schedule = self.sched,
                          start = datetime.now().date(),
                          end = datetime.now().date(),
                          )
        self.rep2 = Report(account = self.account,
                          schedule = self.sched2,
                          start = datetime.now().date(),
                          end = datetime.now().date(),
                          )
        self.rep.put()
        self.rep2.put()
        self.reps = [self.rep, self.rep2]
        self.rmh = ReportMessageHandler(test_queue, testing=True)

    def tearDown(self):
        self.testbed.deactivate()

    def assert_empty_sqs_queue(self):
        # If the queue says there are messages, make sure we can't actually get them
        while not self.rmh.queue.count() == 0:
            assert not self.rmh.handle_messages()
            # Fucking timeout
            time.sleep(1)
        return True
    
    def empty_rmh_maps(self):
        for msg_map in self.rmh.message_maps:
            if not msg_map == {}:
                return False
        return True

    def handle_message_no_data_mptest(self):
        # No data, make sure message is failed, marked as failed, and not in queue
        self.queue_write(self.rep.message)
        # There is a message in the queue, it was just written, keep trying
        # Until it's processed
        while not self.rmh.handle_messages(force_no_data=True):
            time.sleep(.5)
        # Assert that all messages have been handled
        assert len(self.rmh.to_del) == 0
        self.assert_empty_sqs_queue()

        assert Report.get(self.rep.key()).status == "No Data"


    def handle_message_mr_submit_error_mptest(self):
        # MR Submit Error, make sure message is readded to queue 2(3?) times, marked as failed, then not in queue
        self.queue_write(self.rep.message)
        retry = 0
        success = False
        while not success:
            # Force an error while handling
            handled = self.rmh.handle_messages(force_submit_error = True)
            if handled:
                retry += 1
                for k,v in self.rmh.msg_failures.iteritems():
                    assert v == retry
                timeout_retry = 0
                # Make sure it was readded to the Queue
                while self.rmh.queue.count() == 0 and retry <= 3:
                    timeout_retry += 1
                    if timeout_retry == 10:
                        assert False
                    time.sleep(.5)

            # 3 failures, 4th retry and fail = end
            if retry == 4:
                # Make sure it's not in the queue
                assert len(self.rmh.to_del) == 0
                if self.assert_empty_sqs_queue():
                    success = True
                assert success
        # make sure it failed for the right reason
        assert Report.get(self.rep.key()).status == "Failed"

    def handle_message_ignore_deleted_mptest(self):
        # If message in to_del but somehow being processed, ignore it
        self.queue_write(self.rep.message)
        # should run, message should be in to_del, but not handled
        while not self.rmh.handle_messages(force_delete_error=True):
            time.sleep(.5)
        assert len(self.rmh.to_del) == 1
        
        # Report ran with no failures, but didn't get pushed to EMR (testing, duh)
        # so it should be stuck in pending
        assert Report.get(self.rep.key()).status == 'Pending'

        # Force no data, to_del is checked first, should ignore everything else
        while not self.rmh.handle_messages(force_no_data=True):
            time.sleep(.5)

        assert len(self.rmh.to_del) == 0
        # Normally force_no_data would cause this to read 'No Data'
        # but that's not the case
        assert Report.get(self.rep.key()).status == 'Pending'
        

    def handle_message_mptest(self):
        self.queue_write(self.rep.message)
        # No Errors, nothing happens to message, not in queue
        while not self.rmh.handle_messages():
            time.sleep(.5)
        assert len(self.rmh.to_del) == 0
        assert Report.get(self.rep.key()).status == 'Pending'
        self.assert_empty_sqs_queue()
        assert self.rmh.msg_failures.values()[0] == 0


    def handle_jobflow_success_mptest(self):
        jobflow, message = self.create_jobflow()
        self.rmh.handle_working_jobs(jobflows=[jobflow])
        logging.warning("Mesg map: %s" % self.rmh.jobid_message_map)
        # Make sure we're clean
        assert self.empty_rmh_maps()
        report = open(TEST_DATA_DIR + '/sample_data.final', 'r').read()
        logging.warning(report)
        logging.warning(Report.get(self.rep.key()).test_report_blob)
        # Make sure the rep is the same
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).test_report_blob == report

    def handle_upload_failure_mptest(self):
        # List of jobs, one job is failed, make sure in queue, fail again.  Do this three times, assert in the queue every time, on third failure remove from queue, don't process again, marked as failed
        jobflow, message = self.create_jobflow()
        my_step = UPLOAD
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_blob_keys[message] is None
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'

    def handle_key_put_failure_mptest(self):
        # Blobstore fails, make sure the report isn't replicated a million times (whoops)
        jobflow, message = self.create_jobflow()
        my_step = BLOB_KEY_PUT
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_blob_keys[message] is not None
            assert Report.get(self.rep.key()).test_report_blob is None
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'

    def handle_parse_failure_mptest(self):
        # make sure message isnt' removed from the 'to process' list
        jobflow, message = self.create_jobflow()
        my_step = PARSE
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_blob_keys[message] is not None
                assert self.rmh.message_data[message] is None
            assert Report.get(self.rep.key()).test_report_blob is not None
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'
 
    def handle_post_parse_blob_upload_failure_mptest(self):
        jobflow, message = self.create_jobflow()
        my_step = POST_PARSE_BLOB_PUT
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_blob_keys[message] is not None
                assert self.rmh.message_data[message] is not None
            rep = Report.get(self.rep.key())
            assert rep.test_report_blob is not None
            assert rep.completed_at is None
            assert rep.data == {}
        logging.warning(self.rmh.message_maps)
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'

    def handle_post_parse_failure_mptest(self):
        jobflow, message = self.create_jobflow()
        my_step = POST_PARSE_PUT
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_html_blob_keys[message] is not None
                assert self.rmh.message_blob_keys[message] is not None
                assert self.rmh.message_data[message] is not None
            rep = Report.get(self.rep.key())
            assert rep.test_report_blob is not None
            assert rep.completed_at is None
            assert rep.data == {}
        logging.warning(self.rmh.message_maps)
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'

    def handle_post_parse_multi_message_failure_mptest(self):
        jobflow, messages = self.create_jobflow(msgs=2)
        bad_msg, good_msg = messages
        my_step = POST_PARSE_PUT
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step, fail_msg=bad_msg)
            if not self.empty_rmh_maps():
                # Assert that only the bad message has these, the good message
                # has been cleaned up
                assert self.success_until(bad_msg, my_step)
                assert self.rmh.message_blob_keys[bad_msg] is not None
                assert self.rmh.message_data[bad_msg] is not None
            rep = Report.get(self.rep.key())
            rep2 = Report.get(self.rep2.key())
            assert rep.test_report_blob is not None
            assert rep.completed_at is None
            assert rep.data == {}

            assert rep2.test_report_blob is not None
            assert rep2.completed_at is not None
            assert not rep2.data == {}
        logging.warning(self.rmh.message_maps)
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'
        assert not Report.get(self.rep2.key()).status == 'Failed'

    def handle_notify_failure_mptest(self):
        jobflow, message = self.create_jobflow()
        my_step = NOTIFY
        now = datetime.now()
        while (datetime.now() - now).seconds < TEST_FAIL_TIMEOUT:
            self.rmh.handle_working_jobs(jobflows = [jobflow], force_failure = True, fail_step = my_step)
            if not self.empty_rmh_maps():
                assert self.success_until(message, my_step)
                assert self.rmh.message_blob_keys[message] is not None
                assert self.rmh.message_data[message] is not None
            rep = Report.get(self.rep.key())
            assert rep.test_report_blob is not None
            assert rep.completed_at is not None
            assert rep.data is not None
        assert self.empty_rmh_maps()
        assert Report.get(self.rep.key()).status == 'Failed'

    def create_jobflow(self, msgs=1):
        messages = []
        steps = []
        for i in range(msgs):
            m = Message()
            m.set_body(self.reps[i].message)
            good_message = ReportMessage(m)
            step = FakeJobFlowStep(id = i, state = u'COMPLETED', name = good_message.step_name)
            messages.append(good_message)
            steps.append(step)
        for i in range(4):
            steps.append(FakeJobFlowStep(id=i+msgs, state=u'RUNNING', name = 'irrelevant_step_%s' % i))
        jobflow = FakeJobFlow(jobflowid = 1, steps = steps, state = u'RUNNING')
        self.rmh.jobid_message_map[jobflow.jobflowid] = messages
        for msg in messages:
            self.rmh.init_message(msg)
        if len(messages) == 1:
            return jobflow, messages[0]
        else:
            return jobflow, messages


    def success_until(self, message, step):
        for s in MESSAGE_COMPLETION_STEPS:
            if s == step:
                if not self.rmh.completed(message, s):
                    return True
                else:
                    return False
            elif not self.rmh.completed(message, s):
                return False

