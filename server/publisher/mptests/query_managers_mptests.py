import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from nose.tools import ok_, eq_

from ad_server.adunit_context.adunit_context import AdUnitContext
from common.constants import MAX_OBJECTS
from common.utils.test.fixtures import (generate_network_config, generate_app,
                                        generate_adunit)
from common.utils.test.test_utils import (confirm_db, dict_eq, list_eq,
                                          model_eq, model_key_eq, ADDED_1,
                                          EDITED_1)
from common.utils.test.views import BaseViewTestCase
from publisher.models import App, AdUnit
from publisher.query_managers import (AdUnitContextQueryManager,
                                      PublisherQueryManager, AppQueryManager,
                                      AdUnitQueryManager)


class AdUnitContextQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitContextQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_context(self):
        """
        Get the adunit context for our adunit and confirm that its
        properties are as expected.
        """

        adunit_key = self.adunit.key()

        expected_adunit = AdUnit.get(adunit_key)
        expected_adunit_context = AdUnitContext.wrap(expected_adunit)

        adunit_context = AdUnitContextQueryManager.get_context(adunit_key)

        model_key_eq(adunit_context, expected_adunit_context)

    @confirm_db()
    def mptest_cache_get_or_insert(self):
        """
        Get the adunit context for our adunit from hypercache or memcache or
        build it from the datastore and confirm that its properties are as
        expected.
        """

        adunit_key = self.adunit.key()

        expected_adunit = AdUnit.get(adunit_key)
        expected_adunit_context = AdUnitContext.wrap(expected_adunit)

        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)

        model_key_eq(adunit_context, expected_adunit_context)

        # TODO: Check more of the functionality of this method.
        # Especially if the context is in hypercache.

    @confirm_db()
    def mptest_cache_delete_from_adunits(self):
        """
        Remove adunit context from cache.
        """

        AdUnitContextQueryManager.cache_delete_from_adunits([self.adunit])

        # TODO: Somehow check that memcache is now devoid of adunit_contexts.


class PublisherQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(PublisherQueryManagerTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get_objects_dict_for_account(self):
        """
        Get all apps and adunits for the account and confirm that their
        properties are as expected.
        """

        objects_dict = PublisherQueryManager.get_objects_dict_for_account(self.account)

        eq_(len(objects_dict), 1)
        expected_app = objects_dict.values()[0]

        model_eq(self.app, expected_app)

        eq_(len(expected_app.adunits), 1)
        expected_adunit = expected_app.adunits[0]

        model_eq(self.adunit, expected_adunit)

    @confirm_db()
    def mptest_get_apps_dict_for_account(self):
        """
        Get all apps for the account and confirm that their properties are as
        expected.
        """

        apps_dict = PublisherQueryManager.get_apps_dict_for_account(self.account)

        expected_apps_dict = {
            str(self.app.key()): self.app
        }

        dict_eq(apps_dict, expected_apps_dict)

    @confirm_db()
    def mptest_get_adunits_dict_for_account(self):
        """
        Get all adunits for the account and confirm that their properties are as
        expected.
        """

        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(self.account)

        expected_adunits_dict = {
            str(self.adunit.key()): self.adunit
        }

        dict_eq(adunits_dict, expected_adunits_dict)

       # TODO: Check that deleted apps/adunits are not returned


class AppQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
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

    @confirm_db(app=ADDED_1)
    def mptest_put_new_apps(self):
        expected_new_app = generate_app(self.account, put=False)

        # TODO: put_apps will be changed to a class method.
        AppQueryManager().put_apps([expected_new_app])

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 2)

        # Obtain the created app/adunit.
        new_apps = filter(lambda app: app.key() != self.app.key(), apps)
        eq_(len(new_apps), 1)
        new_app = new_apps[0]

        model_eq(new_app, expected_new_app)

        old_app = App.get(self.app.key())
        model_eq(old_app, self.app)

    @confirm_db(app=EDITED_1)
    def mptest_put_existing_apps(self):
        self.app.name = 'Edited App'

        # TODO: put_apps will be changed to a class method.
        AppQueryManager().put_apps([self.app])

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 1)

        edited_app = apps[0]

        model_eq(edited_app, self.app)

    @confirm_db(app=ADDED_1)
    def mptest_put_new_app(self):
        expected_new_app = generate_app(self.account, put=False)

        AppQueryManager.put(expected_new_app)

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 2)

        # Obtain the created app/adunit.
        new_apps = filter(lambda app: app.key() != self.app.key(), apps)
        eq_(len(new_apps), 1)
        new_app = new_apps[0]

        model_eq(new_app, expected_new_app)

        old_app = App.get(self.app.key())
        model_eq(old_app, self.app)

    @confirm_db(app=EDITED_1)
    def mptest_put_existing_app(self):
        self.app.name = 'Edited App'

        AppQueryManager.put(self.app)

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 1)

        edited_app = apps[0]

        model_eq(edited_app, self.app)

    @confirm_db(app=EDITED_1, network_config=ADDED_1)
    def mptest_update_config_and_put(self):
        network_config = generate_network_config(account=None, put=False)

        AppQueryManager.update_config_and_put(self.app, network_config)

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 1)
        app = apps[0]
        model_eq(app, self.app, exclude=['network_config'])

        network_config = app.network_config
        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(network_config, expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def update_config_and_put_multi(self):
        network_config = generate_network_config(account=None, put=False)

        AppQueryManager.update_config_and_put_multi([self.app], [network_config])

        apps = App.all().fetch(MAX_OBJECTS)
        eq_(len(apps), 1)
        app = apps[0]
        model_eq(app, self.app, exclude=['network_config'])

        network_config = app.network_config
        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(network_config, expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def get_apps_with_network_configs(self):
        apps = AppQueryManager.get_apps_with_network_configs(self.account)
        eq_(len(apps), 0)

        network_config = generate_network_config(account=None, put=False)

        AppQueryManager.update_config_and_put_multi([self.app], [network_config])

        apps = AppQueryManager.get_apps_with_network_configs(self.account)
        eq_(len(apps), 1)
        app = apps[0]
        model_eq(app, self.app, exclude=['network_config'])

        network_config = app.network_config
        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(network_config, expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def get_apps_without_pub_ids(self):
        # At first, the app does not have a pub id.
        apps = AppQueryManager(self.account, networks=['mobfox'])
        eq_(len(apps), 1)
        app = apps[0]
        model_eq(app, self.app)

        network_config = generate_network_config(account=None, put=False)
        AppQueryManager.update_config_and_put(self.app, network_config)

        # We put a network config with no pub ids, and still expect the app to
        # not have a pub id.
        apps = AppQueryManager(self.account, networks=['mobfox'])
        eq_(len(apps), 1)
        app = apps[0]
        model_eq(app, self.app)

        self.app.network_config.mobfox_pub_id = 'MOBFOX ID'
        AppQueryManager.update_config_and_put(self.app, self.app.network_config)

        # Now that our app has an associated pub id, we no longer expect to get
        # any apps back from this function.
        apps = AppQueryManager(self.account, networks=['mobfox'])
        eq_(len(apps), 0)

    @confirm_db()
    def get_iad_pub_id(self):
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        ok_(pub_id is None)

        self.app.url = 'http://www.mopub.com'
        self.app.put()
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        ok_(pub_id is None)

        self.app.url = 'http://itunes.apple.com/id/12345?'
        self.app.put()
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        eq_(pub_id, '12345')

    @confirm_db()
    def get_iad_pub_ids(self):
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        list_eq(pub_id, [])

        self.app.url = 'http://www.mopub.com'
        self.app.put()
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        list_eq(pub_id, [])

        self.app.url = 'http://itunes.apple.com/id/12345?'
        self.app.put()
        pub_id = AppQueryManager.get_iad_pub_id(self.account, self.app.name)
        list_eq(pub_id, ['12345'])


class AdUnitQueryManagerTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
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

    @confirm_db(adunit=ADDED_1)
    def mptest_put_new_adunits(self):
        expected_new_adunit = generate_adunit(self.account, self.app, put=False)

        AdUnitQueryManager.put_adunits([expected_new_adunit])

        adunits = AdUnit.all().fetch(MAX_OBJECTS)
        eq_(len(adunits), 2)

        # Obtain the created adunit/adunit.
        new_adunits = filter(lambda adunit: adunit.key() != self.adunit.key(), adunits)
        eq_(len(new_adunits), 1)
        new_adunit = new_adunits[0]

        model_eq(new_adunit, expected_new_adunit)

        old_adunit = AdUnit.get(self.adunit.key())
        model_eq(old_adunit, self.adunit)

    @confirm_db(adunit=EDITED_1)
    def mptest_put_existing_adunits(self):
        self.adunit.name = 'Edited AdUnit'

        AdUnitQueryManager.put_adunits([self.adunit])

        adunits = AdUnit.all().fetch(MAX_OBJECTS)
        eq_(len(adunits), 1)

        edited_adunit = adunits[0]

        model_eq(edited_adunit, self.adunit)

    @confirm_db(adunit=ADDED_1)
    def mptest_put_new_adunit(self):
        expected_new_adunit = generate_adunit(self.account, self.app, put=False)

        AdUnitQueryManager.put(expected_new_adunit)

        adunits = AdUnit.all().fetch(MAX_OBJECTS)
        eq_(len(adunits), 2)

        # Obtain the created adunit/adunit.
        new_adunits = filter(lambda adunit: adunit.key() != self.adunit.key(), adunits)
        eq_(len(new_adunits), 1)
        new_adunit = new_adunits[0]

        model_eq(new_adunit, expected_new_adunit)

        old_adunit = AdUnit.get(self.adunit.key())
        model_eq(old_adunit, self.adunit)

    @confirm_db(adunit=EDITED_1)
    def mptest_put_existing_adunit(self):
        self.adunit.name = 'Edited AdUnit'

        AdUnitQueryManager.put(self.adunit)

        adunits = AdUnit.all().fetch(MAX_OBJECTS)
        eq_(len(adunits), 1)

        edited_adunit = adunits[0]

        model_eq(edited_adunit, self.adunit)

    @confirm_db()
    def update_config_and_put_multi(self):
        network_config = generate_network_config(account=None, put=False)

        AdUnitQueryManager.update_config_and_put_multi([self.adunit], [network_config])

        adunits = AdUnit.all().fetch(MAX_OBJECTS)
        eq_(len(adunits), 1)
        adunit = adunits[0]
        model_eq(adunit, self.adunit, exclude=['network_config'])

        network_config = adunit.network_config
        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(network_config, expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def get_adunits_with_network_configs(self):
        adunits = AdUnitQueryManager.get_adunits_with_network_configs(self.account)
        eq_(len(adunits), 0)

        network_config = generate_network_config(account=None, put=False)

        AdUnitQueryManager.update_config_and_put_multi([self.adunit], [network_config])

        adunits = AdUnitQueryManager.get_adunits_with_network_configs(self.account)
        eq_(len(adunits), 1)
        adunit = adunits[0]
        model_eq(adunit, self.adunit, exclude=['network_config'])

        network_config = adunit.network_config
        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(network_config, expected_network_config,
                 check_primary_key=False)
