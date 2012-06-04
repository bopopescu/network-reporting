import datetime
import logging
import os
import simplejson as json
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from account.models import NetworkConfig
from account.query_managers import NetworkConfigQueryManager
from advertiser.models import Campaign, AdGroup, Creative
from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager)
from ad_server.adunit_context.adunit_context import AdUnitContext
from common.utils.date_magic import gen_days
from common.utils.test.fixtures import (generate_network_config, generate_app,
                                        generate_adunit, generate_campaign,
                                        generate_adgroup,
                                        generate_marketplace_creative,
                                        generate_html_creative)
from common.utils.test.test_utils import (confirm_db, dict_eq, list_eq,
                                          model_key_eq, time_almost_eq,
                                          model_eq)
from common.utils.test.views import BaseViewTestCase
from common.utils.timezones import Pacific_tzinfo
from publisher.forms import AppForm, AdUnitForm
from publisher.models import App, AdUnit
from publisher.query_managers import AdUnitContextQueryManager, PublisherQueryManager, AppQueryManager, AdUnitQueryManager
from reporting.models import StatsModel

# AdUnitContextQueryManager
# # get_context
# # cache_get_or_insert
# # cache_delete_from_adunits

# PublisherQueryManager
# # get_objects_dict_for_account
# # get_apps_dict_for_account
# # get_adunits_dict_for_account

# AppQueryManager
# # get_app_by_key
# # get_apps
# # get_app_keys
# # get_all_apps
# # reports_get_apps
# # put_apps
# # put
# # update_config_and_put
# # update_config_and_put_multi
# # get_apps_with_network_configs
# # get_apps_without_pub_ids
# # get_iad_pub_id
# # get_iad_pub_ids

# AdUnitContextQueryManager
# # get_adunits
# # reports_get_adunits
# # put_adunits
# # get_by_key
# # get_adunit
# # put
# # update_config_and_put
# # update_config_and_put_multi


class AdUnitContextQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius
    """

    def setUp(self):
        super(AdUnitContextQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_context(self):
        adunit_key = self.adunit.key()

        expected_adunit = AdUnit.get(adunit_key)
        expected_adunit_context = AdUnitContext.wrap(expected_adunit)

        adunit_context = AdUnitContextQueryManager.get_context(adunit_key)

        model_key_eq(adunit_context, expected_adunit_context)

    @confirm_db()
    def mptest_cache_get_or_insert(self):
        adunit_key = self.adunit.key()

        expected_adunit = AdUnit.get(adunit_key)
        expected_adunit_context = AdUnitContext.wrap(expected_adunit)

        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)

        model_key_eq(adunit_context, expected_adunit_context)

        # TODO: Check more of the functionality of this method.
        # Especially if the context is in hypercache.

    @confirm_db()
    def mptest_cache_delete_from_adunits(self):
        AdUnitContextQueryManager.cache_delete_from_adunits([self.adunit])

        # TODO: Somehow check that memcache is now devoid of adunit_contexts.


class PublisherQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius
    """

    def setUp(self):
        super(PublisherQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_objects_dict_for_account(self):
        objects_dict = PublisherQueryManager.get_objects_dict_for_account(self.account)

        eq_(len(objects_dict), 1)
        expected_app = objects_dict.values()[0]

        model_eq(self.app, expected_app)

        eq_(len(expected_app.adunits), 1)
        expected_adunit = expected_app.adunits[0]

        model_eq(self.adunit, expected_adunit)

    @confirm_db()
    def mptest_get_apps_dict_for_account(self):
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(self.account)

        expected_apps_dict = {
            str(self.app.key()): self.app
        }

        dict_eq(apps_dict, expected_apps_dict)

    @confirm_db()
    def mptest_get_adunits_dict_for_account(self):
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(self.account)

        expected_adunits_dict = {
            str(self.adunit.key()): self.adunit
        }

        dict_eq(adunits_dict, expected_adunits_dict)

       # TODO: Check that deleted apps/adunits are not returned


class AppQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius
    """

    def setUp(self):
        super(AppQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_app_by_key(self):
        app = AppQueryManager.get_app_by_key(self.app.key())

        model_eq(self.app, app)

    @confirm_db()
    def mptest_get_apps(self):
        apps = AppQueryManager.get_apps(self.account)

        expected_apps = [self.app]

        list_eq(apps, expected_apps)

    @confirm_db()
    def mptest_get_app_keys(self):
        app_keys = AppQueryManager.get_app_keys(self.account)

        expected_app_keys = [self.app.key()]

        list_eq(app_keys, expected_app_keys)

    @confirm_db()
    def mptest_reports_get_apps(self):
        # TODO: Obviously there are a lot of combinations here. Flesh this out in the future.

        apps = AppQueryManager.reports_get_apps(account=self.account)

        # Wait so some times this returns a query, and other times a list? Ugh.

        expected_apps = [self.app]

        # TODO: Casting the query to a list for now. Fix QM and change this.
        list_eq(list(apps), expected_apps)

    @confirm_db()
    def mptest_put_apps(self):
        new_app = generate_app(self.account, put=False)

        # Check db state before put

        # Do put

        # Check db state after put

    @confirm_db()
    def mptest_put(self):
        pass

    @confirm_db()
    def mptest_update_config_and_put(self):
        pass

    @confirm_db()
    def update_config_and_put_multi(self):
        pass

    @confirm_db()
    def get_apps_with_network_configs(self):
        pass

    @confirm_db()
    def get_apps_without_pub_ids(self):
        pass

    @confirm_db()
    def get_iad_pub_id(self):
        pass

    @confirm_db()
    def get_iad_pub_ids(self):
        pass


class AdUnitQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius
    """

    def setUp(self):
        super(AdUnitQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_adunits(self):
        # Filters are keys (if provided, returns), otherwise app and account
        # TODO: test combinations? test cases where it returns none?
        adunit_keys = [self.adunit.key()]

        expected_adunits = [self.adunit]

        adunits = AdUnitQueryManager.get_adunits(keys=adunit_keys)
        list_eq(adunits, expected_adunits)

        adunits = AdUnitQueryManager.get_adunits(app=self.app)
        list_eq(adunits, expected_adunits)

        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        list_eq(adunits, expected_adunits)

    @confirm_db()
    def mptest_reports_get_adunits(self):
        # Again this can either return a Query or a list.
        # TODO: Check more of the filtering options from the method signature.

        adunits = AdUnitQueryManager.reports_get_adunits(account=self.account)

        # Wait so some times this returns a query, and other times a list? Ugh.

        expected_adunits = [self.adunit]

        # TODO: Casting the query to a list for now. Fix QM and change this.
        list_eq(list(adunits), expected_adunits)

    @confirm_db()
    def mptest_put_adunits(self):
        pass

    # TODO: These error out with the following:
    # unbound method get_adunit() must be called with AdUnitQueryManager instance as first argument (got Key instance instead)

    # def mptest_get_by_key(self):
    #     adunit = AdUnitQueryManager.get_by_key(self, self.adunit.key())

    #     model_eq(adunit, self.adunit)

    # def mptest_get_adunit(self):
    #     # Is this essentially an alias of the above function?
    #     adunit = AdUnitQueryManager.get_adunit(self, self.adunit.key())

    #     model_eq(adunit, self.adunit)

    @confirm_db()
    def mptest_put(self):
        pass

    @confirm_db()
    def mptest_update_config_and_put(self):
        pass

    @confirm_db()
    def update_config_and_put_multi(self):
        pass
