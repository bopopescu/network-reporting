#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=10 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id


EC2_IPS="ec2-50-16-61-151.compute-1.amazonaws.com
ec2-184-73-74-71.compute-1.amazonaws.com
ec2-50-17-12-94.compute-1.amazonaws.com
ec2-184-72-151-215.compute-1.amazonaws.com
ec2-50-16-108-196.compute-1.amazonaws.com
ec2-184-72-163-210.compute-1.amazonaws.com
ec2-204-236-207-10.compute-1.amazonaws.com
ec2-50-16-140-95.compute-1.amazonaws.com
ec2-50-16-28-242.compute-1.amazonaws.com
ec2-50-16-158-239.compute-1.amazonaws.com
ec2-75-101-202-173.compute-1.amazonaws.com
ec2-50-16-94-52.compute-1.amazonaws.com
ec2-184-72-205-159.compute-1.amazonaws.com
ec2-67-202-33-80.compute-1.amazonaws.com
ec2-50-17-29-71.compute-1.amazonaws.com
ec2-50-16-16-41.compute-1.amazonaws.com
ec2-50-16-153-69.compute-1.amazonaws.com
ec2-184-72-179-12.compute-1.amazonaws.com
ec2-72-44-58-168.compute-1.amazonaws.com
ec2-50-16-138-99.compute-1.amazonaws.com
ec2-50-16-121-29.compute-1.amazonaws.com
ec2-174-129-70-74.compute-1.amazonaws.com
ec2-184-73-46-101.compute-1.amazonaws.com
ec2-50-16-174-87.compute-1.amazonaws.com
ec2-50-16-178-141.compute-1.amazonaws.com
ec2-50-16-178-87.compute-1.amazonaws.com
ec2-184-73-6-67.compute-1.amazonaws.com
ec2-174-129-191-19.compute-1.amazonaws.com
ec2-75-101-226-45.compute-1.amazonaws.com
ec2-67-202-45-47.compute-1.amazonaws.com
ec2-50-17-21-15.compute-1.amazonaws.com
ec2-50-16-66-216.compute-1.amazonaws.com
ec2-50-16-151-125.compute-1.amazonaws.com
ec2-75-101-255-149.compute-1.amazonaws.com
ec2-50-17-13-213.compute-1.amazonaws.com
ec2-50-16-51-3.compute-1.amazonaws.com
ec2-72-44-41-218.compute-1.amazonaws.com
ec2-184-73-148-144.compute-1.amazonaws.com
ec2-184-72-90-59.compute-1.amazonaws.com
ec2-174-129-180-194.compute-1.amazonaws.com
ec2-50-17-1-190.compute-1.amazonaws.com
ec2-184-73-9-41.compute-1.amazonaws.com
ec2-50-17-23-105.compute-1.amazonaws.com
ec2-50-17-14-246.compute-1.amazonaws.com
ec2-50-17-31-198.compute-1.amazonaws.com
ec2-204-236-245-90.compute-1.amazonaws.com
ec2-174-129-66-120.compute-1.amazonaws.com
ec2-75-101-213-60.compute-1.amazonaws.com
ec2-50-16-140-19.compute-1.amazonaws.com
ec2-50-16-117-146.compute-1.amazonaws.com"

# clear cache
curl http://eventrackerscaletest.appspot.com/counter/test?flush=1
echo
#---------------------
# CNT=0
# for ec2_ip in $EC2_IPS
# do
# echo ${CNT} ${ec2_ip}
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/eventrackerscaletest/utils/loadtest.py ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/utils/loadtest.py
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/eventrackerscaletest/utils/load.sh ubuntu@${ec2_ip}:/home/ubuntu/scripts/load.sh
# CNT=$((CNT+1))
# done
#---------------------
# Calculate number of servers
NUM_SERVERS=0
for ec2_ip in $EC2_IPS
do
    NUM_SERVERS=$((NUM_SERVERS+1))
done

START_TIME=$(date +%s)
echo ${NUM_SERVERS}
CNT=0
SLEEP_TIME=$((DELAY*NUM_THREADS))
for ec2_ip in $EC2_IPS
do
    echo ${CNT} ${ec2_ip}
    THREAD_TIME_AT_PEAK=$(echo "${TIME_AT_PEAK} + (${NUM_SERVERS} -${CNT} -1) * (${SLEEP_TIME} / 60 )" |bc -l)
    echo "THREAD_TIME_AT_PEAK = $THREAD_TIME_AT_PEAK"
    echo ${TEST_ID}
    ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip} "screen -d -m /home/ubuntu/scripts/load.sh ${NUM_THREADS} ${TIME_AT_PEAK} ${DELAY} ${LOGGING} ${CNT} ${TEST_ID}"
    CNT=$((CNT+1))
done
# waits for the last one to finish
# sleep $((2*TIME_AT_PEAK))
sleep $((TIME_AT_PEAK*60+DELAY*NUM_THREADS+60))
STOP_TIME=$(date +%s)
RUNTIME=$((STOP_TIME-START_TIME))
echo RUNTIME is ${RUNTIME}
# Get the counts
CNT=0
for ec2_ip in $EC2_IPS
do
    echo ${CNT}
    echo ${ec2_ip}
    scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/counts.csv counts_${CNT}.csv
    # scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/file.out file_${CNT}.out
    CNT=$((CNT+1))
done
python accuracytest.py