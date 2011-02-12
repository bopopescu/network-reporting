#!/bin/bash
cd /home/ubuntu/eventrackerscaletest
rm -rf file.out
python utils/loadtest.py -n $1 -t $2 -d $3 -l $4 -i $5 >> file.out