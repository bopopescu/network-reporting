#!/bin/bash -x
#---------------------------------------------
# ec2-describe-instances --filter instance-state-name=running --filter tag:Name=LOAD
NUM_THREADS=40
TIME_AT_PEAK=10 #minutes
DELAY=10 # should be 30, but sometimes i just say fuck it and do 10
LOGGING=3
TEST_ID=$RANDOM # generates a random test id


EC2_IPS="ec2-50-17-74-36.compute-1.amazonaws.com
ec2-75-101-211-236.compute-1.amazonaws.com
ec2-50-16-50-151.compute-1.amazonaws.com
ec2-50-16-27-135.compute-1.amazonaws.com
ec2-50-17-84-150.compute-1.amazonaws.com"

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