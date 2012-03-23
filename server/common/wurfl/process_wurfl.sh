#!/bin/bash

# start timestamp
OVERALL_START_TIME=$(date +%s)


# Because locale (ex: en-US) adds noise to device search via user-agent, strip out all locales (ex: en-US) 
# from wurfl.xml and create new file wurfl.xml.no_loc:
echo 
echo "removing locale from user-agent strings..."
echo "input:  wurfl.xml"
echo "output: wurfl_no_locale.xml"
python locale_remover.py -i wurfl.xml -o wurfl_no_locale.xml


# Generate the wurfl.py file from wurfl.xml.no_loc:
echo
echo "converting xml to py ..."
echo "input:  wurfl_no_locale.xml"
echo "output: wurfl.py"
python wurfl2python.py wurfl_no_locale.xml 


# Extract out device info from wurfl.py and pickle a dictionary 
# (k: devid, v: [brand_name, marketing_name, device_os, device_os_version]) to devices.pkl:
echo
echo "extracting out device info..."
echo "input:  wurfl.py"
echo "output: 10 pickle files"
python device_extractor.py


# Make a copy and put it in the server/reporting/aws_logging/ directory (needed for EMR)
echo
echo "copied wurfl.py to ../../reporting/aws_logging/ for EMR"
cp wurfl.py ../../reporting/aws_logging/


# end timestamp
OVERALL_STOP_TIME=$(date +%s)
echo
echo "WURFL processing took" $((OVERALL_STOP_TIME-OVERALL_START_TIME)) "seconds"
echo
