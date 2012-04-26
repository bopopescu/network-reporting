#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=20 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id
VERSION=$1


EC2_IPS="ec2-184-73-41-29.compute-1.amazonaws.com
ec2-50-17-51-152.compute-1.amazonaws.com
ec2-50-17-69-135.compute-1.amazonaws.com
ec2-174-129-168-132.compute-1.amazonaws.com
ec2-50-16-46-149.compute-1.amazonaws.com
ec2-174-129-88-171.compute-1.amazonaws.com
ec2-50-17-28-55.compute-1.amazonaws.com
ec2-50-17-47-179.compute-1.amazonaws.com
ec2-50-17-18-172.compute-1.amazonaws.com
ec2-50-16-135-57.compute-1.amazonaws.com
ec2-50-17-30-220.compute-1.amazonaws.com
ec2-184-73-5-67.compute-1.amazonaws.com
ec2-50-17-87-48.compute-1.amazonaws.com
ec2-184-72-89-233.compute-1.amazonaws.com
ec2-50-17-52-85.compute-1.amazonaws.com
ec2-75-101-232-225.compute-1.amazonaws.com
ec2-50-16-64-17.compute-1.amazonaws.com
ec2-72-44-61-200.compute-1.amazonaws.com
ec2-67-202-19-37.compute-1.amazonaws.com
ec2-50-17-3-101.compute-1.amazonaws.com
ec2-50-16-96-235.compute-1.amazonaws.com
ec2-184-72-204-100.compute-1.amazonaws.com
ec2-50-17-83-205.compute-1.amazonaws.com
ec2-50-17-15-238.compute-1.amazonaws.com
ec2-174-129-52-191.compute-1.amazonaws.com
ec2-50-17-83-4.compute-1.amazonaws.com
ec2-50-16-162-87.compute-1.amazonaws.com
ec2-50-16-44-230.compute-1.amazonaws.com
ec2-184-72-163-217.compute-1.amazonaws.com
ec2-67-202-43-150.compute-1.amazonaws.com
ec2-50-16-168-23.compute-1.amazonaws.com
ec2-50-17-50-104.compute-1.amazonaws.com
ec2-174-129-91-149.compute-1.amazonaws.com
ec2-50-16-78-191.compute-1.amazonaws.com
ec2-50-17-76-0.compute-1.amazonaws.com
ec2-50-17-56-219.compute-1.amazonaws.com
ec2-50-16-39-136.compute-1.amazonaws.com
ec2-50-17-43-137.compute-1.amazonaws.com
ec2-72-44-46-195.compute-1.amazonaws.com
ec2-174-129-87-153.compute-1.amazonaws.com
ec2-50-16-8-128.compute-1.amazonaws.com
ec2-184-73-28-85.compute-1.amazonaws.com
ec2-204-236-209-121.compute-1.amazonaws.com
ec2-50-16-53-126.compute-1.amazonaws.com
ec2-184-73-121-172.compute-1.amazonaws.com
ec2-204-236-197-136.compute-1.amazonaws.com
ec2-50-16-82-121.compute-1.amazonaws.com
ec2-184-73-14-230.compute-1.amazonaws.com
ec2-50-16-139-135.compute-1.amazonaws.com
ec2-184-73-31-222.compute-1.amazonaws.com
ec2-50-17-57-220.compute-1.amazonaws.com
ec2-50-16-60-16.compute-1.amazonaws.com
ec2-50-17-49-129.compute-1.amazonaws.com
ec2-174-129-128-74.compute-1.amazonaws.com
ec2-50-17-3-179.compute-1.amazonaws.com
ec2-50-17-16-67.compute-1.amazonaws.com
ec2-50-17-77-77.compute-1.amazonaws.com
ec2-50-17-33-252.compute-1.amazonaws.com
ec2-50-17-59-234.compute-1.amazonaws.com
ec2-50-16-95-157.compute-1.amazonaws.com
ec2-50-16-158-136.compute-1.amazonaws.com
ec2-50-16-134-200.compute-1.amazonaws.com
ec2-50-16-58-233.compute-1.amazonaws.com
ec2-174-129-165-226.compute-1.amazonaws.com
ec2-50-17-15-1.compute-1.amazonaws.com
ec2-75-101-220-197.compute-1.amazonaws.com
ec2-50-17-77-178.compute-1.amazonaws.com
ec2-50-17-83-18.compute-1.amazonaws.com
ec2-50-16-81-12.compute-1.amazonaws.com
ec2-50-17-13-183.compute-1.amazonaws.com
ec2-174-129-160-148.compute-1.amazonaws.com
ec2-50-17-28-8.compute-1.amazonaws.com
ec2-184-73-20-139.compute-1.amazonaws.com
ec2-50-16-77-102.compute-1.amazonaws.com
ec2-50-16-130-194.compute-1.amazonaws.com
ec2-50-17-95-13.compute-1.amazonaws.com
ec2-184-73-8-30.compute-1.amazonaws.com
ec2-50-17-51-253.compute-1.amazonaws.com
ec2-50-16-147-76.compute-1.amazonaws.com
ec2-72-44-50-240.compute-1.amazonaws.com
ec2-174-129-50-8.compute-1.amazonaws.com
ec2-67-202-28-233.compute-1.amazonaws.com
ec2-50-17-51-155.compute-1.amazonaws.com
ec2-67-202-15-196.compute-1.amazonaws.com
ec2-50-17-74-36.compute-1.amazonaws.com
ec2-174-129-105-44.compute-1.amazonaws.com
ec2-174-129-92-48.compute-1.amazonaws.com
ec2-50-16-149-40.compute-1.amazonaws.com
ec2-50-16-180-27.compute-1.amazonaws.com
ec2-174-129-105-37.compute-1.amazonaws.com
ec2-50-16-43-160.compute-1.amazonaws.com
ec2-50-17-85-240.compute-1.amazonaws.com
ec2-75-101-178-106.compute-1.amazonaws.com
ec2-50-16-5-163.compute-1.amazonaws.com
ec2-50-17-70-60.compute-1.amazonaws.com
ec2-204-236-246-26.compute-1.amazonaws.com
ec2-50-17-2-171.compute-1.amazonaws.com
ec2-184-73-101-249.compute-1.amazonaws.com"

# 
# clear cache
# curl http://eventrackerscaletest.appspot.com/counter/test?flush=1
echo
# #---------------------
# CNT=0
# for ec2_ip in $EC2_IPS
# do
# echo ${CNT} ${ec2_ip}
# scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/mopub/server/serverload.sh ubuntu@${ec2_ip}:/home/ubuntu/scripts/serverload.sh
# # scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ~/programs/mopub/eventrackerscaletest/utils/load.sh ubuntu@${ec2_ip}:/home/ubuntu/scripts/load.sh
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
    ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip} "screen -d -m /home/ubuntu/scripts/serverload.sh ${NUM_THREADS} ${TIME_AT_PEAK} ${DELAY} ${LOGGING} ${CNT} ${TEST_ID} ${VERSION}.latest.eventrackerscaletest.appspot.com"
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
