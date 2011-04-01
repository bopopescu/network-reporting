#!/bin/bash
PATH=$PATH:/usr/local/bin:~/google_appengine

APP_DIR=~/mopub/server
LOG_DIR=~/aws_logs
S3_BUCKET=mopub-aws-logging
S3_LOG_DIR=s3://$S3_BUCKET/logs-`date +"%Y-%m%d"`

LOGFILE=aws-logfile-`date +"%Y-%m%d-%H%M"`
LOCAL_LOGFILE=$LOG_DIR/$LOGFILE
S3_LOGFILE=$S3_LOG_DIR/$LOGFILE


# start timestamp
OVERALL_START_TIME=$(date +%s)
echo
echo
echo `date +"%D"` `date +"%T"`
echo
echo

mkdir $LOG_DIR

START_TIME=$(date +%s)

# download logs from GAE
echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 request_logs $APP_DIR $LOG_DIR/request-logfile
echo

STOP_TIME=$(date +%s)
echo
echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"


echo
echo "copying downloaded logs to" $LOCAL_LOGFILE "as input to EMR..."
cp $LOG_DIR/request-logfile $LOCAL_LOGFILE


START_TIME=$(date +%s)

# upload new logs to S3
echo
echo "uploading" $LOCAL_LOGFILE "to" $S3_LOGFILE "..."
s3cmd put $LOCAL_LOGFILE $S3_LOGFILE

STOP_TIME=$(date +%s)
echo "uploading GAE logs to S3 took" $((STOP_TIME-START_TIME)) "seconds"


START_TIME=$(date +%s)

# submit and run job
echo
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -f $S3_LOGFILE #-n 3

STOP_TIME=$(date +%s)
echo "EMR job took" $((STOP_TIME-START_TIME)) "seconds"


START_TIME=$(date +%s)

# download output files from S3 and merge them into one
echo
s3cmd get $S3_LOGFILE.out/part-* $LOG_DIR

STOP_TIME=$(date +%s)
echo "download S3 output files took" $((STOP_TIME-START_TIME)) "seconds"

echo
echo "merging output files to" $LOCAL_LOGFILE.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.stats


# deleting local and remote S3 output files (clean slate for next run)
echo
echo "deleting local S3 part files at" $LOG_DIR
rm -rf $LOG_DIR/part-*
echo "deleting remote S3 part files at" $S3_LOGFILE.out
s3cmd del --recursive $S3_LOGFILE.out


START_TIME=$(date +%s)

# parse MR output and update StatsModels in GAE datastore
echo
echo "updating GAE datastore..."
python $APP_DIR/reporting/aws_logging/stats_updater.py -f $LOCAL_LOGFILE.stats 

STOP_TIME=$(date +%s)
echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"


echo
echo "uploading stats file to" $S3_LOGFILE.stats
s3cmd put $LOCAL_LOGFILE.stats $S3_LOGFILE.stats


# end timestamp
OVERALL_STOP_TIME=$(date +%s)
echo
echo
echo "total time:" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)/60)) "minutes and" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)%60)) "seconds"
echo
echo `date +"%D"` `date +"%T"`
echo
echo

