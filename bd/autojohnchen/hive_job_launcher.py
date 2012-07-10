import logging
import os
import sys
import time
import traceback
from datetime import datetime

import boto
from boto.emr.connection import EmrConnection
from boto.emr.instance_group import InstanceGroup
from boto.emr.step import JarStep
from boto.s3.connection import S3Connection
from boto.s3.key import Key


# create the EMR connection
ACCESS_KEY_ID = 'AKIAJKOJXDCZA3VYXP3Q'
SECRET_ACCESS_KEY = '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'
EMR_CONN = EmrConnection(ACCESS_KEY_ID, SECRET_ACCESS_KEY)
S3_CONN = S3Connection(ACCESS_KEY_ID, SECRET_ACCESS_KEY)

S3_BUCKET = S3_CONN.get_bucket('mopub-aws-logging')
S3_ROOT = 's3://mopub-aws-logging'
S3_LOG_URI = S3_ROOT + '/jobflow_logs'

AZ = 'us-east-1'
AWS_HIVE_LIB_DIR = 's3://%s.elasticmapreduce/libs/hive/' % (AZ)
SCRIPT_RUNNER_JAR = 's3://%s.elasticmapreduce/libs/script-runner/script-runner.jar' % (AZ)
AWS_HIVE_VER = '0.7.1'

JOBFLOW_NAME = 'jc automator hive job'
SCHEMA_VERSION = 2
USER='autojohnchen'
QUERY_FILE = 'monthly_mpx_rev_by_app.q'

NUM_MACHINES = 100


def get_jobflow_state(jobid):
    while True:
        try:
            state = EMR_CONN.describe_jobflow(jobid).state
            return state
        except:
            time.sleep(1)
            logging.info('try to get waiting jobflow state again...')


def get_output_data(s3_path):
    content = ''
    rs = S3_BUCKET.list(s3_path)
    for f in rs:
        content += f.get_contents_as_string()
    return content


def get_waiting_jobflow():
    waiting_jobflows = EMR_CONN.describe_jobflows(['WAITING'])
    for jobflow in waiting_jobflows:
        if jobflow.name != JOBFLOW_NAME: continue

        jobid = jobflow.jobflowid
        num_steps = len(jobflow.steps)
        logging.info('found waiting jobflow %s "%s" with %i steps completed' % (jobid, JOBFLOW_NAME, num_steps))

        if num_steps > 250:
            logging.info('num of steps near limit of 256: terminating jobflow %s "%s" ...' % (jobid, JOBFLOW_NAME))
            EMR_CONN.terminate_jobflow(jobid)
        else:
            return jobid
    return None


def launch_monthly_mpx_rev_hivejob(year, month, num_machines=NUM_MACHINES):
    # create master and core instance groups
    instance_groups = [
        InstanceGroup(num_instances=1, role='MASTER', type='m1.large', market='ON_DEMAND', name='master-group'),
        InstanceGroup(num_instances=num_machines, role='CORE', type='m1.large', market='ON_DEMAND', name='core-group'),
    ]

    # for single digit months
    month = str(month).rjust(2, '0')

    # populate hive args
    hive_args = []
    hive_args += ['v=%i' % SCHEMA_VERSION]
    hive_args += ['y=%s' % year]  # current year
    hive_args += ['m=%s' % month]  # current month

    # add username and filename as hive args, accessible inside hive query file
    hive_args += ['user=%s' %USER, 'qf=%s' %QUERY_FILE]

    logging.info('hive args: %s', hive_args)

    # prepend S3 URI path to hive script file
    # s3://mopub-aws-logging/hive_scripts/autojohnchen/monthly_mpx_rev_by_app.q
    s3_query_file = '%s/hive_scripts/%s/%s' % (S3_ROOT, USER, QUERY_FILE)


    # jar step to setup Hive on EMR machine
    setup_step = JarStep(
        name='setup hive',
        jar=SCRIPT_RUNNER_JAR,
        step_args=[AWS_HIVE_LIB_DIR + 'hive-script',
            '--base-path', AWS_HIVE_LIB_DIR,
            '--hive-versions', AWS_HIVE_VER,
            '--install-hive'],
    )

    # basic step args for running hive script
    script_step_args = [AWS_HIVE_LIB_DIR + 'hive-script',
        '--base-path', AWS_HIVE_LIB_DIR,
        '--hive-versions', AWS_HIVE_VER,
        '--run-hive-script',
        '--args',
        '-f', s3_query_file]

    # add additional hive args from CLI
    for pair in hive_args:
        script_step_args.extend(['-d', pair])

    # jar step running the Hive script
    script_step = JarStep(
        name=QUERY_FILE,
        jar=SCRIPT_RUNNER_JAR,
        step_args=script_step_args,
    )


    # try to find an existing jobflow in waiting mode
    while True:
        try:
            jobid = get_waiting_jobflow()
            break
        except:
            time.sleep(1)
            logging.info('try to get waiting jobflows again...')

    if jobid:
        steps = [script_step]   # no need for setup step
        EMR_CONN.add_jobflow_steps(jobid, steps)
        logging.info('added step to waiting jobflow: %s "%s"' %(jobid, JOBFLOW_NAME))
    else:   # spin up a new jobflow
        steps = [setup_step, script_step]
        jobid = EMR_CONN.run_jobflow(
            name=JOBFLOW_NAME,
            ec2_keyname='jpmopub',
            steps=steps,
            log_uri=S3_LOG_URI,
            instance_groups=instance_groups,
            keep_alive=True,
            enable_debugging=True,
            hadoop_version='0.20.205',
            ami_version='2.0',
        )
        logging.info('submitted new jobflow: %s "%s"' %(jobid, JOBFLOW_NAME))

    # output dir containing hive results:
    # hive_outputs/autojohnchen/monthly_mpx_rev_by_app.q/v=2/y=${y}/m=${m}
    output_dir = 'hive_outputs/%s/%s/v=%s/y=%s/m=%s' % (USER, QUERY_FILE, SCHEMA_VERSION, year, month)

    return jobid, output_dir



if __name__ == '__main__':
    # for testing out
    launch_monthly_mpx_rev_hivejob(2012, 4)
