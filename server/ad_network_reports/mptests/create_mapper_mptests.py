import os
import sys
sys.path.append(os.environ['PWD'])

from datetime import date

import common.utils.test.setup

from nose.tools import ok_, \
       eq_

from django.core.urlresolvers import reverse
from common.utils.test.test_utils import confirm_all_models, \
        model_eq

from networks.mptests.network_test_case import NetworkTestCase, \
        DEFAULT_PUB_ID

from ad_network_reports.models import AdNetworkScrapeStats, AdNetworkAppMapper
from ad_network_reports.query_managers import AdNetworkMapperManager

class ContentFilterViewTestCase(NetworkTestCase):
    """
    Author: Tiago (9/12/2012)
    """

    def setUp(self):
        super(ContentFilterViewTestCase, self).setUp()

        self.url = reverse('create_mapper')

        self.network_type = 'admob'
        self.set_up_existing_apps_and_adunits()
        self.existing_apps = self.get_apps_with_adunits(self.account)

        self.existing_campaign = self.generate_network_campaign(self.network_type,
            self.account, self.existing_apps)
        self.login = self.generate_ad_network_login(self.network_type, self.account)

        self.test_pub_id = 'NEW_PUB_ID_1'

        self.post_data = {'network_type': self.network_type,
                          'app_key': str(self.existing_apps[0].key()),
                          'pub_id': self.test_pub_id}

    def mptest_create_mapper(self):
        """
        Create ad network app mapper for the new pub id

        Author: Tiago (9/12/2012)
        """
        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added={AdNetworkAppMapper: 1})

        # Fetch all mappers for our app and this network type.
        mappers = AdNetworkAppMapper.all(). \
            filter('application in', self.existing_apps). \
            filter('ad_network_name =', self.network_type).fetch(1000)

        # There should only be one mapper: the one for the app we just updated.
        eq_(len(mappers), 1)

        mapper = mappers[0]
        eq_(mapper.publisher_id, self.test_pub_id)
        eq_(mapper.ad_network_name, self.network_type)
        eq_(mapper.ad_network_login.key(), self.login.key())

    def mptest_delete_old_mapper(self):
        """
        Delete the old mapper since it has no stats and create a new one for the new pub id

        Author: Tiago (9/12/2012)
        """
        mapper = AdNetworkMapperManager.create(self.network_type, DEFAULT_PUB_ID,
                self.login, self.existing_apps[0])

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added={AdNetworkAppMapper: 1},
                           deleted=[mapper.key()])

        # Fetch all mappers for our app and this network type.
        # TODO: refactor ad_network_reports.query_managers
        mappers = AdNetworkAppMapper.all(). \
            filter('application in', self.existing_apps). \
            filter('ad_network_name =', self.network_type).fetch(1000)

        # There should only be one mapper: the one for the app we just updated.
        eq_(len(mappers), 1)

        mapper = mappers[0]
        eq_(mapper.publisher_id, self.test_pub_id)
        eq_(mapper.ad_network_name, self.network_type)
        eq_(mapper.ad_network_login.key(), self.login.key())

    def mptest_save_mappers_with_stats(self):
        """
        Create a new mapper and preserve old mappers with stats while deleting
        old ones without stats.

        Author: Tiago (9/12/2012)
        """
        pub_id_1 = 'PUB_ID_1'
        pub_id_2 = 'PUB_ID_2'
        mapper_1 = AdNetworkMapperManager.create(self.network_type, pub_id_1,
                self.login, self.existing_apps[0])
        AdNetworkScrapeStats(ad_network_app_mapper=mapper_1, date=date.today()).put()
        
        mapper_2 = AdNetworkMapperManager.create(self.network_type, pub_id_2,
                self.login, self.existing_apps[0])

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           added={AdNetworkAppMapper: 1},
                           deleted=[mapper_2.key()])

        # Fetch all mappers for our app and this network type.
        mappers = AdNetworkAppMapper.all(). \
            filter('application in', self.existing_apps). \
            filter('ad_network_name =', self.network_type).fetch(1000)

        # There should be two mappers: one we just created and the one with
        # stats
        eq_(len(mappers), 2)

        ok_(all([mapper.ad_network_name == self.network_type for mapper in mappers]))
        ok_(all([mapper.ad_network_login.key() == self.login.key() for mapper in mappers]))

        mapper_keys = [mapper.key() for mapper in mappers]
        ok_(mapper_1.key() in mapper_keys)
        ok_(mapper_2.key() not in mapper_keys)
        
        mapper_pub_ids = [mapper.publisher_id for mapper in mappers]
        ok_(mapper_1.publisher_id in mapper_pub_ids)
        ok_(self.test_pub_id in mapper_pub_ids)

    def mptest_dont_create_mapper_without_login(self):
        """
        Don't do anything if no login exists.

        Author: Tiago (9/12/2012)
        """
        self.login.delete()

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

