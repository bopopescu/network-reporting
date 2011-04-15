import logging
import os
import time
from optparse import OptionParser

from boto.emr.connection import EmrConnection
from boto.emr.step import StreamingStep


S3_BUCKET = 'mopub-aws-logging'
LOG_URI = 's3://' + S3_BUCKET + '/jobflow_logs'
LOG_MAPPER = 's3://' + S3_BUCKET + '/code/log_mapper.py'
LOG_REDUCER = 's3://' + S3_BUCKET + '/code/log_reducer.py'
UNIQ_USER_MAPPER = 's3://' + S3_BUCKET + '/code/uniq_user_mapper.py'


NUM_INSTANCES = 1
MASTER_INSTANCE_TYPE = 'm1.large'
SLAVE_INSTANCE_TYPE = 'm1.large'
KEEP_ALIVE = True
    


def get_waiting_jobflow(conn):
    waiting_jobflow_ids = conn.describe_jobflows([u'WAITING'])
    if len(waiting_jobflow_ids) > 0:
        jobid = waiting_jobflow_ids[0].jobflowid
        print 'found waiting jobflow:', jobid
        return jobid
    else:
        return None

    
def main():
    start = time.time()
        
    parser = OptionParser()
    parser.add_option('-l', '--local_dir', dest='local_dir')
    parser.add_option('-r', '--remote_dir', dest='remote_dir')
    parser.add_option('-o', '--output_file', dest='output_file')
    parser.add_option('-n', '--num_instances', dest='num_instances', default=NUM_INSTANCES)
    (options, args) = parser.parse_args()
    
    print
    print "local dir:\t", options.local_dir
    print "remote dir:\t", options.remote_dir
    print

    log_count_input_files = [os.path.join(options.remote_dir, f) for f in os.listdir(options.local_dir) 
                                if f.startswith('chunk')]
    uniq_user_input_files = [os.path.join(options.remote_dir, f) for f in os.listdir(options.local_dir) 
                                if f.startswith('pp-chunk')]
        
    conn = EmrConnection('AKIAJKOJXDCZA3VYXP3Q', 'yjMKFo61W0mMYhMgphqa+Lc2WX74+g9fP+FVeyoH')

    log_count_step = StreamingStep(
        name='log count step',
        mapper=LOG_MAPPER,
        reducer=LOG_REDUCER,
        cache_files = ['s3://' + S3_BUCKET + '/code/log_parser.py#log_parser.py'],
        input=log_count_input_files,
        output=options.output_file+'.out',
    )
    
    uniq_user_count_step = StreamingStep(
        name='uniq user count step',
        mapper=UNIQ_USER_MAPPER,
        reducer='aggregate',
        cache_files = ['s3://' + S3_BUCKET + '/code/log_parser.py#log_parser.py'],
        input=uniq_user_input_files,
        output=options.output_file+'.pp.out',
    )
    
    #try to find an existing jobflow in waiting mode
    jobid = get_waiting_jobflow(conn)
    
    if jobid:
        conn.add_jobflow_steps(jobid, [log_count_step, uniq_user_count_step])
        print 'added step to waiting jobflow:', jobid
        
        # wait while jobflow is still in waiting mode
        while conn.describe_jobflow(jobid).state == u'WAITING':
            print '%s\tjob state: WAITING' % time.strftime('%b %d %Y %H:%M:%S')
            time.sleep(1)
    else:   # spin up a new jobflow    
        jobid = conn.run_jobflow(
            name='log parsing job',
            steps=[log_count_step, uniq_user_count_step],
            log_uri=LOG_URI,
            num_instances=options.num_instances,
            master_instance_type=MASTER_INSTANCE_TYPE,
            slave_instance_type=SLAVE_INSTANCE_TYPE,
            keep_alive=KEEP_ALIVE,
            enable_debugging=True,
        )
        print 'submitted new jobflow:', jobid
        
    # check jobflow status periodically while it's active
    while True:
        state = conn.describe_jobflow(jobid).state
        print '%s\tjob state: %s' % (time.strftime('%b %d %Y %H:%M:%S'), state)
        if state in [u'COMPLETED', u'FAILED', u'TERMINATED', u'WAITING']:
            break
        else:
            time.sleep(10)

    
    elapsed = time.time() - start
    print "job %s took %i minutes and %i seconds" % (jobid, elapsed/60, elapsed%60)
    


if __name__ == "__main__":
    main()
