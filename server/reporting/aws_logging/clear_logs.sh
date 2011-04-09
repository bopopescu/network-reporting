#!/bin/bash

LOG_ROOT_DIR=~/aws_logs
#LOG_ROOT_DIR=/mnt/aws_logs # EC2 path
rm -rf $LOG_ROOT_DIR
echo
echo `date +"%D"` `date +"%T"`
echo $LOG_ROOT_DIR "deleted" 
echo

