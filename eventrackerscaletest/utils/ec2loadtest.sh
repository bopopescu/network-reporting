#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=20 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3

EC2_IPS="ec2-184-73-114-35.compute-1.amazonaws.com
ec2-184-72-156-173.compute-1.amazonaws.com
ec2-184-72-136-250.compute-1.amazonaws.com
ec2-184-73-81-201.compute-1.amazonaws.com
ec2-50-16-152-181.compute-1.amazonaws.com
ec2-50-16-82-9.compute-1.amazonaws.com
ec2-50-16-161-127.compute-1.amazonaws.com
ec2-67-202-26-231.compute-1.amazonaws.com
ec2-50-16-145-13.compute-1.amazonaws.com
ec2-184-73-14-21.compute-1.amazonaws.com
ec2-174-129-46-10.compute-1.amazonaws.com
ec2-184-72-213-16.compute-1.amazonaws.com
ec2-184-72-204-32.compute-1.amazonaws.com
ec2-174-129-123-132.compute-1.amazonaws.com
ec2-204-236-201-238.compute-1.amazonaws.com
ec2-184-72-206-170.compute-1.amazonaws.com
ec2-174-129-60-124.compute-1.amazonaws.com
ec2-50-16-125-149.compute-1.amazonaws.com
ec2-50-16-172-203.compute-1.amazonaws.com
ec2-184-72-199-82.compute-1.amazonaws.com
ec2-50-16-126-8.compute-1.amazonaws.com
ec2-50-16-141-126.compute-1.amazonaws.com
ec2-50-16-51-186.compute-1.amazonaws.com
ec2-184-72-149-17.compute-1.amazonaws.com
ec2-184-73-141-17.compute-1.amazonaws.com
ec2-50-16-170-213.compute-1.amazonaws.com
ec2-50-16-106-221.compute-1.amazonaws.com
ec2-50-16-109-20.compute-1.amazonaws.com
ec2-184-72-175-47.compute-1.amazonaws.com
ec2-50-17-25-52.compute-1.amazonaws.com
ec2-75-101-197-108.compute-1.amazonaws.com
ec2-204-236-208-227.compute-1.amazonaws.com
ec2-50-16-69-151.compute-1.amazonaws.com
ec2-50-17-27-112.compute-1.amazonaws.com
ec2-204-236-240-245.compute-1.amazonaws.com
ec2-174-129-94-82.compute-1.amazonaws.com
ec2-174-129-144-184.compute-1.amazonaws.com
ec2-75-101-187-7.compute-1.amazonaws.com
ec2-50-16-144-72.compute-1.amazonaws.com
ec2-50-16-182-102.compute-1.amazonaws.com
ec2-184-73-18-109.compute-1.amazonaws.com
ec2-184-73-30-229.compute-1.amazonaws.com
ec2-184-72-168-8.compute-1.amazonaws.com
ec2-50-17-16-182.compute-1.amazonaws.com
ec2-50-16-21-70.compute-1.amazonaws.com
ec2-184-72-150-74.compute-1.amazonaws.com
ec2-50-16-31-53.compute-1.amazonaws.com
ec2-50-16-146-203.compute-1.amazonaws.com
ec2-50-17-22-226.compute-1.amazonaws.com
ec2-184-73-139-194.compute-1.amazonaws.com
ec2-50-17-33-92.compute-1.amazonaws.com
ec2-184-72-90-198.compute-1.amazonaws.com
ec2-50-16-130-3.compute-1.amazonaws.com
ec2-50-16-135-149.compute-1.amazonaws.com
ec2-50-16-84-178.compute-1.amazonaws.com
ec2-72-44-55-206.compute-1.amazonaws.com
ec2-50-16-84-162.compute-1.amazonaws.com
ec2-50-17-28-105.compute-1.amazonaws.com
ec2-50-16-8-86.compute-1.amazonaws.com
ec2-184-73-151-10.compute-1.amazonaws.com
ec2-50-17-10-201.compute-1.amazonaws.com
ec2-50-16-155-196.compute-1.amazonaws.com
ec2-50-16-121-17.compute-1.amazonaws.com
ec2-184-73-44-170.compute-1.amazonaws.com
ec2-50-16-48-38.compute-1.amazonaws.com
ec2-184-72-155-167.compute-1.amazonaws.com
ec2-184-73-145-81.compute-1.amazonaws.com
ec2-204-236-196-250.compute-1.amazonaws.com
ec2-184-72-84-72.compute-1.amazonaws.com
ec2-204-236-201-61.compute-1.amazonaws.com
ec2-50-17-36-35.compute-1.amazonaws.com
ec2-50-17-17-170.compute-1.amazonaws.com
ec2-50-17-4-240.compute-1.amazonaws.com
ec2-50-17-29-130.compute-1.amazonaws.com
ec2-184-72-195-94.compute-1.amazonaws.com
ec2-174-129-150-96.compute-1.amazonaws.com
ec2-50-17-22-79.compute-1.amazonaws.com
ec2-50-16-1-252.compute-1.amazonaws.com
ec2-184-73-122-73.compute-1.amazonaws.com
ec2-50-16-169-224.compute-1.amazonaws.com
ec2-50-16-35-218.compute-1.amazonaws.com
ec2-50-16-159-192.compute-1.amazonaws.com
ec2-67-202-9-99.compute-1.amazonaws.com
ec2-67-202-19-5.compute-1.amazonaws.com
ec2-67-202-13-164.compute-1.amazonaws.com
ec2-50-16-2-11.compute-1.amazonaws.com
ec2-75-101-232-141.compute-1.amazonaws.com
ec2-50-16-18-234.compute-1.amazonaws.com
ec2-174-129-70-199.compute-1.amazonaws.com
ec2-75-101-243-73.compute-1.amazonaws.com
ec2-174-129-60-229.compute-1.amazonaws.com
ec2-50-17-36-123.compute-1.amazonaws.com
ec2-184-73-10-21.compute-1.amazonaws.com
ec2-67-202-41-63.compute-1.amazonaws.com
ec2-50-16-175-111.compute-1.amazonaws.com
ec2-50-16-59-245.compute-1.amazonaws.com
ec2-50-17-20-1.compute-1.amazonaws.com
ec2-184-72-72-239.compute-1.amazonaws.com
ec2-50-16-112-210.compute-1.amazonaws.com
ec2-184-72-173-216.compute-1.amazonaws.com"

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
    ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ~/.ec2/jpmopub-keypair ubuntu@${ec2_ip} "screen -d -m /home/ubuntu/scripts/load.sh ${NUM_THREADS} ${TIME_AT_PEAK} ${DELAY} ${LOGGING} ${CNT}"
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