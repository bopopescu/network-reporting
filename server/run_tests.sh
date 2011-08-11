#!/bin/sh
echo $1

export DJANGO_SETTINGS_MODULE='settings'

if [ -z "$1" ] # if $1 does not exist
then                                                                            
    echo "Running userstore tests..."
    nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests'
    # nosetests ./userstore/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./'
    
    echo "Running reporting tests..."
    nosetests ./reporting/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running budget tests..." 
    nosetests ./budget/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running account tests..."
    nosetests ./account/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running common/utils tests..."
    nosetests ./common/utils/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    
    # Adserver Tests 
    echo "\n--------- ADSERVER TESTS --------"            
    echo "Running optimizer tests..."
    nosetests ./ad_server/optimizer/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running adunit_context tests..." 
    nosetests ./ad_server/adunit_context/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running ad_server/filter tests..."  
    nosetests ./ad_server/filters/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running auction tests..."    
    nosetests ./ad_server/auction/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    echo "Running ad_handler tests..."   
    nosetests ./ad_server/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox        
    echo "Running parser tests..."  
    nosetests ./ad_server/parser/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
  
  
    # System Tests (Must live in server root dir for some reason TODO: Fix this) 
    echo "\n--------- SYSTEM TESTS --------"            
    echo "Running system end-to-end tests..."
    nosetests system_mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox         
    echo "Running network_config tests..."
    nosetests network_config_mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    
else
    nosetests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests'
    # nosetests ./userstore/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./'
    
    
    nosetests ./reporting/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox 
    nosetests ./budget/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./account/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./common/utils/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

    # Adserver Tests
    nosetests ./ad_server/optimizer/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/filters/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox 
    nosetests ./ad_server/auction/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/parser/tests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
  
    # System T--with-coverage --with-xunit --gae-lib-root="$1" ests (Must live in server root dir for some reason TODO: Fix this)
    nosetests system_mptests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests network_config_mptests --with-coverage --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
fi
