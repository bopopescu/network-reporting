#!/bin/bash
#
# This script transfers our datastore from mopub-inc to mopub-experimental

pushd ~/tmp

echo $1
# if [ -z "$1" ] # if $1 does not exist
# then
#     rm -rf datastore0
#     rm -rf datastore1
#     rm -rf datastore2
#     rm -rf datastore3
#     rm -rf datastore4
#     rm -rf datastore5
#     rm -rf datastore6
# fi


# 
# appcfg.py upload_data --email=olp@mopub.com --filename=datastore0 --application=mopub-experimental --url=http://mopub-experimental.appspot.com/remote_api --passin


DESTINATION_URL="http://mopub-experimental.appspot.com/remote_api"
DESTINATION_APP="mopub-experimental"
DESTINATION_PASS="N47935N47935"
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore0 --email=olp@mopub.com --passin --kind=User
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore0 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore1 --email=olp@mopub.com --passin --kind=Account
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore1 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore2 --email=olp@mopub.com --passin --kind=App
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore2 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore3 --email=olp@mopub.com --passin --kind=Site
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore3 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore4 --email=olp@mopub.com --passin --kind=Campaign
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore4 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore5 --email=olp@mopub.com --passin --kind=AdGroup
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore5 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore6 --email=olp@mopub.com --passin --kind=Creative
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore6 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin
 
 echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore7 --email=olp@mopub.com --passin --kind=NetworkConfig
 echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore7 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin    
      
echo N47935N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore7 --email=olp@mopub.com --passin --kind=MarketPlaceConfig
echo $DESTINATION_PASS | appcfg.py upload_data --email=olp@mopub.com --filename=datastore7 --application=$DESTINATION_APP --url=$DESTINATION_URL --passin      


