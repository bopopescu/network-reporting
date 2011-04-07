#!/bin/bash
PATH=$PATH:/usr/local/bin:~/google_appengine

APP_DIR=~/mopub/server
LOG_DIR=~/aws_logs
S3_BUCKET=mopub-aws-logging
S3_LOG_DIR=s3://$S3_BUCKET/logs-`date +"%Y-%m%d"`

LOGFILE=testing-aws-logfile-`date +"%Y-%m%d-%H%M"`
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

# download logs from GAE
START_TIME=$(date +%s)
#echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 request_logs $APP_DIR $LOG_DIR/request-logfile
echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=10 request_logs $APP_DIR $LOG_DIR/request-logfile
echo
STOP_TIME=$(date +%s)
echo
echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"


# copy accumulated logs to new log file
echo
echo "copying downloaded logs to" $LOCAL_LOGFILE "as input to EMR..."
echo
cp $LOG_DIR/request-logfile $LOCAL_LOGFILE


# preprocess logs for unique user count
echo "preprocessing logs: dereferencing models for uniq user counts..."
START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/log_preprocessor.py -f $LOCAL_LOGFILE
STOP_TIME=$(date +%s)
echo
echo "preprocessing logs took" $((STOP_TIME-START_TIME)) "seconds"


# upload new logs to S3
START_TIME=$(date +%s)
echo
echo "uploading" $LOCAL_LOGFILE "to" $S3_LOGFILE "..."
s3cmd put $LOCAL_LOGFILE $S3_LOGFILE
echo
echo "uploading" $LOCAL_LOGFILE.pp "to" $S3_LOGFILE.pp "..."
s3cmd put $LOCAL_LOGFILE.pp $S3_LOGFILE.pp
STOP_TIME=$(date +%s)
echo "uploading logs to S3 took" $((STOP_TIME-START_TIME)) "seconds"


# submit and run job
START_TIME=$(date +%s)
echo
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -f $S3_LOGFILE -n 10
STOP_TIME=$(date +%s)
echo "EMR job took" $((STOP_TIME-START_TIME)) "seconds"


# download log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
s3cmd get $S3_LOGFILE.out/part-* $LOG_DIR
STOP_TIME=$(date +%s)
echo "downloading log counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.stats


# deleting local and remote log counts S3 output files 
echo
echo "deleting local log counts S3 part files at" $LOG_DIR
rm -rf $LOG_DIR/part-*
echo "deleting remote log counts S3 part files at" $S3_LOGFILE.out
s3cmd del --recursive $S3_LOGFILE.out


# download uniq user counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
s3cmd get $S3_LOGFILE.pp.out/part-* $LOG_DIR
STOP_TIME=$(date +%s)
echo "downloading uniq user counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.uu.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.uu.stats


# deleting local and remote uniq user counts S3 output files 
echo
echo "deleting local uniq user counts S3 part files at" $LOG_DIR
rm -rf $LOG_DIR/part-*
echo "deleting remote uniq user counts S3 part files at" $S3_LOGFILE.pp.out
s3cmd del --recursive $S3_LOGFILE.pp.out


# parse log counts MR output and update StatsModels in GAE datastore
START_TIME=$(date +%s)
echo
echo "updating log counts in GAE datastore..."
python $APP_DIR/reporting/aws_logging/stats_updater.py -f $LOCAL_LOGFILE.stats 
STOP_TIME=$(date +%s)
echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"


# parse uniq user counts MR output and update StatsModels in GAE datastore
START_TIME=$(date +%s)
echo
echo "updating uniq user counts in GAE datastore..."
python $APP_DIR/reporting/aws_logging/uniq_user_stats_updater.py -f $LOCAL_LOGFILE.uu.stats 
STOP_TIME=$(date +%s)
echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"


# uploading stats files to S3
echo
echo "uploading log counts stats file to" $S3_LOGFILE.stats
s3cmd put $LOCAL_LOGFILE.stats $S3_LOGFILE.stats
echo
echo "uploading uniq user counts stats file to" $S3_LOGFILE.uu.stats
s3cmd put $LOCAL_LOGFILE.uu.stats $S3_LOGFILE.uu.stats


# end timestamp
OVERALL_STOP_TIME=$(date +%s)
echo
echo
echo "total time:" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)/60)) "minutes and" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)%60)) "seconds"
echo
echo `date +"%D"` `date +"%T"`
echo
echo

