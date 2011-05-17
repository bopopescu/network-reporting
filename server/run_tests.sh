#!/bin/sh

echo $1
if [ -z "$1" ] # if $1 does not exist
then
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests' #--with-coverage
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./reporting/tests' --without-sandbox # --with-coverage 
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./ad_server/filters/tests' --without-sandbox # --with-coverage  
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./budget/tests' --without-sandbox
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./ad_server/optimizer/tests' --without-sandbox
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./common/utils' --without-sandbox
    # nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./reports/tests' --without-sandbox # --with-coverage  
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./account/tests' --without-sandbox
    
    # System Tests (Must live in server root dir for some reason TODO: Fix this)
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' system_mptests
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' network_config_mptests
    nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' ad_server_tests # --with-coverage
else
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests' #--with-coverage
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./reporting/tests' --without-sandbox # --with-coverage 
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./ad_server/filters/tests' --without-sandbox # --with-coverage  
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./budget/tests' --without-sandbox
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./ad_server/optimizer/tests' --without-sandbox
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./common/utils' --without-sandbox
    # nosetest--with-coverage --with-xunits --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./reports/tests' --without-sandbox # --with-coverage  
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./account/tests' --without-sandbox

    # System T--with-coverage --with-xunit--gae-lib-root="$1" ests (Must live in server root dir for some reason TODO: Fix this)
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' system_mptests
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' network_config_mptests
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --with-gae --gae-datastore='./test_data/basic_test.datastore' ad_server_tests # --with-coverage
fi