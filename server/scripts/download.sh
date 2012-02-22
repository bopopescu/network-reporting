#!/bin/bash
#
# This script works. Just type in your GAE username/password when prompted in the first download command. 
# Then type in a blank password to upload to your local machine.
# -Jim, 2/24/2011

pushd /tmp

echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=User --filename=/tmp/datastore00 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Account --filename=/tmp/datastore01 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdGroup --filename=/tmp/datastore02 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=App --filename=/tmp/datastore03 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Budget --filename=/tmp/datastore04 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Campaign --filename=/tmp/datastore05 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Creative --filename=/tmp/datastore06 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=MarketPlaceConfig --filename=/tmp/datastore07 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=NetworkConfig --filename=/tmp/datastore08 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=PaymentInfo --filename=/tmp/datastore09 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=PaymentRecord --filename=/tmp/datastore10 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=RegistrationProfile --filename=/tmp/datastore11 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Report --filename=/tmp/datastore12 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=ScheduledReport --filename=/tmp/datastore13 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=Site --filename=/tmp/datastore14 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkAppMapper --filename=/tmp/datastore15 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkAppStats --filename=/tmp/datastore16 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkLoginCredentials --filename=/tmp/datastore17 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkManagementStats --filename=/tmp/datastore18 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkNetworkStats --filename=/tmp/datastore19 --email=olp@mopub.com --passin
echo N47935 | appcfg.py download_data --application=mopub-inc --url=http://38-aws.mopub-inc.appspot.com/remote_api --kind=AdNetworkScrapeStats --filename=/tmp/datastore20 --email=olp@mopub.com --passin