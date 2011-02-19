#!/bin/bash
cd /home/ubuntu/eventrackerscaletest
python utils/loadtest.py -n $1 -t $2 -d $3 -l $4 -i $5 -e $6 > file.out