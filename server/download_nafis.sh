#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

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
# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore0 --email=olp@mopub.com --passin --kind=User
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore0 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore1 --email=olp@mopub.com --passin --kind=Account
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore1 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore2 --email=olp@mopub.com --passin --kind=App
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore2 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore3 --email=olp@mopub.com --passin --kind=Site
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore3 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore4 --email=olp@mopub.com --passin --kind=Campaign
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore4 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore5 --email=olp@mopub.com --passin --kind=AdGroup
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore5 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

# echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://mopub-inc.appspot.com/remote_api --filename=datastore6 --email=olp@mopub.com --passin --kind=Creative
echo bar | appcfg.py upload_data --email=foobar@nowhere.com --filename=datastore6 --application=mopub-inc --url=http://localhost:8000/remote_api --passin

