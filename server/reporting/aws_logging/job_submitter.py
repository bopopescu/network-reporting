import logging
import os
import time
from optparse import OptionParser

from boto.emr.bootstrap_action import BootstrapAction
from boto.emr.connection import EmrConnection
from boto.emr.step import StreamingStep


S3_BUCKET = 's3://mopub-aws-logging'
LOG_URI = S3_BUCKET + '/jobflow_logs'

S3_CODE_DIR = S3_BUCKET + '/code4'
DEDUP_MAPPER = S3_CODE_DIR + '/dedup_mapper.py'
PREPROCESS_MAPPER = S3_CODE_DIR + '/preprocess_mapper.py'

BASIC_LOG_MAPPER = S3_CODE_DIR + '/basic_log_mapper.py'
ADVANCED_LOG_MAPPER = S3_CODE_DIR + '/advanced_log_mapper.py'

LOG_REDUCER = S3_CODE_DIR + '/log_reducer.py'
UNIQ_USER_MAPPER = S3_CODE_DIR + '/uniq_user_mapper.py'


NUM_INSTANCES = 1
MASTER_INSTANCE_TYPE = 'm1.large'
SLAVE_INSTANCE_TYPE = 'm1.large'
# MASTER_INSTANCE_TYPE = 'm1.small'
# SLAVE_INSTANCE_TYPE = 'm1.small'
KEEP_ALIVE = False
    


def get_waiting_jobflow(conn):
    waiting_jobflows = conn.describe_jobflows([u'WAITING'])
    for jobflow in waiting_jobflows:
        jobid = jobflow.jobflowid
        num_steps = len(jobflow.steps)
        print 'found waiting jobflow %s with %i steps completed' % (jobid, num_steps)
        
        if num_steps > 250:
            print 'num of steps near limit of 256: terminating jobflow %s ...' % (jobid)
            conn.terminate_jobflow(jobid)
        else:
            return jobid
    return None

    
def main():
    start = time.time()
        
    parser = OptionParser()
    parser.add_option('-i', '--input_dir', dest='input_dir')
    parser.add_option('-n', '--num_instances', type='int', dest='num_instances', default=NUM_INSTANCES)
    (options, args) = parser.parse_args()
        
    conn = EmrConnection('AKIAJKOJXDCZA3VYXP3Q', 'yjMKFo61W0mMYhMgphqa+Lc2WX74+g9fP+FVeyoH')

    bootstrap_step = BootstrapAction(
        name='bootstrap step',
        path=S3_CODE_DIR+'/bootstrap.sh',
        bootstrap_action_args=None)

    dedup_step = StreamingStep(
        name='dedup step',
        mapper=DEDUP_MAPPER,
        reducer='aggregate',
        input=options.input_dir+'.raw',
        output=options.input_dir+'.dd',
    )

    preprocess_step = StreamingStep(
        name='preprocess step',
        mapper=PREPROCESS_MAPPER,
        reducer='aggregate',
        cache_files=[S3_CODE_DIR+'/utils.py#utils.py', S3_CODE_DIR+'/parse_utils.py#parse_utils.py', S3_CODE_DIR+'/wurfl.py#wurfl.py', S3_CODE_DIR+'/deref_cache.pkl#deref_cache.pkl'],
        input=options.input_dir+'.dd',
        output=options.input_dir+'.pp',
    )

    # pub:adv:country_code:time (hour & day)
    basic_count_step = StreamingStep(
        name='log count step',
        mapper=BASIC_LOG_MAPPER,
        reducer=LOG_REDUCER,
        cache_files=[S3_CODE_DIR+'/utils.py#utils.py', S3_CODE_DIR+'/parse_utils.py#parse_utils.py', S3_CODE_DIR+'/wurfl.py#wurfl.py'],
        input=options.input_dir+'.dd',
        output=options.input_dir+'.basic.dd.out',
    )

    # pub:adv:country_code:brand_name:marketing_name:os:os_version:hour
    advanced_count_step = StreamingStep(
        name='log count step',
        mapper=ADVANCED_LOG_MAPPER,
        reducer=LOG_REDUCER,
        cache_files=[S3_CODE_DIR+'/utils.py#utils.py', S3_CODE_DIR+'/parse_utils.py#parse_utils.py', S3_CODE_DIR+'/wurfl.py#wurfl.py'],
        input=options.input_dir+'.dd',
        output=options.input_dir+'.advanced.dd.out',
    )

    uniq_user_count_step = StreamingStep(
        name='uniq user count step',
        mapper=UNIQ_USER_MAPPER,
        reducer='aggregate',
        cache_files=[S3_CODE_DIR+'/utils.py#utils.py', S3_CODE_DIR + '/parse_utils.py#parse_utils.py'],
        input=options.input_dir+'.pp',
        output=options.input_dir+'.pp.out',
    )
    
    # try to find an existing jobflow in waiting mode
    jobid = get_waiting_jobflow(conn)
    
    if jobid:
        conn.add_jobflow_steps(jobid, [dedup_step, preprocess_step, basic_count_step, advanced_count_step, uniq_user_count_step])
        print 'added step to waiting jobflow:', jobid
        
        # wait while jobflow is still in waiting mode
        while conn.describe_jobflow(jobid).state == u'WAITING':
            print '%s\tjob state: WAITING' % time.strftime('%b %d %Y %H:%M:%S')
            time.sleep(1)
    else:   # spin up a new jobflow    
        jobid = conn.run_jobflow(
            name='log parsing job',
            steps=[dedup_step, preprocess_step, basic_count_step, advanced_count_step, uniq_user_count_step],
            bootstrap_actions=[bootstrap_step],
            log_uri=LOG_URI,
            num_instances=options.num_instances,
            main_instance_type=MASTER_INSTANCE_TYPE,
            subordinate_instance_type=SLAVE_INSTANCE_TYPE,
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
