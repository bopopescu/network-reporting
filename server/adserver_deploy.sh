#!/bin/bash
#
# Script for deploying adserver backend on GAE. 
# It first copies the contents to /tmp then uses the appropriate
# app.yaml file.
# Nafis 1/13/2012

pushd ..

echo "copying ./server -> /tmp/server"
cp -r server /tmp/server

# manipulating the copied folder
cd /tmp/server

echo "copying 'app.adserver.yaml' -> 'app.yaml'"
cp app.adserver.yaml app.yaml

echo "uploading to GAE"
python2.5 manage.py update

echo "copying 'app.frontend.yaml' -> 'app.yaml'"
cp app.frontend.yaml app.yaml

popd
echo "deleting temporary files"
rm -rf /tmp/server
