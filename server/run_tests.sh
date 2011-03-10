#!/bin/sh

echo $1
if [ -z "$1" ] # if $1 does not exist
then
    nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' --with-coverage ad_server_tests
else
    nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' --gae-lib-root="$1" --with-coverage --with-xunit --verbose --ad_server_tests
fi

# GAE data modeling for conversion tracking
#nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests' --with-coverage

# --with-profile --profile-stats-file='./test_data/profile_statsi.stats'