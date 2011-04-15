#!/bin/bash
PATH=$PATH:/usr/local/bin:~/google_appengine

TIMESTAMP=`date +"%Y-%m%d-%H%M"`
DAYSTAMP=`date +"%Y-%m%d"`

APP_DIR=~/mopub/server
LOG_ROOT_DIR=~/aws_logs
LOG_DIR=$LOG_ROOT_DIR/logs-$TIMESTAMP # to minute resolution, so every run is siloed completely

S3_BUCKET=mopub-aws-logging
S3_LOG_DIR=s3://$S3_BUCKET/logs-$DAYSTAMP

LOGFILE=aws-logfile-$TIMESTAMP
LOCAL_LOGFILE=$LOG_DIR/$LOGFILE
S3_LOGFILE=$S3_LOG_DIR/$LOGFILE

SPLIT_SIZE=10000000

# start timestamp
OVERALL_START_TIME=$(date +%s)
echo
echo
echo `date +"%D"` `date +"%T"`
echo
echo

mkdir $LOG_ROOT_DIR
mkdir $LOG_DIR

# download logs from GAE
START_TIME=$(date +%s)
echo
echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
#echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=3 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
echo
STOP_TIME=$(date +%s)
echo
echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"


# preprocess logs for unique user count
echo "preprocessing logs: dereferencing models for uniq user counts..."
START_TIME=$(date +%s)
python $APP_DIR/reporting/aws_logging/log_preprocessor.py -f $LOG_ROOT_DIR/request-logfile -o $LOCAL_LOGFILE.pp
STOP_TIME=$(date +%s)
echo
echo "preprocessing logs took" $((STOP_TIME-START_TIME)) "seconds"


# split input files
echo
echo "splitting " $LOG_ROOT_DIR/request-logfile "..."
split -l $SPLIT_SIZE $LOG_ROOT_DIR/request-logfile $LOG_DIR/chunk-$TIMESTAMP.
echo "splitting " $LOCAL_LOGFILE.pp "..."
split -l $SPLIT_SIZE $LOCAL_LOGFILE.pp $LOG_DIR/pp-chunk-$TIMESTAMP.


# upload new logs to S3
START_TIME=$(date +%s)
echo
echo "uploading" $LOG_DIR/chunk-$TIMESTAMP".* to" $S3_LOG_DIR/$LOGFILE/ "..."
s3cmd put $LOG_DIR/chunk-$TIMESTAMP.* $S3_LOG_DIR/$LOGFILE/
echo
echo "uploading" $LOG_DIR/pp-chunk-$TIMESTAMP".* to" $S3_LOG_DIR/$LOGFILE/ "..."
s3cmd put $LOG_DIR/pp-chunk-$TIMESTAMP.* $S3_LOG_DIR/$LOGFILE/
STOP_TIME=$(date +%s)
echo
echo "uploading logs to S3 took" $((STOP_TIME-START_TIME)) "seconds"


# submit and run job
START_TIME=$(date +%s)
echo
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -l $LOG_DIR -r $S3_LOG_DIR/$LOGFILE -o $S3_LOGFILE -n 100
STOP_TIME=$(date +%s)
echo "EMR job took" $((STOP_TIME-START_TIME)) "seconds"


# remove local preprocessed log file - this file can be much larger than raw downloaded logs
echo
echo "removing" $LOG_DIR/chunk-$TIMESTAMP".*"
rm $LOG_DIR/chunk-$TIMESTAMP.*
echo
echo "removing" $LOG_DIR/pp-chunk-$TIMESTAMP".*"
rm $LOG_DIR/pp-chunk-$TIMESTAMP.*
echo
echo "removing" $LOCAL_LOGFILE.pp
rm $LOCAL_LOGFILE.pp


# download log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
echo "downloading log counts output files from S3..."
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
echo "downloading uniq user counts output files from S3..."
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
echo `date +"%D"` `date +"%T"`    "total runtime:" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)/60)) "minutes and" $(((OVERALL_STOP_TIME-OVERALL_START_TIME)%60)) "seconds"
echo
echo 


