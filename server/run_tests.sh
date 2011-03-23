#!/bin/sh

echo $1
if [ -z "$1" ] # if $1 does not exist
then
    # nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' --with-coverage ad_server_tests
    # nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests' --with-coverage
    # nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./reporting/tests' --with-coverage  --without-sandbox 
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-datastore='./test_data/basic_test.datastore' budget_integration_mptests #--with-coverage 

else
    nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' --gae-lib-root="$1" --with-coverage --with-xunit --verbose ad_server_tests
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --gae-lib-root="$1" --where='./userstore/tests' --with-coverage
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --gae-lib-root="$1" --where='./reporting/tests' --with-coverage --without-sandbox
fi


