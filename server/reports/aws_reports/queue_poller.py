#!/usr/bin/python
import logging
import time
import sys
import os

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
from boto.sqs.connection import SQSConnection

############### Mopub Imports ############### 
from reports.aws_reports.parse_utils import AWS_ACCESS_KEY, AWS_SECRET_KEY
from reports.aws_reports.report_message_handler import ReportMessageHandler
from reports.aws_reports.helpers import default_exc_handle, rotate_logfile

################## PID Stuff ######################
f = open("/tmp/poller.pid", 'w')
f.write('%s' % os.getpid())
f.close()


################## Other AWS Stuff ###################
MAX_MSGS = 10
SQS_CONN = SQSConnection(AWS_ACCESS_KEY, AWS_SECRET_KEY)

################## Constants ###################
REPORT_QUEUE = 'report_queue'

DAWN_OF_TIME = time.time()
SECONDS_IN_DAY = 86400

def main_loop():
    report_queue = SQS_CONN.create_queue(REPORT_QUEUE)
    rep_handler = ReportMessageHandler(report_queue)
    last_day = 0
    while True:

        if int((time.time() - DAWN_OF_TIME)/SECONDS_IN_DAY) != last_day:
            last_day += 1
            rotate_logfile()

        try:
            # Throws no unhandled errors
            rep_handler.handle_messages()
            # Throws some errors if BlobStore is busy//down
            # rep_handler must handle errors that need to notify GAE
            rep_handler.handle_working_jobs()
            # Maybe Throws something
            rep_handler.kill_waiting_jobflows()
            time.sleep(10)
        except Exception, e:
            logging.warning("\n\n\nFAILING FAILING FAILLING FAILING")
            default_exc_handle(e)

if __name__ == '__main__':
    main_loop()
