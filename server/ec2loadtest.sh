#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=5 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id


EC2_IPS="ec2-50-17-36-206.compute-1.amazonaws.com
ec2-50-16-68-156.compute-1.amazonaws.com
ec2-50-17-56-91.compute-1.amazonaws.com
ec2-50-17-58-11.compute-1.amazonaws.com
ec2-50-16-49-234.compute-1.amazonaws.com"
# ec2-50-16-79-14.compute-1.amazonaws.com
# ec2-184-72-182-224.compute-1.amazonaws.com
# ec2-50-17-54-235.compute-1.amazonaws.com
# ec2-50-16-155-161.compute-1.amazonaws.com
# ec2-50-17-68-158.compute-1.amazonaws.com
# ec2-75-101-205-107.compute-1.amazonaws.com
# ec2-174-129-149-249.compute-1.amazonaws.com
# ec2-50-16-158-154.compute-1.amazonaws.com
# ec2-50-16-84-137.compute-1.amazonaws.com
# ec2-50-16-100-5.compute-1.amazonaws.com
# ec2-184-72-185-86.compute-1.amazonaws.com
# ec2-50-16-13-176.compute-1.amazonaws.com
# ec2-50-16-38-28.compute-1.amazonaws.com
# ec2-50-16-28-67.compute-1.amazonaws.com
# ec2-50-16-25-54.compute-1.amazonaws.com
# ec2-67-202-43-109.compute-1.amazonaws.com
# ec2-67-202-12-47.compute-1.amazonaws.com
# ec2-50-16-144-188.compute-1.amazonaws.com
# ec2-50-16-38-252.compute-1.amazonaws.com
# ec2-174-129-175-172.compute-1.amazonaws.com
# ec2-50-17-88-238.compute-1.amazonaws.com
# ec2-50-16-39-121.compute-1.amazonaws.com
# ec2-50-17-78-243.compute-1.amazonaws.com
# ec2-174-129-166-81.compute-1.amazonaws.com
# ec2-50-16-177-98.compute-1.amazonaws.com
# ec2-50-17-17-80.compute-1.amazonaws.com
# ec2-67-202-26-231.compute-1.amazonaws.com
# ec2-50-17-39-118.compute-1.amazonaws.com
# ec2-50-16-7-50.compute-1.amazonaws.com
# ec2-50-17-51-220.compute-1.amazonaws.com
# ec2-50-16-26-250.compute-1.amazonaws.com
# ec2-67-202-28-176.compute-1.amazonaws.com
# ec2-50-16-41-125.compute-1.amazonaws.com
# ec2-174-129-162-12.compute-1.amazonaws.com
# ec2-184-73-63-39.compute-1.amazonaws.com
# ec2-50-17-47-0.compute-1.amazonaws.com
# ec2-174-129-90-67.compute-1.amazonaws.com
# ec2-50-17-33-221.compute-1.amazonaws.com
# ec2-50-17-65-230.compute-1.amazonaws.com
# ec2-50-16-102-227.compute-1.amazonaws.com
# ec2-50-17-56-190.compute-1.amazonaws.com
# ec2-174-129-142-103.compute-1.amazonaws.com
# ec2-50-16-181-195.compute-1.amazonaws.com
# ec2-50-16-152-128.compute-1.amazonaws.com
# ec2-50-16-73-80.compute-1.amazonaws.com
# ec2-50-16-171-200.compute-1.amazonaws.com
# ec2-184-73-39-79.compute-1.amazonaws.com
# ec2-184-72-215-55.compute-1.amazonaws.com
# ec2-184-72-167-22.compute-1.amazonaws.com
# ec2-67-202-13-205.compute-1.amazonaws.com
# ec2-50-17-85-214.compute-1.amazonaws.com
# ec2-67-202-21-9.compute-1.amazonaws.com
# ec2-72-44-41-25.compute-1.amazonaws.com
# ec2-50-16-173-62.compute-1.amazonaws.com
# ec2-50-17-85-217.compute-1.amazonaws.com
# ec2-72-44-59-223.compute-1.amazonaws.com
# ec2-50-16-76-87.compute-1.amazonaws.com
# ec2-75-101-207-107.compute-1.amazonaws.com
# ec2-75-101-191-99.compute-1.amazonaws.com
# ec2-184-72-95-182.compute-1.amazonaws.com
# ec2-50-17-55-71.compute-1.amazonaws.com
# ec2-184-73-39-127.compute-1.amazonaws.com
# ec2-184-73-38-249.compute-1.amazonaws.com
# ec2-72-44-60-35.compute-1.amazonaws.com
# ec2-50-17-17-14.compute-1.amazonaws.com
# ec2-50-16-29-204.compute-1.amazonaws.com
# ec2-50-16-43-117.compute-1.amazonaws.com
# ec2-50-16-87-4.compute-1.amazonaws.com
# ec2-67-202-11-18.compute-1.amazonaws.com
# ec2-67-202-37-58.compute-1.amazonaws.com
# ec2-50-16-158-134.compute-1.amazonaws.com
# ec2-75-101-205-205.compute-1.amazonaws.com
# ec2-50-17-37-7.compute-1.amazonaws.com
# ec2-67-202-53-105.compute-1.amazonaws.com
# ec2-72-44-62-53.compute-1.amazonaws.com
# ec2-184-72-149-130.compute-1.amazonaws.com
# ec2-75-101-206-7.compute-1.amazonaws.com
# ec2-50-17-95-229.compute-1.amazonaws.com
# ec2-174-129-159-84.compute-1.amazonaws.com
# ec2-184-72-84-97.compute-1.amazonaws.com
# ec2-50-16-120-247.compute-1.amazonaws.com
# ec2-75-101-177-153.compute-1.amazonaws.com
# ec2-50-17-69-126.compute-1.amazonaws.com
# ec2-184-73-63-234.compute-1.amazonaws.com
# ec2-50-16-46-134.compute-1.amazonaws.com
# ec2-50-17-95-218.compute-1.amazonaws.com
# ec2-50-16-106-238.compute-1.amazonaws.com
# ec2-184-72-163-136.compute-1.amazonaws.com
# ec2-184-72-91-192.compute-1.amazonaws.com
# ec2-50-16-70-82.compute-1.amazonaws.com
# ec2-50-17-56-152.compute-1.amazonaws.com
# ec2-75-101-184-29.compute-1.amazonaws.com
# ec2-50-17-91-136.compute-1.amazonaws.com
# ec2-67-202-55-110.compute-1.amazonaws.com
# ec2-50-16-47-101.compute-1.amazonaws.com"

# 
# clear cache
# curl http://eventrackerscaletest.appspot.com/counter/test?flush=1
echo
#---------------------
# CNT=0
# for ec2_ip in $EC2_IPS
# do
# echo ${CNT} ${ec2_ip}
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/mopub/server/loadtest.py ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/utils/loadtest.py
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
    ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip} "screen -d -m /home/ubuntu/scripts/serverload.sh ${NUM_THREADS} ${TIME_AT_PEAK} ${DELAY} ${LOGGING} ${CNT} ${TEST_ID}"
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
    scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip}:/home/ubuntu/server/counts.csv counts_${CNT}.csv
    # scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip}:/home/ubuntu/eventrackerscaletest/file_tail.out file_${CNT}.out
    CNT=$((CNT+1))
done
python accuracy_test.py