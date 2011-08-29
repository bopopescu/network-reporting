#! /bin/sh
echo "Starting up the poller..."
sudo -b -i python /home/ubuntu/mopub/server/reports/aws_reports/queue_poller.py
