#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=10 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id


EC2_IPS="ec2-174-129-53-157.compute-1.amazonaws.com
ec2-50-17-21-70.compute-1.amazonaws.com
ec2-50-17-15-8.compute-1.amazonaws.com
ec2-50-17-25-48.compute-1.amazonaws.com
ec2-184-73-102-99.compute-1.amazonaws.com
ec2-67-202-55-8.compute-1.amazonaws.com
ec2-50-17-71-223.compute-1.amazonaws.com
ec2-50-16-140-65.compute-1.amazonaws.com
ec2-50-17-69-244.compute-1.amazonaws.com
ec2-184-72-209-254.compute-1.amazonaws.com
ec2-184-72-211-210.compute-1.amazonaws.com
ec2-50-17-73-199.compute-1.amazonaws.com
ec2-50-16-78-123.compute-1.amazonaws.com
ec2-50-17-9-57.compute-1.amazonaws.com
ec2-50-16-139-147.compute-1.amazonaws.com
ec2-50-16-161-127.compute-1.amazonaws.com
ec2-184-72-175-47.compute-1.amazonaws.com
ec2-184-73-85-63.compute-1.amazonaws.com
ec2-50-17-70-194.compute-1.amazonaws.com
ec2-174-129-181-80.compute-1.amazonaws.com
ec2-50-17-53-115.compute-1.amazonaws.com
ec2-75-101-246-201.compute-1.amazonaws.com
ec2-67-202-6-196.compute-1.amazonaws.com
ec2-50-16-25-40.compute-1.amazonaws.com
ec2-50-17-57-56.compute-1.amazonaws.com
ec2-184-72-136-36.compute-1.amazonaws.com
ec2-50-16-183-226.compute-1.amazonaws.com
ec2-184-73-62-63.compute-1.amazonaws.com
ec2-50-17-5-66.compute-1.amazonaws.com
ec2-75-101-171-128.compute-1.amazonaws.com
ec2-184-72-161-50.compute-1.amazonaws.com
ec2-75-101-194-107.compute-1.amazonaws.com
ec2-75-101-234-222.compute-1.amazonaws.com
ec2-184-72-151-108.compute-1.amazonaws.com
ec2-174-129-178-241.compute-1.amazonaws.com
ec2-50-17-40-2.compute-1.amazonaws.com
ec2-184-72-207-131.compute-1.amazonaws.com
ec2-174-129-150-152.compute-1.amazonaws.com
ec2-184-72-148-8.compute-1.amazonaws.com
ec2-50-17-62-5.compute-1.amazonaws.com
ec2-174-129-170-104.compute-1.amazonaws.com
ec2-174-129-69-107.compute-1.amazonaws.com
ec2-184-72-150-74.compute-1.amazonaws.com
ec2-50-16-94-178.compute-1.amazonaws.com
ec2-184-73-38-48.compute-1.amazonaws.com
ec2-67-202-23-131.compute-1.amazonaws.com
ec2-50-17-40-190.compute-1.amazonaws.com
ec2-50-16-102-117.compute-1.amazonaws.com
ec2-50-16-179-220.compute-1.amazonaws.com
ec2-50-16-103-9.compute-1.amazonaws.com
ec2-50-17-33-146.compute-1.amazonaws.com
ec2-50-17-7-55.compute-1.amazonaws.com
ec2-50-17-11-114.compute-1.amazonaws.com
ec2-50-17-71-17.compute-1.amazonaws.com
ec2-50-17-15-1.compute-1.amazonaws.com
ec2-50-17-44-131.compute-1.amazonaws.com
ec2-50-17-10-161.compute-1.amazonaws.com
ec2-50-17-10-201.compute-1.amazonaws.com
ec2-174-129-53-153.compute-1.amazonaws.com
ec2-50-17-13-208.compute-1.amazonaws.com
ec2-50-17-26-90.compute-1.amazonaws.com
ec2-184-73-107-181.compute-1.amazonaws.com
ec2-50-17-35-29.compute-1.amazonaws.com
ec2-50-16-159-247.compute-1.amazonaws.com
ec2-204-236-196-250.compute-1.amazonaws.com
ec2-184-72-84-72.compute-1.amazonaws.com
ec2-184-72-149-17.compute-1.amazonaws.com
ec2-75-101-211-236.compute-1.amazonaws.com
ec2-50-16-152-181.compute-1.amazonaws.com
ec2-204-236-242-66.compute-1.amazonaws.com
ec2-50-17-4-91.compute-1.amazonaws.com
ec2-50-17-4-240.compute-1.amazonaws.com
ec2-184-72-158-40.compute-1.amazonaws.com
ec2-184-72-73-76.compute-1.amazonaws.com
ec2-184-72-151-3.compute-1.amazonaws.com
ec2-67-202-16-79.compute-1.amazonaws.com
ec2-50-17-22-79.compute-1.amazonaws.com
ec2-50-16-169-43.compute-1.amazonaws.com
ec2-174-129-184-212.compute-1.amazonaws.com
ec2-184-72-174-26.compute-1.amazonaws.com
ec2-50-17-21-124.compute-1.amazonaws.com
ec2-50-16-61-1.compute-1.amazonaws.com
ec2-50-16-25-159.compute-1.amazonaws.com
ec2-50-16-179-125.compute-1.amazonaws.com
ec2-174-129-70-199.compute-1.amazonaws.com
ec2-75-101-243-73.compute-1.amazonaws.com
ec2-67-202-7-85.compute-1.amazonaws.com
ec2-174-129-138-91.compute-1.amazonaws.com
ec2-50-16-97-97.compute-1.amazonaws.com
ec2-50-16-139-20.compute-1.amazonaws.com
ec2-184-73-57-130.compute-1.amazonaws.com
ec2-184-72-180-139.compute-1.amazonaws.com
ec2-184-73-90-130.compute-1.amazonaws.com
ec2-204-236-193-69.compute-1.amazonaws.com
ec2-75-101-238-123.compute-1.amazonaws.com
ec2-50-17-72-182.compute-1.amazonaws.com
ec2-174-129-188-112.compute-1.amazonaws.com
ec2-50-17-66-56.compute-1.amazonaws.com
ec2-50-17-65-1.compute-1.amazonaws.com
ec2-50-17-69-95.compute-1.amazonaws.com
ec2-184-73-91-129.compute-1.amazonaws.com
ec2-50-16-57-72.compute-1.amazonaws.com
ec2-50-16-170-226.compute-1.amazonaws.com
ec2-184-72-150-63.compute-1.amazonaws.com
ec2-75-101-197-126.compute-1.amazonaws.com
ec2-50-17-77-247.compute-1.amazonaws.com
ec2-50-17-76-174.compute-1.amazonaws.com
ec2-50-16-1-23.compute-1.amazonaws.com
ec2-50-17-73-183.compute-1.amazonaws.com
ec2-50-17-78-61.compute-1.amazonaws.com
ec2-50-17-78-16.compute-1.amazonaws.com
ec2-50-17-77-156.compute-1.amazonaws.com
ec2-50-17-73-29.compute-1.amazonaws.com
ec2-50-17-75-110.compute-1.amazonaws.com
ec2-50-17-72-95.compute-1.amazonaws.com
ec2-50-16-94-123.compute-1.amazonaws.com
ec2-50-16-117-65.compute-1.amazonaws.com
ec2-184-73-35-137.compute-1.amazonaws.com
ec2-50-17-76-75.compute-1.amazonaws.com
ec2-174-129-77-125.compute-1.amazonaws.com
ec2-184-73-79-138.compute-1.amazonaws.com
ec2-75-101-238-66.compute-1.amazonaws.com
ec2-50-17-77-246.compute-1.amazonaws.com
ec2-50-17-36-170.compute-1.amazonaws.com
ec2-174-129-141-44.compute-1.amazonaws.com
ec2-174-129-115-82.compute-1.amazonaws.com
ec2-50-16-41-150.compute-1.amazonaws.com
ec2-50-16-107-75.compute-1.amazonaws.com
ec2-72-44-44-63.compute-1.amazonaws.com
ec2-50-17-71-104.compute-1.amazonaws.com
ec2-50-16-118-24.compute-1.amazonaws.com
ec2-50-17-30-55.compute-1.amazonaws.com
ec2-174-129-68-30.compute-1.amazonaws.com
ec2-50-16-99-179.compute-1.amazonaws.com
ec2-50-16-41-187.compute-1.amazonaws.com
ec2-50-16-103-139.compute-1.amazonaws.com
ec2-174-129-173-51.compute-1.amazonaws.com
ec2-184-73-57-192.compute-1.amazonaws.com
ec2-50-17-66-239.compute-1.amazonaws.com
ec2-50-17-24-154.compute-1.amazonaws.com
ec2-67-202-18-251.compute-1.amazonaws.com
ec2-184-73-22-202.compute-1.amazonaws.com"

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