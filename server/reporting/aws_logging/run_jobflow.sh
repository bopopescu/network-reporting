#!/bin/bash
PATH=~/mopub/server/reporting/aws_logging:$PATH:/usr/local/bin:~/google_appengine
# echo $PATH

TIMESTAMP=`date +"%Y-%m%d-%H%M"`
DAYSTAMP=`date +"%Y-%m%d"`

APP_DIR=~/mopub/server
LOG_ROOT_DIR=~/aws_logs #-$DAYSTAMP
LOG_DIR=$LOG_ROOT_DIR/logs-$TIMESTAMP # to minute resolution, so every run is siloed completely

S3_BUCKET=s3://mopub-aws-logging
S3_CODE_DIR=$S3_BUCKET/code3
S3_LOG_DIR=$S3_BUCKET/tmp3/logs-$DAYSTAMP

LOGFILE=aws-logfile-$TIMESTAMP
LOCAL_LOGFILE=$LOG_DIR/$LOGFILE
S3_LOGFILE=$S3_LOG_DIR/$LOGFILE

SPLIT_SIZE=5000000

# start timestamp
OVERALL_START_TIME=$(date +%s)
echo
echo
echo BEGIN: `date +"%D"` `date +"%T"`
echo
echo

mkdir $LOG_ROOT_DIR
mkdir $LOG_DIR


# download logs from GAE
# START_TIME=$(date +%s)
# echo
# echo N47935 | ./appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 --verbose request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
# #echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=3 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
# echo
# STOP_TIME=$(date +%s)
# echo
# echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"


# download deref cache from S3 (if it exists) and replace local one
# echo
# echo "downloading existing deref cache from S3..."
# s3cmd get --force $S3_CODE_DIR/deref_cache.pkl $APP_DIR/reporting/aws_logging/deref_cache.pkl 


# build up deref cache for log preprocessing
# echo
# python $APP_DIR/reporting/aws_logging/deref_cache_builder.py -f $LOG_ROOT_DIR/request-logfile 


# upload updated deref cache to S3
echo
echo "uploading" $APP_DIR/reporting/aws_logging/deref_cache.pkl "to" $S3_CODE_DIR/ "..."
s3cmd put $APP_DIR/reporting/aws_logging/deref_cache.pkl $S3_CODE_DIR/ 


# split input files
echo
echo "splitting" $LOG_ROOT_DIR/request-logfile "..."
split -l $SPLIT_SIZE $LOG_ROOT_DIR/request-logfile $LOG_DIR/chunk-$TIMESTAMP.


# upload new logs to S3
START_TIME=$(date +%s)
echo
echo "uploading" $LOG_DIR/chunk-$TIMESTAMP".* to" $S3_LOGFILE.raw/ "..."
s3cmd put $LOG_DIR/chunk-$TIMESTAMP.* $S3_LOGFILE.raw/
STOP_TIME=$(date +%s)
echo
echo "uploading logs to S3 took" $((STOP_TIME-START_TIME)) "seconds"


# submit and run job
START_TIME=$(date +%s)
echo
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -i $S3_LOGFILE -n 10
STOP_TIME=$(date +%s)
echo "EMR job took" $((STOP_TIME-START_TIME)) "seconds"


# remove local chunk files to save space
echo
echo "deleting local chunk log files at" $LOG_DIR
rm $LOG_DIR/*


# download log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
echo "downloading log counts output files from S3..."
s3cmd get $S3_LOGFILE.dd.out/part-* $LOG_DIR
STOP_TIME=$(date +%s)
echo "downloading log counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.stats


# deleting local and remote log counts S3 output files 
echo
echo "deleting local log counts S3 part files at" $LOG_DIR.dd.out
rm -rf $LOG_DIR/part-*
echo "deleting remote log counts S3 part files at" $S3_LOGFILE.dd.out
s3cmd del --recursive $S3_LOGFILE.dd.out


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
echo "deleting local uniq user counts S3 part files at" $LOG_DIR.pp.out
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
