#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

rm -rf /Users/nafis/tmp/datastore0
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore0 --kind=User --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore0 --application=mopub-inc --url=http://localhost:8000/remote_api

rm -rf /Users/nafis/tmp/datastore1
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore1 --kind=Account --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore1 --application=mopub-inc --url=http://localhost:8000/remote_api

rm /Users/nafis/tmp/datastore2
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore2 --kind=App --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore2 --application=mopub-inc --url=http://localhost:8000/remote_api

rm /Users/nafis/tmp/datastore3
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore3 --kind=Site --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore3 --application=mopub-inc --url=http://localhost:8000/remote_api

rm /Users/nafis/tmp/datastore4
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore4 --kind=Campaign --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore4 --application=mopub-inc --url=http://localhost:8000/remote_api

rm /Users/nafis/tmp/datastore5
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore5 --kind=AdGroup --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore5 --application=mopub-inc --url=http://localhost:8000/remote_api

rm /Users/nafis/tmp/datastore6
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=/Users/nafis/tmp/datastore6 --kind=Creative --email=olp@mopub.com --passin
echo asdf | appcfg.py upload_data --email=foobar@nowhere.com --filename=/Users/nafis/tmp/datastore6 --application=mopub-inc --url=http://localhost:8000/remote_api
