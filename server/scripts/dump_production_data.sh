#!/bin/bash
#
# This script transfers our datastore from mopub-inc to mopub-experimental

# pushd ~/tmp

# echo $1
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

# appcfg.py upload_data --email=olp@mopub.com --filename=datastore0 --application=mopub-experimental --url=http://mopub-experimental.appspot.com/remote_api --passin

NUM_THREADS=20
BATCH_SIZE=20
BANDWIDTH_LIMIT=500000
RPS_LIMIT=40

SOURCE_PASSWORD="N47935N47935"
SOURCE_EMAIL="olp@mopub.com"
SOURCE_URL="http://mopub-inc.appspot.com/remote_api"
SOURCE_APP="mopub-inc"

DESTINATION_PASSWORD="N47935N47935"
DESTINATION_EMAIL="olp@mopub.com"
DESTINATION_URL="http://mopub-experimental.appspot.com/remote_api"
DESTINATION_APP="mopub-experimental"

# # User
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=User --filename=datastore_user
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_user

# # Account
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=Account --filename=datastore_account
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_account

# # App
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=App --filename=datastore_app
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_app

# # Site
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=Site --filename=datastore_site
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_site

# # Campaign
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=Campaign --filename=datastore_campaign
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_campaign

# # AdGroup
# echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdGroup --filename=datastore_adgroup
# #echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_adgroup

# Creative
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=Creative --filename=datastore_creative
#echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_creative

# NetworkConfig
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=NetworkConfig --filename=datastore_networkconfig
#echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_networkconfig

# # AdNetworkAppMapper
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkAppMapper --filename=datastore_adnetworkappmapper
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=datastore_adnetworkappmapper

# # AdNetworkAppStats
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkAppStats --filename=AdNetworkAppStats
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=AdNetworkAppStats

# # AdNetworkLoginCredentials
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkLoginCredentials --filename=AdNetworkLoginCredentials
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=AdNetworkLoginCredentials

# # AdNetworkManagementStats
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkManagementStats --filename=AdNetworkManagementStats
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=AdNetworkManagementStats

# # AdNetworkNetworkStats
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkNetworkStats --filename=AdNetworkNetworkStats
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=AdNetworkNetworkStats

# # AdNetworkScrapeStats
echo $SOURCE_PASSWORD | appcfg.py download_data --email=$SOURCE_EMAIL --passin --application=$SOURCE_APP --url=$SOURCE_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --kind=AdNetworkScrapeStats --filename=AdNetworkScrapeStats
# echo $DESTINATION_PASSWORD | appcfg.py upload_data --email=$DESTINATION_EMAIL --passin --application=$DESTINATION_APP --url=$DESTINATION_URL --num_threads=$NUM_THREADS --batch_size=$BATCH_SIZE --bandwidth_limit=$BANDWIDTH_LIMIT --rps_limit=$RPS_LIMIT --filename=AdNetworkScrapeStats
