#!/bin/bash

LOG_ROOT_DIR=~/aws_logs
rm -f $LOG_ROOT_DIR/request-logfile
echo
echo `date +"%D"` `date +"%T"`
echo $LOG_ROOT_DIR/request-logfile "deleted" 
echo

