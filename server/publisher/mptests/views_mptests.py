import datetime
import logging
import os
import simplejson as json
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager
from common.utils.date_magic import gen_days
from common.utils.test.fixtures import (generate_app, generate_adunit,
                                        generate_campaign, generate_adgroup,
                                        default_app_dict, default_adunit_dict)
from common.utils.test.test_utils import (dict_eq, list_eq, model_key_eq,
                                          model_to_dict, time_almost_eq)
from common.utils.test.views import BaseViewTestCase
from common.utils.timezones import Pacific_tzinfo
from publisher.forms import AppForm, AdUnitForm
from publisher.query_managers import PublisherQueryManager
from reporting.models import StatsModel


class DashboardViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(DashboardViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

    def mptest_get(self):
        """
        Confirm that dashboard returns an appropriate response by checking the
        status_code and context.
        """
        url = reverse('dashboard')

        get_response = self.client.get(url)
        eq_(get_response.status_code, 200)

        eq_(get_response.context['page_width'], 'wide')

        # Names is a dict mapping internal representation to readable names. It
        # includes source types and all model keys for an account.
        names = {
            'direct': 'Direct Sold',
            'mpx': 'Marketplace',
            'network': 'Ad Networks',
            str(self.app.key()): self.app.name,
            str(self.adunit.key()): self.adunit.name,
        }
        dict_eq(get_response.context['names'], names)


class AppIndexViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppIndexViewTestCase, self).setUp()

        self.url = reverse('app_index')

    def mptest_get_without_app(self):
        """
        Confirm that app_index returns a redirect to the create app page when
        the account has no apps.
        """
        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 302)

        redirect_url = self.test_client_reverse('publisher_create_app')
        eq_(get_response['Location'], redirect_url)

    def mptest_get_with_app(self):
        """
        Confirm that app_index returns an appropriate response when the account
        has an app by checking the status_code and context.
        """
        app = generate_app(self.account)

        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 200)

        list_eq(get_response.context['apps'], [app])
        eq_(get_response.context['app_keys'], json.dumps([str(app.key())]))

        # TODO: check account_stats and stats


class AppDetailViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppDetailViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        # Create a campaign that doesn't target our adunit to confirm that it
        # doesn't show up on this page.
        self.untargetted_campaign = generate_campaign(self.account)
        generate_adgroup(self.account, self.untargetted_campaign)

        # Create campaigns of each type and an adgroup for each campaign. Each
        # adgroup targets our adunit by setting its site_keys property.
        site_keys = [self.adunit.key()]

        self.gtee_high_campaign = generate_campaign(
                self.account, campaign_type='gtee_high')
        generate_adgroup(
                self.account, self.gtee_high_campaign, site_keys=site_keys)

        self.gtee_campaign = generate_campaign(
                self.account)
        generate_adgroup(
                self.account, self.gtee_campaign, site_keys=site_keys)

        self.gtee_low_campaign = generate_campaign(
                self.account, campaign_type='gtee_low')
        generate_adgroup(
                self.account, self.gtee_low_campaign, site_keys=site_keys)

        self.promo_campaign = generate_campaign(
                self.account, campaign_type='promo')
        generate_adgroup(
                self.account, self.promo_campaign, site_keys=site_keys)

        self.backfill_promo_campaign = generate_campaign(
                self.account, campaign_type='backfill_promo')
        generate_adgroup(
                self.account, self.backfill_promo_campaign, site_keys=site_keys)

        # Use the query manager methods to create marketplace campaigns and
        # adgroups and put them to the db.
        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
                self.account)
        self.marketplace_campaign.put()
        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

        # TODO: network campaigns

        self.url = reverse('publisher_app_show', args=[str(self.app.key())])

    def mptest_get(self):
        """
        Confirm that app detail returns an appropriate response by checking the
        status_code and context.
        """

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 200)

        # When the view is accessed with no GET paramaters, these are the
        # default start and end dates.
        end_date = datetime.datetime.now(Pacific_tzinfo()).date()
        start_date = end_date - datetime.timedelta(days=13)

        eq_(get_response.context['start_date'], start_date)
        eq_(get_response.context['end_date'], end_date)
        eq_(get_response.context['date_range'], 14)

        model_key_eq(get_response.context['app'], self.app)

        # This app has no stats, so compare app.all_stats to a list of empty
        # StatsModels for each date in the date range.
        empty_stats_models = []
        for date in gen_days(start_date, end_date):
            # StatsModel constructor requires a datetime
            datetime_ = datetime.datetime(date.year, date.month, date.day)
            stats_model = StatsModel(publisher=self.app, account=self.account,
                                     date=datetime_)
            empty_stats_models.append(stats_model)

        # This view attaches the all_stats property to the app.
        list_eq(get_response.context['app'].all_stats, empty_stats_models)

        # This view defines these as the last two dates in the date range.
        eq_(get_response.context['today'], empty_stats_models[-1])
        eq_(get_response.context['yesterday'], empty_stats_models[-2])

        # We really shouldn't be passing up HTML fragments here, so here are
        # simple tests until we refactor.
        ok_(isinstance(get_response.context['app_form_fragment'], basestring))
        ok_(isinstance(get_response.context['adunit_form_fragment'],
                       basestring))

        model_key_eq(get_response.context['account'], self.account)

        # There is no helptext if you have created a campaign.
        ok_(get_response.context['helptext'] is None)

        # This view creates this fucking dumb structure for guaranteed campaigns
        # and their level.  This really should not be a list of dicts of lists.
        expected_gtee = [
            {
                'name': 'high',
                'campaigns': [self.gtee_high_campaign],
            },
            {
                'name': 'normal',
                'campaigns': [self.gtee_campaign],
            },
            {
                'name': 'low',
                'campaigns': [self.gtee_low_campaign],
            },
        ]
        list_eq(get_response.context['gtee'], expected_gtee)

        list_eq(get_response.context['promo'], [self.promo_campaign])
        list_eq(get_response.context['marketplace'],
                [self.marketplace_campaign])
        # TODO: list_eq(get_response.context['network'], [self.network_campaign])
        list_eq(get_response.context['backfill_promo'],
                [self.backfill_promo_campaign])

        # Both of these are true because we have an active marketplace campaign
        # targetting an active adunit.
        eq_(get_response.context['marketplace_activated'], True)
        eq_(get_response.context['active_mpx_adunit_exists'], True)

    def mptest_get_authorization(self):
        """
        Confirm that app detail returns a 404 when an unauthorized account
        attempts to access it.
        """

        self.login_secondary_account()

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 404)


# class ExportFileViewTestCase(BaseViewTestCase):
#     """
#     author: Ignatius, Peter
#     """

#     def setUp(self):
#         super(ExportFileViewTestCase, self).setUp()

#         self.app = generate_app(self.account)
#         self.adunit = generate_adunit(self.account, self.app)

#         self.url = reverse('exporter', args=('csv', 'app', str(self.app.key())))

#     def mptest_get(self):
#         """
#         Confirm that export file returns an appropriate response by checking the
#         status_code and context.
#         """

#         get_response = self.client.get(self.url)
#         eq_(get_response.status_code, 200)

#         # TODO: actually test this POS

#     def mptest_get_authorization(self):
#         """
#         """
#         self.login_secondary_account()

#         get_response = self.client.get(self.url)
#         ok_(get_response.status_code, 404)


class AdUnitShowViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitShowViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        # Create a campaign that doesn't target our adunit to confirm that it
        # doesn't show up on this page.
        self.untargetted_campaign = generate_campaign(self.account)
        generate_adgroup(self.account, self.untargetted_campaign)

        # Create campaigns of each type and an adgroup for each campaign. Each
        # adgroup targets our adunit by setting its site_keys property.
        site_keys = [self.adunit.key()]

        self.gtee_high_campaign = generate_campaign(
                self.account, campaign_type='gtee_high')
        self.gtee_high_adgroup = generate_adgroup(
                self.account, self.gtee_high_campaign, site_keys=site_keys)

        self.gtee_campaign = generate_campaign(
                self.account)
        self.gtee_adgroup = generate_adgroup(
                self.account, self.gtee_campaign, site_keys=site_keys)

        self.gtee_low_campaign = generate_campaign(
                self.account, campaign_type='gtee_low')
        self.gtee_low_adgroup = generate_adgroup(
                self.account, self.gtee_low_campaign, site_keys=site_keys)

        self.promo_campaign = generate_campaign(
                self.account, campaign_type='promo')
        self.promo_adgroup = generate_adgroup(
                self.account, self.promo_campaign, site_keys=site_keys)

        self.backfill_promo_campaign = generate_campaign(
                self.account, campaign_type='backfill_promo')
        self.backfill_promo_adgroup = generate_adgroup(
                self.account, self.backfill_promo_campaign, site_keys=site_keys)

        # Use the query manager methods to create marketplace campaigns and
        # adgroups and put them to the db.
        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
                self.account)
        self.marketplace_campaign.put()
        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

        # TODO: network campaigns

        self.url = reverse('publisher_adunit_show',
                           args=[str(self.adunit.key())])

    def mptest_get(self):
        """
        Confirm that adunit detail returns an appropriate response by checking
        the status_code and context.
        """

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 200)

        # I HATE MY LIFE
        model_key_eq(get_response.context['site'], self.adunit)
        model_key_eq(get_response.context['adunit'], self.adunit)

        # When the view is accessed with no GET paramaters, these are the
        # default start and end dates.
        end_date = datetime.datetime.now(Pacific_tzinfo()).date()
        start_date = end_date - datetime.timedelta(days=13)
        days = gen_days(start_date, end_date)

        eq_(get_response.context['start_date'], start_date)
        eq_(get_response.context['end_date'], end_date)
        eq_(get_response.context['date_range'], 14)
        eq_(get_response.context['days'], days)

        # This app has no stats, so compare adunit.all_stats to a list of empty
        # StatsModels for each date in the date range.
        empty_stats_models = []
        for date in days:
            # StatsModel constructor requires a datetime
            datetime_ = datetime.datetime(date.year, date.month, date.day)
            stats_model = StatsModel(publisher=self.adunit,
                                     account=self.account, date=datetime_)
            empty_stats_models.append(stats_model)

        # This view attaches the all_stats property to the app.
        list_eq(get_response.context['adunit'].all_stats, empty_stats_models)

        # This view defines these as the last two dates in the date range.
        eq_(get_response.context['today'], empty_stats_models[-1])
        eq_(get_response.context['yesterday'], empty_stats_models[-2])

        # We really shouldn't be passing up HTML fragments here, so here is a
        # simple test until we refactor.
        ok_(isinstance(get_response.context['adunit_form_fragment'],
                       basestring))

        model_key_eq(get_response.context['account'], self.account)

        # This view creates this fucking dumb structure for guaranteed campaign
        # adgroups and their level.  This really should not be a list of dicts
        # of lists.
        # Note: this view is different than the app view in that the gtee,
        # promo, etc. contain adgroups instead of campaigns.
        expected_gtee = [
            {
                'name': 'high',
                'adgroups': [self.gtee_high_adgroup],
            },
            {
                'name': 'normal',
                'adgroups': [self.gtee_adgroup],
            },
            {
                'name': 'low',
                'adgroups': [self.gtee_low_adgroup],
            },
        ]
        list_eq(get_response.context['gtee'], expected_gtee)

        list_eq(get_response.context['promo'], [self.promo_adgroup])
        list_eq(get_response.context['marketplace'],
                [self.marketplace_adgroup])
        # TODO: list_eq(get_response.context['network'], [self.network_adgroup])
        list_eq(get_response.context['backfill_promo'],
                [self.backfill_promo_adgroup])

        # This is true because we have an active marketplace campaign.
        eq_(get_response.context['marketplace_activated'], True)

    def mptest_get_authorization(self):
        """
        Confirm that adunit detail returns a 404 when an unauthorized account
        attempts to access it.
        """

        self.login_secondary_account()

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 404)


class IntegrationHelpViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(IntegrationHelpViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        self.url = reverse('publisher_integration_help',
                           args=[str(self.adunit.key())])

    def mptest_get(self):
        """
        Confirm that integration help returns an appropriate response by
        checking the status_code and context.
        """

        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 200)

        model_key_eq(get_response.context['site'], self.adunit)

        eq_(get_response.context['status'], None)

        eq_(get_response.context['width'], self.adunit.get_width())
        eq_(get_response.context['height'], self.adunit.get_height())

        model_key_eq(get_response.context['account'], self.account)

    def mptest_get_authorization(self):
        """
        Confirm that integration help returns a 404 when an unauthorized account
        attempts to access it.
        """

        self.login_secondary_account()

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 404)


# class AppExportViewTestCase(BaseViewTestCase):
#     """
#     author: Ignatius, Peter
#     """

#     def setUp(self):
#         super(AppExportViewTestCase, self).setUp()

#         self.url = reverse('publisher_app_export')

#     def mptest_get(self):
#         """
#         Confirm that app_index returns an appropriate response by checking the
#         status_code and context.
#         """

#         post_response = self.client.post(self.url)
#         eq_(post_response.status_code, 200)


# class DashboardExportViewTestCase(BaseViewTestCase):
#     """
#     author: Ignatius, Peter
#     """

#     def setUp(self):
#         super(DashboardExportViewTestCase, self).setUp()

#         self.url = reverse('dashboard_export')

#     def mptest_get(self):
#         """
#         Confirm that app_index returns an appropriate response by checking the
#         status_code and context.
#         """

#         post_response = self.client.post(self.url)
#         eq_(post_response.status_code, 200)


# class TableExportViewTestCase(BaseViewTestCase):
#     """
#     author: Ignatius, Peter
#     """

#     def setUp(self):
#         super(TableExportViewTestCase, self).setUp()

#         self.url = reverse('table_export')

#     def mptest_get(self):
#         """
#         Confirm that app_index returns an appropriate response by checking the
#         status_code and context.
#         """

#         post_response = self.client.post(self.url)
#         eq_(post_response.status_code, 200)


################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################
################################################################################

class CreateAppViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(CreateAppViewTestCase, self).setUp()

        self.url = reverse('publisher_create_app')

    @staticmethod
    def generate_post_data(**kwargs):
        """
        Generate a dict of POST parameters that would be generated by the
        create app view page. This should correspond to generate_app,
        generate_adunit, default_app_dict, and default_adunit_dict functions.
        Optionally pass in keywords to modify the default key/value pairs.
        """
        post_data = {
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u''],
            u'adunit-custom_height': [u''],
            u'app_type': [u'iphone'],
            u'name': [u'Book App'],
            u'package': [u''],
            u'url': [u'', u''],
            u'img_file': [u''],
            u'secondary_category': [u''],
            u'adunit-custom_width': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-app_key': [u''],
            u'adunit-device_format': [u'phone'],
            u'img_url': [u''],
            u'primary_category': [u'books'],
            u'adunit-refresh_interval': [u'0'],
        }
        post_data.update(kwargs)
        return post_data

    def mptest_get(self):
        """
        Confirm that the create_app view returns the correct response to a GET
        request by checking the status_code and context.
        """

        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are not bound.
        ok_(isinstance(get_response.context['app_form'], AppForm))
        ok_(not get_response.context['app_form'].is_bound)
        ok_(isinstance(get_response.context['adunit_form'], AdUnitForm))
        ok_(not get_response.context['adunit_form'].is_bound)

    def mptest_create_app_and_adunit(self):
        """
        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app/adunit were created as expected.
        """

        post_data = self.generate_post_data()

        # We're expecting a statuc code 302 because this view, on successful
        # creation, redirects to the app detail page.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 302)

        # Make sure there are exactly one app and one adunit for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the created app/adunit and convert their models to dicts.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # This page should redirect to the integration help page because this
        # is the first app for this account.
        redirect_url = self.test_client_reverse('publisher_integration_help',
                                                args=[str(adunit.key())])
        redirect_url += '?status=welcome'
        eq_(post_response['Location'], redirect_url)

        # Build dicts of expected app/adunit properties and compare them to
        # the actual state of the db.
        expected_app_dict = default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = default_adunit_dict(self.account, app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        # Make sure the app/adunit were created within the last minute.
        time_almost_eq(app.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

    # This test is broken because of an existing bug in both AppForm (name isn't
    # required) and CreateAppHandler.post (attempts to put None app when form
    # validation fails).
    def mptest_create_app_and_adunit_app_validation(self):
        """
        Confirm that create_app returns the appropriate validation errors when
        no app name is supplied and that the database state does not change.
        """

        # Submit an invalid POST by not supplying the required adunit name.
        post_data = self.generate_post_data(name=[u''])

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are bound. Additionally, confirm that the AppForm did not
        # validate, whereas the AdUnitForm did.
        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(not post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})

    def mptest_create_app_and_adunit_adunit_validation(self):
        """
        Confirm that create_app returns the appropriate validation errors when
        no adunit name is supplied and that the database state does not change.
        """

        # Submit an invalid POST by not supplying the required adunit name.
        # We need to supply kwargs as an expanded dict because 'adunit-name'
        # has a hyphen-minus in its name.
        data = self.generate_post_data(**{'adunit-name': [u'']})

        post_response = self.client.post(self.url, data)
        eq_(post_response.status_code, 200)

        # Check to make sure that AppForm and AdUnitForm are of the appropriate
        # type and are bound. Additionally, confirm that the AdUnitForm did not
        # validate, whereas the AppForm did.
        ok_(isinstance(post_response.context['app_form'], AppForm))
        ok_(post_response.context['app_form'].is_bound)
        ok_(not post_response.context['app_form']._errors)
        ok_(isinstance(post_response.context['adunit_form'], AdUnitForm))
        ok_(post_response.context['adunit_form'].is_bound)
        ok_(post_response.context['adunit_form']._errors)

        # Make sure that the state of the database has not changed, and that
        # there are still no apps nor adunits associated with this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})


class AppUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppUpdateAJAXViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        self.url = reverse(
            'publisher_app_update_ajax',
            args=[str(self.app.key())])

    @staticmethod
    def generate_post_data(**kwargs):
        """
        Generate a dict of POST parameters that would change the name and
        primary category of the app generated by generate_app. Optionally
        pass in keywords to modify the default key/value pairs.
        """
        post_data = {
            u'app_type': [u'iphone'],
            u'name': [u'Business App'],
            u'package': [u''],
            u'url': [u'', u''],
            u'img_file': [u''],
            u'secondary_category': [u''],
            u'ajax': [u'true'],
            u'img_url': [u''],
            u'primary_category': [u'business']
        }
        post_data.update(kwargs)
        return post_data

    def mptest_update_app(self):
        """
        Confirm that app editing works by submitting known good parameters and
        confirming the app was modified as expected. Children adunits should
        not be changed.
        """

        post_data = self.generate_post_data()

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(json.loads(post_response.content), {
            'success': True,
            'errors': [],
        })

        # After updating the app, the account should still own one app and one
        # adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the updated app/adunit and convert them to dicts. Exclude 't'
        # because the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of expected app/adunit properties and compare them to the
        # actual state of the db. Based on our POST data, we expect app name and
        # primary_category to have changed. AdUnit properties should not change.
        expected_app_dict = default_app_dict(
            self.account,
            name=u'Business App',
            primary_category=u'business')
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_validation(self):
        """
        Confirm that posting invalid parameters (i.e. empty app name) will
        result in validation errors and no change to the db state.
        """

        # Remove name from the post parameters to generate a validation error.
        post_data = self.generate_post_data(name=[u''])

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(json.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one app and one adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the app/adunit and convert them to dicts. Exclude 't' because
        # the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of the expected app/adunit properties and compare them to
        # actual state of the db, which should not have changed.
        expected_app_dict = default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_app_authorization(self):
        """
        Attempt to update an app using an unauthorized account. Confirm that the
        correct error is returned and that the db state has not changed.
        """

        self.login_secondary_account()

        post_data = self.generate_post_data()

        # We expect a 404 HTTP response code because the secondary account is
        # not authorized to update this app.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 404)

        # The account should still own exactly one app and one adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the app/adunit and convert them to dicts. Exclude 't' because
        # the exact creation time is unknown.
        app = apps_dict.values()[0]
        app_dict = model_to_dict(app, exclude=['t'])
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build dicts of the expected app/adunit properties and compare them to
        # actual state of the db, which should not have changed.
        expected_app_dict = default_app_dict(self.account)
        dict_eq(app_dict, expected_app_dict, exclude=['t'])
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])


class AdUnitUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitUpdateAJAXViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        self.url = reverse('publisher_adunit_update_ajax')

    def generate_post_data(self, **kwargs):
        """
        Generate a dict of POST parameters that would be generated by the
        app detail or adunit detail pages. This should correspond to the
        generate_adunit and default_adunit_dict functions. Optionally
        pass in keywords to modify the default key/value pairs.
        """
        post_data = {
            u'adunit-app_key': [unicode(self.app.key())],
            u'adunit-name': [u'Banner Ad'],
            u'adunit-description': [u''],
            u'adunit-custom_width': [u''],
            u'adunit-custom_height': [u''],
            u'adunit-format': [u'320x50'],
            u'adunit-device_format': [u'phone'],
            u'adunit-refresh_interval': [u'0'],
            u'ajax': ['true'],
        }
        post_data.update(kwargs)
        return post_data

    def mptest_create_adunit(self):
        """
        Confirm that adunit creation works by submitting known good parameters,
        and confirming the adunit was created as expected by checking db state.
        """

        post_data = self.generate_post_data()

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(json.loads(post_response.content), {
            'success': True,
            'errors': [],
        })

        # This account should now have two adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 2)

        # Obtain the created adunit (the one that is not self.adunit) and
        # convert it to a dict. Exclude 't' because the exact creation time is
        # unknown.
        adunit = adunits_dict.values()[0]
        if adunit.key() == self.adunit.key():
            adunit = adunits_dict.values()[1]

        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db.
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

        # Make sure the adunit was created within the last minute.
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

    def mptest_create_adunit_validation(self):
        """
        Confirm that create_adunit returns the appropriate validation errors
        when no adunit name is supplied and that the database state does not
        change.
        """

        # We POST invalid data by not supplying the required name.
        post_data = self.generate_post_data(**{'adunit-name': [u'']})

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(json.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one app and one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

    def mptest_update_adunit(self):
        """
        Confirm that adunit updating works by submitting known good parameters,
        checking for the appropriate response, and confirming db state.
        """

        # Change the name of an existing adunit by submitting a valid POST. We
        # need to supply kwargs as an expanded dict because 'adunit-name' has a
        # hyphen-minus in its name.
        post_data = self.generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        response = self.client.post(self.url, post_data)
        eq_(response.status_code, 200)

        # Confirm that the JSON response indicated success.
        eq_(json.loads(response.content), {
            'success': True,
            'errors': [],
        })

        # There should still be exactly one adunit for this account.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the updated adunit and convert it to a dict. Exclude 't'
        # because the exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db.
        expected_adunit_dict = default_adunit_dict(
            self.account,
            self.app,
            name=u'Updated Banner Ad')
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_validation(self):
        """
        Confirm that editing an adunit returns the appropriate validation errors
        when no adunit name is supplied and that the database state does not
        change.
        """

        # We POST invalid data by not supplying the required name.
        post_data = self.generate_post_data(**{
            'adunit-name': [u''],
            'adunit_key': [unicode(self.adunit.key())]})

        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 200)

        # Confirm that the JSON response indicated failure with the appropriate
        # validation errors.
        eq_(json.loads(post_response.content), {
            'success': False,
            'errors': [[u'name', u'This field is required.']],
        })

        # The account should still own exactly one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the adunit and convert it to a dict. Exclude 't' because the
        # exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db, which should not have changed.
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])

    def mptest_update_adunit_authorization(self):
        """
        Attempt to update an adunit using an unauthorized account. Confirm that
        the correct error is returned and that the db state has not changed.
        """

        self.login_secondary_account()

        post_data = self.generate_post_data(**{
            'adunit-name': [u'Updated Banner Ad'],
            'adunit_key': [unicode(self.adunit.key())]})

        # We expect a 404 HTTP response code because the secondary account is
        # not authorized to update this adunit.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 404)

        # The account should still own exactly one one adunit.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the adunit and convert it to a dict. Exclude 't' because the
        # exact creation time is unknown.
        adunit = adunits_dict.values()[0]
        adunit_dict = model_to_dict(adunit, exclude=['t'])

        # Build a dict of the expected adunit properties and compare it to
        # actual state of the db, which should not have changed.
        expected_adunit_dict = default_adunit_dict(self.account, self.app)
        dict_eq(adunit_dict, expected_adunit_dict, exclude=['t'])


class DeleteAppViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(DeleteAppViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        self.url = reverse('publisher_delete_app', args=[str(self.app.key())])

    def mptest_delete_app(self):
        """
        Delete an app and confirm that it and its child adunit are no longer
        returned by the query manager.
        """

        # This response should redirect to the inventory page with a status
        # code of 302.
        post_response = self.client.post(self.url)
        eq_(post_response.status_code, 302)

        redirect_url = self.test_client_reverse('app_index')
        eq_(post_response['Location'], redirect_url)

        # There should no longer be any apps or adunits associated with this
        # account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(apps_dict, {})
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})

    def mptest_delete_app_authorization(self):
        """
        Confirm that an attempt to delete an app belonging to a different
        account responds with a 404 and the db state does not change.
        """

        self.login_secondary_account()

        # This should return a status code 404.
        post_response = self.client.post(self.url)
        eq_(post_response.status_code, 404)

        # There should still be exactly one app and one adunit associated with
        # this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)


class DeleteAdUnitViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(DeleteAdUnitViewTestCase, self).setUp()

        self.app = generate_app(self.account)
        self.adunit = generate_adunit(self.account, self.app)

        self.url = reverse('publisher_delete_adunit',
                           args=[str(self.adunit.key())])

    def mptest_delete_adunit(self):
        """
        Delete an adunit and confirm that it is no longer returned by the query
        manager.
        """

        # This response should redirect to the inventory page with a status
        # code of 302.
        post_response = self.client.post(self.url)
        eq_(post_response.status_code, 302)

        redirect_url = self.test_client_reverse('publisher_app_show',
                                                args=[str(self.app.key())])
        eq_(post_response['Location'], redirect_url)

        # There should exactly one app and zero adunits associated with this
        # account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(adunits_dict, {})

    def mptest_delete_adunit_authorization(self):
        """
        Confirm that an attempt to delete an adunit belonging to a different
        account responds with a 404 and the db state does not change.
        """

        self.login_secondary_account()

        # This should return a status code 404.
        post_response = self.client.post(self.url)
        eq_(post_response.status_code, 404)

        # There should still be exactly one app and one adunit associated with
        # this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)
