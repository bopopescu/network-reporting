#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

pushd /tmp
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore0 --email=olp@mopub.com --passin
appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore0 --application=mopub-inc --url=http://localhost:8000/remote_api
