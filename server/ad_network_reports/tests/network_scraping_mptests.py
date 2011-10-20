import os, sys
sys.path.append(os.environ['PWD'])

# magic test import
import common.utils.test.setup
import logging

from google.appengine.ext import db

from datetime import date, timedelta
from sets import Set

from ad_network_reports.query_managers import AdNetworkReportQueryManager
from ad_network_reports.update_ad_networks import update_ad_networks
from account.models import Account, NetworkConfig
from publisher.models import App

from ad_network_reports.models import *

import ad_network_reports.query_managers

TEST_JUMPTAP_PUB_ID = '12345'
TEST_ADMOB_PUB_ID = 'a14a9ed9bf1fdcd'
TEST_IAD_PUB_ID = '362641118' # NOT IN NetworkConfig
TEST_INMOBI_PUB_ID ='4028cb962b75ff06012b792fc5fb0045'
TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

def ad_network_reports_mptest():

    from ad_network_reports.tests.load_test_data import *

    # Call the method we are testing.
    update_ad_networks()

    # Verify results.
    manager = AdNetworkReportQueryManager(account) # account

    logging.warning([(app, publisher_id) for app, publisher_id in
        manager.get_apps_with_publisher_ids('jumptap')])

    test_network_app_mappers = list(manager.get_ad_network_mappers())
    assert len(test_network_app_mappers) > 0
    #assert len(test_network_app_mappers) == len(entities)

    logging.warning([a.key().name for a in test_network_app_mappers])

    # Was a day created for each app for the account?
    yesterday = date.today() - timedelta(days = 1)
    for n in test_network_app_mappers:
        n = manager.get_ad_network_app_mapper(ad_network_app_mapper_key =
                n.key())
        stats = manager.get_ad_network_app_stats(n)
        logging.warning( "network name:%s application name: %s" %
                (n.ad_network_name, n.application.name))
        logging.warning("network name:%s application name: %s" %
                (n.ad_network_name, n.application.name))
        assert stats[0].date == yesterday

    # Do aggregate statistics work?
    aggregates = [manager.get_ad_network_aggregates(n, date.today() -
        timedelta(days = 8), date.today() - timedelta(days = 1)) for n in
        test_network_app_mappers]
