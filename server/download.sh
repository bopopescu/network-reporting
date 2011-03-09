#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

pushd /tmp

# rm -rf /Users/njamal/tmp/datastore0
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore0 --kind=User --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore1 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm -rf /Users/njamal/tmp/datastore1
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore1 --kind=Account --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore1 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm /Users/njamal/tmp/datastore2
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore2 --kind=App --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore2 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm /Users/njamal/tmp/datastore3
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore3 --kind=Site --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore3 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm /Users/njamal/tmp/datastore4
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore4 --kind=Campaign --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore4 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm /Users/njamal/tmp/datastore5
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore5 --kind=AdGroup --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore5 --application=mopub-inc --url=http://localhost:8000/remote_api

# rm /Users/njamal/tmp/datastore6
# appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/njamal/tmp/datastore6 --kind=Creative --email=nafisjamal@mopub.com
appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/njamal/tmp/datastore6 --application=mopub-inc --url=http://localhost:8000/remote_api
