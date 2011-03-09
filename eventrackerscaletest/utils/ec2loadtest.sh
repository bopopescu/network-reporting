#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=10 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id


EC2_IPS="ec2-50-17-31-91.compute-1.amazonaws.com
ec2-50-16-144-43.compute-1.amazonaws.com
ec2-50-17-64-35.compute-1.amazonaws.com
ec2-50-16-47-116.compute-1.amazonaws.com
ec2-50-16-0-202.compute-1.amazonaws.com
ec2-75-101-232-225.compute-1.amazonaws.com
ec2-184-72-144-137.compute-1.amazonaws.com
ec2-50-17-62-113.compute-1.amazonaws.com
ec2-50-17-38-213.compute-1.amazonaws.com
ec2-75-101-197-78.compute-1.amazonaws.com
ec2-50-17-3-234.compute-1.amazonaws.com
ec2-50-17-94-211.compute-1.amazonaws.com
ec2-50-17-94-200.compute-1.amazonaws.com
ec2-67-202-7-85.compute-1.amazonaws.com
ec2-50-17-64-166.compute-1.amazonaws.com
ec2-75-101-205-63.compute-1.amazonaws.com
ec2-50-17-55-219.compute-1.amazonaws.com
ec2-50-16-29-17.compute-1.amazonaws.com
ec2-50-16-94-108.compute-1.amazonaws.com
ec2-50-17-19-190.compute-1.amazonaws.com
ec2-50-17-72-185.compute-1.amazonaws.com
ec2-50-16-31-189.compute-1.amazonaws.com
ec2-184-72-75-64.compute-1.amazonaws.com
ec2-184-72-75-65.compute-1.amazonaws.com
ec2-50-16-167-146.compute-1.amazonaws.com
ec2-184-73-12-113.compute-1.amazonaws.com
ec2-174-129-74-65.compute-1.amazonaws.com
ec2-50-17-50-232.compute-1.amazonaws.com
ec2-184-72-195-114.compute-1.amazonaws.com
ec2-184-72-215-246.compute-1.amazonaws.com
ec2-50-16-163-239.compute-1.amazonaws.com
ec2-67-202-49-161.compute-1.amazonaws.com
ec2-174-129-181-111.compute-1.amazonaws.com
ec2-50-16-152-50.compute-1.amazonaws.com
ec2-50-16-9-248.compute-1.amazonaws.com
ec2-50-16-120-131.compute-1.amazonaws.com
ec2-50-16-172-26.compute-1.amazonaws.com
ec2-50-16-159-130.compute-1.amazonaws.com
ec2-184-72-163-215.compute-1.amazonaws.com
ec2-75-101-177-174.compute-1.amazonaws.com
ec2-50-17-33-128.compute-1.amazonaws.com
ec2-174-129-61-149.compute-1.amazonaws.com
ec2-50-16-17-197.compute-1.amazonaws.com
ec2-50-17-74-91.compute-1.amazonaws.com
ec2-50-17-89-53.compute-1.amazonaws.com
ec2-50-17-67-27.compute-1.amazonaws.com
ec2-50-16-27-25.compute-1.amazonaws.com
ec2-50-16-176-169.compute-1.amazonaws.com
ec2-174-129-183-138.compute-1.amazonaws.com"



# 
# clear cache
curl http://eventrackerscaletest.appspot.com/counter/test?flush=1
echo
#---------------------
# CNT=0
# for ec2_ip in $EC2_IPS
# do
# echo ${CNT} ${ec2_ip}
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/mopub/eventrackerscaletest/utils/loadtest.py ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/utils/loadtest.py
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/mopub/eventrackerscaletest/utils/load.sh ubuntu@${ec2_ip}:/home/ubuntu/scripts/load.sh
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
    # scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/file_tail.out file_${CNT}.out
    CNT=$((CNT+1))
done
python accuracytest.py