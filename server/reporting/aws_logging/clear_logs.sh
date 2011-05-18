#!/bin/bash

LOG_ROOT_DIR=~/aws_logs
# rm -f $LOG_ROOT_DIR/request-logfile
mv $LOG_ROOT_DIR/request-logfile $LOG_ROOT_DIR/request-logfile-yesterday
echo
echo `date +"%D"` `date +"%T"`
# echo $LOG_ROOT_DIR/request-logfile "deleted"
echo $LOG_ROOT_DIR/request-logfile "renamed" 
echo

