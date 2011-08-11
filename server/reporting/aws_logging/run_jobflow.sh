#!/bin/bash
PATH=~/mopub/server/reporting/aws_logging:$PATH:/usr/local/bin:~/google_appengine
# echo $PATH

if [ $# == 0 ]; then    # no args passed in; default to yesterday's day stamp
    YEAR=`date -d yesterday +%Y`   # 2011
    if [ ${#YEAR} != 4 ]; then # if lengh is not right, try Mac OS way of using date 
        YEAR=`date -v-1d +%Y`
    fi

    MONTH_DAY=`date -d yesterday +%m%d`   # 0622
    if [ ${#MONTH_DAY} != 4 ]; then # if lengh is not right, try Mac OS way of using date 
        MONTH_DAY=`date -v-1d +%m%d`
    fi
elif [ $# == 1 ]; then    # only month_day is passed in
    YEAR=2011
    MONTH_DAY=$1
else
    YEAR=$1
    MONTH_DAY=$2
fi

    
# download logs for yesterday
download_logs.sh $YEAR $MONTH_DAY

# TIMESTAMP=`date +"%Y-%m%d-%H%M"`
# DAYSTAMP=`date +"%Y-%m%d"`

DAYSTAMP=$YEAR-$MONTH_DAY   # 2011-0622
TIMESTAMP=$DAYSTAMP-0000-full   # 2011-0622-0000-full


APP_DIR=~/mopub/server
LOG_ROOT_DIR=~/aws_logs #-$DAYSTAMP
LOG_DIR=$LOG_ROOT_DIR/logs-$TIMESTAMP # to minute resolution, so every run is siloed completely

S3_BUCKET=s3://mopub-aws-logging
S3_CODE_DIR=$S3_BUCKET/code4
<<<<<<< HEAD
S3_LOG_DIR=$S3_BUCKET/tmp4/logs-$DAYSTAMP
=======
S3_LOG_DIR=$S3_BUCKET/tmp4/logs-$DAYSTAMP-full
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c

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


# download deref cache from S3 (if it exists) and replace local one
<<<<<<< HEAD
echo
echo "downloading existing deref cache from S3..."
s3cmd get --force $S3_CODE_DIR/deref_cache.pkl $APP_DIR/reporting/aws_logging/deref_cache.pkl


# download logs from GAE
START_TIME=$(date +%s)
echo
echo N47935 | custom-appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 --verbose request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
#echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=3 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
=======
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
echo
echo "downloading existing deref cache from S3..."
s3cmd get --force $S3_CODE_DIR/deref_cache.pkl $APP_DIR/reporting/aws_logging/deref_cache.pkl


# re-hydrate deref_cache
echo
echo "re-hydrating deref cache..."
python $APP_DIR/reporting/aws_logging/hydrate_deref_cache.py


<<<<<<< HEAD
# split input files
echo
echo "splitting" $LOG_ROOT_DIR/request-logfile "..."
split -l $SPLIT_SIZE $LOG_ROOT_DIR/request-logfile $LOG_DIR/chunk-$TIMESTAMP.
=======
# upload updated deref cache to S3
echo
echo "uploading" $APP_DIR/reporting/aws_logging/deref_cache.pkl "to" $S3_CODE_DIR/ "..."
s3cmd put $APP_DIR/reporting/aws_logging/deref_cache.pkl $S3_CODE_DIR/ 


# # download logs from GAE
# START_TIME=$(date +%s)
# echo
# echo N47935 | custom-appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 --verbose request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
# #echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=3 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
# echo
# STOP_TIME=$(date +%s)
# echo
# echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"


# # split input files
# echo
# echo "splitting" $LOG_ROOT_DIR/request-logfile "..."
# split -l $SPLIT_SIZE $LOG_ROOT_DIR/request-logfile $LOG_DIR/chunk-$TIMESTAMP.


# # upload new logs to S3
# START_TIME=$(date +%s)
# echo
# echo "uploading" $LOG_DIR/chunk-$TIMESTAMP".* to" $S3_LOGFILE.raw/ "..."
# s3cmd put $LOG_DIR/chunk-$TIMESTAMP.* $S3_LOGFILE.raw/
# STOP_TIME=$(date +%s)
# echo
# echo "uploading logs to S3 took" $((STOP_TIME-START_TIME)) "seconds"
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c


# submit and run job
START_TIME=$(date +%s)
echo
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -i $S3_LOGFILE -n 20
STOP_TIME=$(date +%s)
echo "EMR job took" $((STOP_TIME-START_TIME)) "seconds"


# # remove local chunk files to save space
# echo
# echo "deleting local chunk log files at" $LOG_DIR
# rm $LOG_DIR/*


#### Basic Log Counts ####
# download basic log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
<<<<<<< HEAD
echo "submitting EMR job..."
python $APP_DIR/reporting/aws_logging/job_submitter.py -i $S3_LOGFILE #-n 10
=======
echo "downloading log counts output files from S3..."
s3cmd get $S3_LOGFILE.basic.dd.out/part-* $LOG_DIR
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
STOP_TIME=$(date +%s)
echo "downloading log counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.basic.lc.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.basic.lc.stats


# deleting local and remote log counts S3 output files 
echo
echo "deleting local log counts S3 part files at" $LOG_DIR.basic.dd.out
rm -rf $LOG_DIR/part-*
echo "deleting remote log counts S3 part files at" $S3_LOGFILE.basic.dd.out
s3cmd del --recursive $S3_LOGFILE.basic.dd.out
##########################


<<<<<<< HEAD
#### Basic Log Counts ####
# download basic log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
echo "downloading log counts output files from S3..."
s3cmd get $S3_LOGFILE.basic.dd.out/part-* $LOG_DIR
STOP_TIME=$(date +%s)
echo "downloading log counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.basic.lc.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.basic.lc.stats


# deleting local and remote log counts S3 output files 
echo
echo "deleting local log counts S3 part files at" $LOG_DIR.basic.dd.out
rm -rf $LOG_DIR/part-*
echo "deleting remote log counts S3 part files at" $S3_LOGFILE.basic.dd.out
s3cmd del --recursive $S3_LOGFILE.basic.dd.out
##########################


=======
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c
#### Advanced Log Counts ####
# download advanced log counts output files from S3 and merge them into one
START_TIME=$(date +%s)
echo
echo "downloading log counts output files from S3..."
s3cmd get $S3_LOGFILE.advanced.dd.out/part-* $LOG_DIR
STOP_TIME=$(date +%s)
echo "downloading log counts S3 output files took" $((STOP_TIME-START_TIME)) "seconds"
echo
echo "merging output files to" $LOCAL_LOGFILE.adv.lc.stats "..."
cat $LOG_DIR/part-* > $LOCAL_LOGFILE.adv.lc.stats


# deleting local and remote log counts S3 output files 
echo
echo "deleting local log counts S3 part files at" $LOG_DIR.advanced.dd.out
rm -rf $LOG_DIR/part-*
echo "deleting remote log counts S3 part files at" $S3_LOGFILE.advanced.dd.out
s3cmd del --recursive $S3_LOGFILE.advanced.dd.out
############################


#### Uniq User ####
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
################
<<<<<<< HEAD


# split advanced log counts stats file by account: log+YYMMDD+<account>+.adv.lc.stats
echo
echo "splitting" $LOCAL_LOGFILE.adv.lc.stats " by day and account..."
python $APP_DIR/reporting/aws_logging/stats_splitter.py -f $LOCAL_LOGFILE.adv.lc.stats


# update advanced log counts stats files to blobstore and update BlogLog model
echo
echo "uploading split files in" $LOG_DIR "to blobstore"
python $APP_DIR/reporting/aws_logging/blob_uploader.py -d $LOG_DIR


# parse basic log counts MR output and update StatsModels in GAE datastore
START_TIME=$(date +%s)
echo
echo "updating log counts in GAE datastore..."
python $APP_DIR/reporting/aws_logging/stats_updater.py -f $LOCAL_LOGFILE.basic.lc.stats -n 8
STOP_TIME=$(date +%s)
echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"
=======


# split advanced log counts stats file by account: log+YYMMDD+<account>+.adv.lc.stats
echo
echo "splitting" $LOCAL_LOGFILE.adv.lc.stats " by day and account..."
python $APP_DIR/reporting/aws_logging/stats_splitter.py -f $LOCAL_LOGFILE.adv.lc.stats
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c


# update advanced log counts stats files to blobstore and update BlogLog model
echo
<<<<<<< HEAD
echo "updating uniq user counts in GAE datastore..."
python $APP_DIR/reporting/aws_logging/uniq_user_stats_updater.py -f $LOCAL_LOGFILE.uu.stats -n 8
STOP_TIME=$(date +%s)
echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"
=======
echo "uploading split files in" $LOG_DIR "to blobstore"
python $APP_DIR/reporting/aws_logging/blob_uploader.py -d $LOG_DIR


# # parse basic log counts MR output and update StatsModels in GAE datastore
# START_TIME=$(date +%s)
# echo
# echo "updating log counts in GAE datastore..."
# python $APP_DIR/reporting/aws_logging/stats_updater.py -f $LOCAL_LOGFILE.basic.lc.stats -n 8
# STOP_TIME=$(date +%s)
# echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"
# 
# 
# # parse uniq user counts MR output and update StatsModels in GAE datastore
# START_TIME=$(date +%s)
# echo
# echo "updating uniq user counts in GAE datastore..."
# python $APP_DIR/reporting/aws_logging/uniq_user_stats_updater.py -f $LOCAL_LOGFILE.uu.stats -n 8
# STOP_TIME=$(date +%s)
# echo "updating GAE datastore took" $((STOP_TIME-START_TIME)) "seconds"
>>>>>>> 7d9a671ae089e06e54dc73254ab42b44ab758e4c


# uploading stats files to S3
echo
echo "uploading basic log counts stats file to" $S3_LOGFILE.basic.lc.stats
s3cmd put $LOCAL_LOGFILE.basic.lc.stats $S3_LOGFILE.basic.lc.stats
echo
echo "uploading advanced log counts stats file to" $S3_LOGFILE.adv.lc.stats
s3cmd put $LOCAL_LOGFILE.adv.lc.stats $S3_LOGFILE.adv.lc.stats
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
