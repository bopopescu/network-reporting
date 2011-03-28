import logging
import sys
import time
from optparse import OptionParser

import boto
import boto.emr
from boto.emr.step import StreamingStep


S3_BUCKET = 'log-counts'
LOG_URI = 's3://' + S3_BUCKET + '/jobflow_logs'
# MAPPER = 's3://' + S3_BUCKET + '/code/logparser_mapper.py'
# REDUCER = 'aggregate'
MAPPER = 's3://' + S3_BUCKET + '/code/log_mapper.py'
REDUCER = 's3://' + S3_BUCKET + '/code/log_reducer.py'



NUM_INSTANCES = 1
MASTER_INSTANCE_TYPE = 'm1.small'
SLAVE_INSTANCE_TYPE = 'm1.small'
KEEP_ALIVE = False
    
    
def main():
    start = time.time()
        
    parser = OptionParser()
    parser.add_option('-f', '--file', dest='logfile')
    parser.add_option('-n', '--num_instances', dest='num_instances', default=NUM_INSTANCES)
    (options, args) = parser.parse_args()
    
    conn = boto.connect_emr()

    step = StreamingStep(
        name='logparser step',
        mapper=MAPPER,
        reducer=REDUCER,
        input=options.logfile,
        output=options.logfile+'.out',
    )

    jobid = conn.run_jobflow(
        name='logparser job',
        steps=[step],
        log_uri=LOG_URI,
        num_instances=options.num_instances,
        master_instance_type=MASTER_INSTANCE_TYPE,
        slave_instance_type=SLAVE_INSTANCE_TYPE,
        keep_alive=KEEP_ALIVE,
        enable_debugging=True,
    )

    print 'submitted job: %s'%jobid

    while True:
        state = conn.describe_jobflow(jobid).state
        print '%s\tjob state: %s' % (time.strftime('%b %d %Y %H:%M:%S'), state)
        if state not in [u'COMPLETED', u'FAILED', u'TERMINATED']:
            time.sleep(30)
        else:
            break
    
    elapsed = time.time() - start
    print "job %s took %i minutes and %i seconds" % (jobid, elapsed/60, elapsed%60)
    


if __name__ == "__main__":
    main()
