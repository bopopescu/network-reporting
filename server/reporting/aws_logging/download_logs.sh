#!/bin/bash
PATH=.:$PATH:/usr/local/bin:~/google_appengine
echo $PATH
pwd


APP_DIR=~/mopub/server
LOG_ROOT_DIR=~/aws_logs 

mkdir $LOG_ROOT_DIR

# download logs from GAE
START_TIME=$(date +%s)
echo
echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --append --num_days=1 --verbose request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
#echo N47935 | appcfg.py --no_cookies --email=olp@mopub.com --passin --num_days=3 request_logs $APP_DIR $LOG_ROOT_DIR/request-logfile
echo
STOP_TIME=$(date +%s)
echo
echo "downloading GAE logs took" $((STOP_TIME-START_TIME)) "seconds"