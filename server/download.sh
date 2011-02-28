#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

pushd /tmp

rm -rf datastore
appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore 
appcfg.py upload_data --email=foo@bar.com --filename=datastore --application=mopub-inc --url=http://localhost:8000/remote_api
