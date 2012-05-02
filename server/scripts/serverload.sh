#!/bin/bash
cd /home/ubuntu/server
python load_test.py -n $1 -t $2 -d $3 -l $4 -i $5 -e $6 -x $7 > file.out
