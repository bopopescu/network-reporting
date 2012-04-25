#!/bin/bash
PATH=~/mopub/server/reporting/aws_logging:$PATH:/usr/local/bin:~/google_appengine

INPUT_DAY=$1$2
DAYSTAMP=$1-$2
echo "download logs for day" $DAYSTAMP

APP_DIR=~/mopub/server
LOG_ROOT_DIR=~/aws_logs 
LOG_DIR=$LOG_ROOT_DIR/day-$DAYSTAMP

S3_BUCKET=s3://mopub-aws-logging
S3_LOG_DIR=$S3_BUCKET/tmp4/logs-$DAYSTAMP-full/aws-logfile-$DAYSTAMP-0000-full.raw


# parallel downloading of yeterday's blog logs from GAE blobstore
python $APP_DIR/reporting/aws_logging/blob_log_downloader.py -t $INPUT_DAY -n 32

HOUR_DIRS=`ls $LOG_DIR`

mkdir $LOG_DIR/totals

for hour_dir in $HOUR_DIRS
do
    if [ ${#hour_dir} != 6 ]; then  # not the totals directory
        echo "cat-ing" $LOG_DIR/$hour_dir/ "..." 
        cat $LOG_DIR/$hour_dir/* > $LOG_DIR/totals/$hour_dir.blog
    fi
done

# upload totals to S3
s3cmd put $LOG_DIR/totals/* $S3_LOG_DIR/
