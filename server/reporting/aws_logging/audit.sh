#!/bin/bash
PATH=~/mopub/server/reporting/aws_logging:$PATH:/usr/local/bin:~/google_appengine
echo $PATH

echo
echo BEGIN audit: `date +"%D"` `date +"%T"`
python ~/mopub/server/reporting/aws_logging/audit_log_sorter.py -n 4
echo
echo END audit: `date +"%D"` `date +"%T"`
