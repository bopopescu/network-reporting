#!/bin/bash
pushd /tmp

rm -rf datastore
appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore 
appcfg.py upload_data --email=foo@bar.com --filename=datastore --application=mopub-inc --url=http://localhost:8000/remote_api
