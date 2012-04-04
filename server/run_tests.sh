#!/bin/sh
echo $1

export DJANGO_SETTINGS_MODULE='settings'

if [ -z "$1" ] # if $1 does not exist
then

    # TODO: Why does this have to use --where?
   echo "Userstore tests"
   nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests'

   echo "Reporting tests"
   nosetests ./reporting/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Reports tests"
   nosetests ./reports/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Reports AWS tests"
   nosetests ./reports/aws_reports/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Budget tests"
   nosetests ./budget/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Account tests"
   nosetests ./account/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

#   echo "Network Scraping Tests"
#   nosetests ./ad_network_reports/scrapers/mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
#   echo "Network Models and Update Tests"
#   nosetests ./ad_network_reports/mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

   # Adserver Tests
   echo "Ad Server Optimizer tests"
   nosetests ./ad_server/optimizer/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Adunit Context tests"
   nosetests ./ad_server/adunit_context/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Ad Server Filter tests"
   nosetests ./ad_server/filters/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Auction tests"
   nosetests ./ad_server/auction/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "AdHandler tests"
   nosetests ./ad_server/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Ad Server Parser tests"
   nosetests ./ad_server/parser/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Network Rendering tests"
   nosetests ./ad_server/renderers/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Network Server Side tests"
   nosetests ./ad_server/networks/tests/ --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "SimpleModels Tests"
   nosetests ./simple_models_mptests.py --match='(?:^|[\b_\./-])mptest' --without-sandbox

   # System Tests (Must live in server root dir for some reason TODO: Fix this)
   echo "System tests"
   nosetests system_mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
   echo "Network Config tests"
   nosetests network_config_mptests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

   # to get coverage, use:
   #nosetests ./ad_server/auction/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox  --cover-package ad_server.auction

   # mopub logging tests
   echo "mopub logging tests"
   nosetests ./stats/tests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

else
    nosetests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests'
    # nosetests ./userstore/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./'


    nosetests ./reporting/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./budget/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./account/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

    # Adserver Tests
    nosetests ./ad_server/optimizer/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/filters/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/auction/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/parser/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/renderers/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests ./ad_server/neworks/tests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1"--match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

    # System T --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" ests (Must live in server root dir for some reason TODO: Fix this)
    nosetests system_mptests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
    nosetests network_config_mptests  --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox

    echo "mopub logging tests"
    nosetests ./stats/tests --with-xcoverage --cover-package=ad_server --with-xunit --gae-lib-root="$1" --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --without-sandbox
fi
