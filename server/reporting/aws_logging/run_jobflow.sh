#!/bin/bash
PATH=$PATH:~/google_appengine


# set AWS credentials for boto
export AWS_ACCESS_KEY_ID=AKIAJKOJXDCZA3VYXP3Q
export AWS_SECRET_ACCESS_KEY=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

# download logs from GAE
echo N47935 | appcfg.py --version=$1 --no_cookies --email=olp@mopub.com --passin --append --num_days=1 request_logs ~/src/server ~/logs/request-logfile-1
echo
echo N47935 | appcfg.py --version=$2 --no_cookies --email=olp@mopub.com --passin --append --num_days=1 request_logs ~/src/server ~/logs/request-logfile-2
echo

# combine logfiles
echo
echo "merging log files to" $LOCAL_LOGFILE "..."
#LOGFILE=logfile-`date +"%Y%m%d-%H%M%S"`
LOGFILE=aws-logfile-`date +"%Y%m%d"`
LOCAL_LOGFILE=~/logs/$LOGFILE
S3_LOGFILE=s3://log-counts/test/logs/$LOGFILE
cat ~/logs/request-logfile-1 ~/logs/request-logfile-2 > $LOCAL_LOGFILE

# upload new logs to S3
echo 
echo "uploading to S3..."
s3cmd put $LOCAL_LOGFILE $S3_LOGFILE

# submit and run job
echo
python job_submitter.py -f $S3_LOGFILE #-n 3

# download output files from S3 and merge them into one
echo 
echo "making tmp directory..."
mkdir tmp
echo "downloading output files from S3..."
s3cmd get $S3_LOGFILE.out/part-* tmp
echo "merging output files to" $LOCAL_LOGFILE.out "..."
cat tmp/part-* > $LOCAL_LOGFILE.out
echo "removing tmp directory..."
rm -rf tmp

# parse MR output and update StatsModels in GAE datastore
python stats_updater.py -f $LOCAL_LOGFILE.out 




#echo; START_TIME=$(date +%s); echo "START="$START_TIME; echo; python stats_updater.py -f ~/logs/logfile-20110324-191951.out; STOP_TIME=$(date +%s); echo "STOP =" $STOP_TIME; echo "=========";echo "LATENCY=" $((STOP_TIME-START_TIME));


