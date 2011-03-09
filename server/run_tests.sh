nosetests --with-gae --gae-datastore='./test_data/basic_test.datastore' --with-coverage ad_server_tests

# GAE data modeling for conversion tracking
nosetests --match='(?:^|[\b_\./-])mptest' --with-gae --gae-application='./' --where='./userstore/tests' --with-coverage

# --with-profile --profile-stats-file='./test_data/profile_statsi.stats'
