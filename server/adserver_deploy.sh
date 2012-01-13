#!/bin/bash
#
# Script for deploying adserver backend on GAE. 
# It first copies the contents to /tmp then uses the appropriate
# app.yaml file.
# Nafis 1/13/2012

echo "copying ./server -> /tmp/server"
pushd ..
cp -r server /tmp/server

cd /tmp/server
echo "copying 'app.adserver.yaml' -> 'app.yaml'"
cp app.adserver.yaml app.yaml
echo "uploading to GAE"
python2.5 appcfg.py update .
echo "copying 'app.frontend.yaml' -> 'app.yaml'"
cp app.frontend.yaml app.yaml
popd