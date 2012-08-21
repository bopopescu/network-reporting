import datetime
import os
import simplejson as json
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager)
from common.utils.date_magic import gen_days
from common.utils.test.fixtures import (generate_app, generate_adunit,
                                        generate_campaign, generate_adgroup,
                                        generate_marketplace_creative,
                                        generate_html_creative,
                                        generate_network_campaign)
from common.utils.test.test_utils import (confirm_all_models, confirm_db,
                                          dict_eq, list_eq, model_key_eq,
                                          time_almost_eq, model_eq, ADDED_1,
                                          EDITED_1)
from common.utils.test.views import BaseViewTestCase
from common.utils.timezones import Pacific_tzinfo
from publisher.forms import AppForm, AdUnitForm
from publisher.query_managers import (PublisherQueryManager,
                                      AppQueryManager,
                                      AdUnitQueryManager)
from reporting.models import StatsModel


from account.models import NetworkConfig
from publisher.models import App, AdUnit
from advertiser.models import Campaign, AdGroup, Creative


class DashboardViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(DashboardViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

    @confirm_db()
    def mptest_get(self):
        """
        Confirm that dashboard returns an appropriate response by checking the
        status_code and context.
        """
        url = reverse('dashboard')

        get_response = self.client.get(url)
        eq_(get_response.status_code, 200)

        eq_(get_response.context['page_width'], 'wide')

        marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)

        # Names is a dict mapping internal representation to readable names. It
        # includes source types and all model keys for an account.
        names = {
            'direct': 'Direct Sold',
            'mpx': 'Marketplace',
            'network': 'Ad Networks',
            str(self.app.key()): self.app.name,
            str(self.adunit.key()): self.adunit.name,
            str(marketplace_campaign.key()): marketplace_campaign.name
        }
        dict_eq(get_response.context['names'], names)


class AppIndexViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppIndexViewTestCase, self).setUp()

        self.url = reverse('app_index')

    @confirm_db()
    def mptest_get_without_app(self):
        """
        Confirm that app_index returns a redirect to the create app page when
        the account has no apps.
        """
        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 302)

        redirect_url = self.test_client_reverse('publisher_create_app')
        eq_(get_response['Location'], redirect_url)

    @confirm_db(app=ADDED_1)
    def mptest_get_with_app(self):
        """
        Confirm that app_index returns an appropriate response when the account
        has an app by checking the status_code and context.
        """
        app = generate_app(self.account, put=True)

        get_response = self.client.get(self.url)
        eq_(get_response.status_code, 200)

        list_eq(get_response.context['apps'], [app])
        eq_(get_response.context['app_keys'], json.dumps([str(app.key())]))


class AppDetailViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AppDetailViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        # Create a campaign and adgroup that doesn't target our app's adunit to
        # confirm that it doesn't show up on this page.
        self.untargetted_campaign = generate_campaign(self.account, put=True)
        self.untargetted_adgroup = generate_adgroup(self.account, self.untargetted_campaign, put=True)

        # Create campaigns and adgroups of each adgroup_type. Each adgroup
        # targets our adunit by setting its site_keys property.
        site_keys = [self.adunit.key()]

        self.gtee_high_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_high_adgroup = generate_adgroup(
            self.account, self.gtee_high_campaign, put=True,
            adgroup_type='gtee_high', site_keys=site_keys)

        self.gtee_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_adgroup = generate_adgroup(
            self.account, self.gtee_campaign, put=True, adgroup_type='gtee',
            site_keys=site_keys)

        self.gtee_low_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_low_adgroup = generate_adgroup(
            self.account, self.gtee_low_campaign, put=True,
            adgroup_type='gtee_low', site_keys=site_keys)

        self.promo_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.promo_adgroup = generate_adgroup(
            self.account, self.promo_campaign, put=True, adgroup_type='promo',
            site_keys=site_keys)

        self.backfill_promo_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.backfill_promo_adgroup = generate_adgroup(
            self.account, self.backfill_promo_campaign, put=True,
            adgroup_type='backfill_promo', site_keys=site_keys)

        # Use the query manager methods to create the marketplace campaign and
        # adgroup and put them to the db.
        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        self.marketplace_campaign.put()
        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

        # Create network campaign and adgroups.
        self.network_campaign = generate_network_campaign(
                self.account, 'mobfox', put=True)

        self.url = reverse('publisher_app_show', args=[str(self.app.key())])

    @confirm_db()
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

        marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        list_eq(get_response.context['marketplace'],
            [marketplace_campaign])
        list_eq(get_response.context['network'], [self.network_campaign])
        list_eq(get_response.context['backfill_promo'],
            [self.backfill_promo_campaign])

    @confirm_db()
    def mptest_get_authorization(self):
        """
        Confirm that app detail returns a 404 when an unauthorized account
        attempts to access it.
        """

        self.login_secondary_account()

        get_response = self.client.get(self.url)
        ok_(get_response.status_code, 404)


class AdUnitShowViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitShowViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        # Create a campaign and adgroup that doesn't target our adunit to
        # confirm that it doesn't show up on this page.
        self.untargetted_campaign = generate_campaign(self.account, put=True)
        self.untargetted_adgroup = generate_adgroup(self.account, self.untargetted_campaign, put=True)

        # Create campaigns and adgroups of each adgroup_type. Each adgroup
        # targets our adunit by setting its site_keys property.
        site_keys = [self.adunit.key()]

        self.gtee_high_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_high_adgroup = generate_adgroup(
            self.account, self.gtee_high_campaign, put=True,
            adgroup_type='gtee_high', site_keys=site_keys)

        self.gtee_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_adgroup = generate_adgroup(
            self.account, self.gtee_campaign, put=True, adgroup_type='gtee',
            site_keys=site_keys)

        self.gtee_low_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.gtee_low_adgroup = generate_adgroup(
            self.account, self.gtee_low_campaign, put=True,
            adgroup_type='gtee_low', site_keys=site_keys)

        self.promo_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.promo_adgroup = generate_adgroup(
            self.account, self.promo_campaign, put=True, adgroup_type='promo',
            site_keys=site_keys)

        self.backfill_promo_campaign = generate_campaign(
            self.account, put=True, campaign_type='order')
        self.backfill_promo_adgroup = generate_adgroup(
            self.account, self.backfill_promo_campaign, put=True,
            adgroup_type='backfill_promo', site_keys=site_keys)

        # Use the query manager methods to create the marketplace campaign and
        # adgroup and put them to the db.
        self.marketplace_campaign = CampaignQueryManager.get_marketplace(
            self.account)
        self.marketplace_campaign.put()
        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
            self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

        # Create network campaign and adgroups.
        self.network_campaign = generate_network_campaign(
                self.account, 'mobfox', put=True)

        self.url = reverse('publisher_adunit_show',
                           args=[str(self.adunit.key())])

    @confirm_db()
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

        network_adgroup = AdGroupQueryManager.get_network_adgroup(
            self.network_campaign, self.adunit.key(), self.account.key())
        list_eq(get_response.context['network'], [network_adgroup])
        list_eq(get_response.context['backfill_promo'],
                [self.backfill_promo_adgroup])

    @confirm_db()
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

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.url = reverse('publisher_integration_help',
                           args=[str(self.adunit.key())])

    @confirm_db()
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

    @confirm_db()
    def mptest_get_authorization(self):
        """
        Confirm that integration help returns a 404 when an unauthorized account
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

#     def mptest_get_authorization(self):
#         """
#         """
#         self.login_secondary_account()

#         get_response = self.client.get(self.url)
#         ok_(get_response.status_code, 404)


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

class NewCreateAppViewTestCase(BaseViewTestCase):
    """
    NewCreateAppViewTestCase will replcae CreateAppViewTestCase because it uses
    the confirm_all_models helper which makes tests cleaner and tests for more things.
    It's not replcaed yet because I'm being lazy and don't want to look into
    everything that CreateAppViewTestCase tests for

        Author: Tiago Bandeira (8/16/2012)
    """
    def setUp(self):
        super(NewCreateAppViewTestCase, self).setUp()

        self.post_data = {
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

        self.url = reverse('publisher_create_app')

    def mptest_create_app_and_adunit(self):
        """Create an app and adunit

        Author: Tiago Bandeira (8/16/2012)
        """
        c = Campaign.all().get()
        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           edited={self.account.key(): {'status': 'step4'}},
                           added={App: 1,
                                  AdUnit: 1,
                                  NetworkConfig: 2,
                                  Campaign: 1,
                                  AdGroup: 2,
                                  Creative: 2},
                           response_code=302)

    def mptest_create_network_adgroup(self):
        """Create an app and adunit. Make sure adgroup is created for the network campaign for the new adunit.

        Author: Tiago Bandeira (8/16/2012)
        """
        self.network_campaign = generate_network_campaign(
                self.account, 'admob', put=True)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           edited={self.account.key(): {'status': 'step4'}},
                           added={App: 1,
                                  AdUnit: 1,
                                  NetworkConfig: 2,
                                  Campaign: 1,
                                  AdGroup: 3,
                                  Creative: 3},
                           response_code=302)

    def mptest_create_network_adgroup_and_copy_settings(self):
        """Create an app and adunit. Make sure adgroup is created for the network campaign for the new adunit.

        Author: Tiago Bandeira (8/16/2012)
        """
        app = generate_app(self.account)
        AppQueryManager.put(app)
        adunit = generate_adunit(self.account, app)
        AdUnitQueryManager.put(adunit)

        self.network_campaign = generate_network_campaign(
                self.account, 'admob', put=True)

        adgroup = self.network_campaign.adgroups[0]

        # modify global adgroup settings
        adgroup.device_targeting = True

        adgroup.target_iphone = True
        adgroup.target_ipod = True
        adgroup.target_ipad = False
        adgroup.target_android = True
        adgroup.target_other = False

        adgroup.ios_version_min = '2.1+'
        adgroup.ios_version_max = '3.2+'

        adgroup.android_version_min = '1.6'
        adgroup.android_version_max = '2.2'

        adgroup.geo_predicates = [u'country_name=BR']
        adgroup.cities = [u'-22.90277778,-43.2075:21:Rio de Janeiro:BR', u'-23.5475,-46.63611111:27:Sao Paolo:BR']
        adgroup.keywords = ['abc', 'de', 'fg']

        AdGroupQueryManager.put(adgroup)

        confirm_all_models(self.client.post,
                           args=[self.url, self.post_data],
                           kwargs={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'},
                           edited={self.account.key(): {'status': 'step4'}},
                           added={App: 1,
                                  AdUnit: 1,
                                  NetworkConfig: 2,
                                  AdGroup: 2,
                                  Creative: 2},
                           response_code=302)

        # verify settings have been copied over
        new_adgroup = [ag for ag in self.network_campaign.adgroups if ag.key() != adgroup.key()][0]
        model_eq(adgroup, new_adgroup, exclude=['site_keys', 't', 'active', 'created'], check_primary_key=False)


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

    @confirm_db()
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

    @confirm_db(app=ADDED_1, adunit=ADDED_1, campaign=ADDED_1,
                adgroup={'added': 2}, creative={'added': 2},
                account={'edited': 1}, network_config={'added': 2})
    def mptest_create_first_app_and_adunit(self):
        """mptest_create_first_app_and_adunit

        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app/adunit were created as expected.
        """

        post_data = self.generate_post_data()

        # We're expecting a status code 302 because this view, on successful
        # creation, redirects to the integration help page.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 302)

        # Make sure there are exactly one app and one adunit for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the created app/adunit.
        app = apps_dict.values()[0]
        adunit = adunits_dict.values()[0]

        # This page should redirect to the integration help page.
        redirect_url = self.test_client_reverse('publisher_integration_help',
                                                args=[str(adunit.key())])
        redirect_url += '?status=welcome'
        eq_(post_response['Location'], redirect_url)

        # Compare the app/adunit to their expected models.
        expected_app = generate_app(self.account)
        model_eq(app, expected_app, exclude=['network_config', 't'], check_primary_key=False)

        expected_adunit = generate_adunit(self.account, app)
        model_eq(adunit, expected_adunit, exclude=['network_config', 't'], check_primary_key=False)

        # Make sure the app/adunit were created within the last minute.
        time_almost_eq(app.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

        # CAMPAIGNS
        # When you create your first app/adunit, marketplace and
        # backfill_promo campaigns/adgroups/creatives are created.
        campaigns_dict = AdvertiserQueryManager.get_campaigns_dict_for_account(
            self.account)
        eq_(len(campaigns_dict), 2)

        marketplace_campaign = self._get_object(
            lambda campaign: campaign.campaign_type == 'marketplace',
            campaigns_dict.values())
        expected_marketplace_campaign = generate_campaign(
            self.account, active=False, name="MarketPlace",
            advertiser='marketplace', campaign_type="marketplace")
        model_eq(marketplace_campaign, expected_marketplace_campaign,
            check_primary_key=False, exclude=['created'])

        backfill_promo_campaign = self._get_object(
            lambda campaign: campaign.campaign_type == 'order',
            campaigns_dict.values())
        expected_backfill_promo_campaign = generate_campaign(
            self.account, name="MoPub Demo Order",
            description="Demo Order for checking that MoPub works for your" +
            " application")
        model_eq(backfill_promo_campaign, expected_backfill_promo_campaign,
            check_primary_key=False, exclude=['created'])

        # ADGROUPS
        adgroups_dict = AdvertiserQueryManager.get_adgroups_dict_for_account(
            self.account)
        eq_(len(adgroups_dict), 2)

        marketplace_adgroup = self._get_object(
            lambda adgroup: adgroup.adgroup_type == 'marketplace',
            adgroups_dict.values())
        expected_marketplace_adgroup = generate_adgroup(
            self.account, marketplace_campaign, name='Marketplace',
            adgroup_type='marketplace', site_keys=[adunit.key()])
        model_eq(marketplace_adgroup, expected_marketplace_adgroup,
            check_primary_key=False, exclude=['created', 't'])

        backfill_promo_adgroup = self._get_object(
            lambda adgroup: adgroup.adgroup_type == 'backfill_promo',
            adgroups_dict.values())
        expected_backfill_promo_adgroup = generate_adgroup(
            self.account, backfill_promo_campaign, name="MoPub Demo Line Item",
            adgroup_type='backfill_promo', site_keys=[adunit.key()], bid=1.0)
        model_eq(backfill_promo_adgroup, expected_backfill_promo_adgroup,
            check_primary_key=False, exclude=['created', 't', 'start_datetime'])

        # CREATIVES
        creatives_dict = AdvertiserQueryManager.get_creatives_dict_for_account(
            self.account)
        eq_(len(creatives_dict), 2)

        marketplace_creative = self._get_object(
            lambda creative: creative.ad_group.key() == marketplace_adgroup.key(),
            creatives_dict.values())
        expected_marketplace_creative = generate_marketplace_creative(
            self.account, marketplace_adgroup, name='marketplace dummy',
            ad_type='html')
        model_eq(marketplace_creative, expected_marketplace_creative,
            check_primary_key=False, exclude=['t'])

        backfill_promo_creative = self._get_object(
            lambda creative: creative.ad_group.key() == backfill_promo_adgroup.key(),
            creatives_dict.values())
        default_creative_html = """
    <style type="text/css">
    body {
      font-size: 12px;
      font-family: helvetica,arial,sans-serif;
      margin:0;
      padding:0;
      text-align:center;
      background:white
    }
    .creative_headline {
      font-size: 18px;
    }
    .creative_promo {
      color: green;
      text-decoration: none;
    }
    </style>
    <div class="creative_headline">
      Welcome to mopub!
    </div>
    <div class="creative_promo">
      <a href="http://www.mopub.com">
        Click here to test ad
      </a>
    </div>
    <div>
      You can now set up a new campaign to serve other ads.
    </div>
    """
        expected_backfill_promo_creative = generate_html_creative(
            self.account, backfill_promo_adgroup, name="Demo HTML Creative",
            html_data=default_creative_html, ad_type="html")
        model_eq(backfill_promo_creative, expected_backfill_promo_creative,
            check_primary_key=False, exclude=['t'])

    @confirm_db(app={'added': 2}, adunit={'added': 2},
                adgroup={'added': 1}, creative={'added': 1},
                account={'edited': 1}, network_config={'added': 2})
    def mptest_create_additional_app_and_adunit(self):
        """mptest_create_additional_app_and_adunit

        Confirm the entire app creation workflow by submitting known good
        parameters, and confirming the app/adunit were created as expected.
        """

        # Generate a filler app/adunit pair to test creation of additional
        # apps/adunits.
        filler_app = generate_app(self.account, put=True)
        filler_adunit = generate_adunit(self.account, filler_app, put=True)

        post_data = self.generate_post_data()

        # We're expecting a status code 302 because this view, on successful
        # creation, redirects to the integration help page.
        post_response = self.client.post(self.url, post_data)
        eq_(post_response.status_code, 302)

        # Make sure there are exactly two app/adunit pairs for this account.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 2)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 2)

        # Obtain the created app/adunit.
        new_apps = filter(
            lambda app: app.key() != filler_app.key(), apps_dict.values())
        app = new_apps[0]
        new_adunits = filter(
            lambda adunit: adunit.key() != filler_adunit.key(),
            adunits_dict.values())
        adunit = new_adunits[0]

        # This page should redirect to the integration help page.
        redirect_url = self.test_client_reverse('publisher_integration_help',
                                                args=[str(adunit.key())])
        redirect_url += '?status=welcome'
        eq_(post_response['Location'], redirect_url)

        # Compare the app/adunit to their expected models.
        expected_app = generate_app(self.account)
        model_eq(app, expected_app, exclude=['network_config', 't'], check_primary_key=False)

        expected_adunit = generate_adunit(self.account, app)
        model_eq(adunit, expected_adunit, exclude=['network_config', 't'], check_primary_key=False)

        # Make sure the app/adunit were created within the last minute.
        time_almost_eq(app.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

    @staticmethod
    def _get_object(lambda_, list_):
        objects = filter(lambda_, list_)
        eq_(len(objects), 1)
        return objects[0]

    @confirm_db()
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

    @confirm_db()
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

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

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
            u'url': [u''],
            u'img_file': [u''],
            u'secondary_category': [u''],
            u'ajax': [u'true'],
            u'img_url': [u''],
            u'primary_category': [u'business']
        }
        post_data.update(kwargs)
        return post_data

    @confirm_db(app=EDITED_1)
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

        # Obtain the updated app/adunit.
        app = apps_dict.values()[0]
        adunit = adunits_dict.values()[0]

        # Compare the app/adunit to their expected models. Name and
        # primary_category should have been updated.
        expected_app = generate_app(self.account,
                        key=self.app.key(),
                        name=post_data['name'][0],
                        primary_category=post_data['primary_category'][0])
        model_eq(app, expected_app)

        expected_adunit = generate_adunit(
            self.account, app, key=self.adunit.key())
        model_eq(adunit, expected_adunit)

    @confirm_db()
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

        # Obtain the app/adunit.
        app = apps_dict.values()[0]
        adunit = adunits_dict.values()[0]

        # Compare the app/adunit to their expected models. Nothing should have
        # changed due to the validation error.
        expected_app = generate_app(self.account,
                        key=self.app.key())
        model_eq(app, expected_app)

        expected_adunit = generate_adunit(
            self.account, app, key=self.adunit.key())
        model_eq(adunit, expected_adunit)

    @confirm_db()
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

        # The account should still own exactly one app and one adunit.
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(
            account=self.account)
        eq_(len(apps_dict), 1)
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 1)

        # Obtain the app/adunit.
        app = apps_dict.values()[0]
        adunit = adunits_dict.values()[0]

        # Compare the app/adunit to their expected models. Nothing should have
        # changed due to the authorization error.
        expected_app = generate_app(self.account,
                        key=self.app.key())
        model_eq(app, expected_app)

        expected_adunit = generate_adunit(
            self.account, app, key=self.adunit.key())
        model_eq(adunit, expected_adunit)


class AdUnitUpdateAJAXViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(AdUnitUpdateAJAXViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

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

    @confirm_db(adunit=ADDED_1, adgroup=ADDED_1, creative=ADDED_1, network_config=ADDED_1)
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

        # This account should now have two adunits.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(
            account=self.account)
        eq_(len(adunits_dict), 2)

        # Obtain the created adunit (the one that is not self.adunit) and
        # convert it to a dict. Exclude 't' because the exact creation time is
        # unknown.
        adunit = adunits_dict.values()[0]
        if adunit.key() == self.adunit.key():
            adunit = adunits_dict.values()[1]

        # Compare the adunit to its expected models.
        expected_adunit = generate_adunit(self.account, self.app,
                                name=post_data['adunit-name'][0])
        model_eq(adunit, expected_adunit, exclude=['network_config', 't'], check_primary_key=False)

        # Make sure the adunit was created within the last minute.
        time_almost_eq(adunit.t,
                       datetime.datetime.utcnow(),
                       datetime.timedelta(minutes=1))

        adgroups_dict = AdvertiserQueryManager.get_adgroups_dict_for_account(
            account=self.account)
        eq_(len(adgroups_dict), 1)

        marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)

        marketplace_adgroup = adgroups_dict.values()[0]
        expected_marketplace_adgroup = generate_adgroup(
            self.account, marketplace_campaign, name='Marketplace',
            adgroup_type='marketplace', site_keys=[adunit.key()])
        model_eq(marketplace_adgroup, expected_marketplace_adgroup,
            check_primary_key=False, exclude=['created', 't'])

        creatives_dict = AdvertiserQueryManager.get_creatives_dict_for_account(
            self.account)
        eq_(len(creatives_dict), 1)

        marketplace_creative = creatives_dict.values()[0]
        expected_marketplace_creative = generate_marketplace_creative(
            self.account, marketplace_adgroup, name='marketplace dummy',
            ad_type='html')
        model_eq(marketplace_creative, expected_marketplace_creative,
            check_primary_key=False, exclude=['t'])

    @confirm_db()
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

    @confirm_db(adunit=EDITED_1)
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

        # Obtain the updated adunit.
        adunit = adunits_dict.values()[0]

        # Compare the adunit to its expected models. The name should have been
        # changed.
        expected_adunit = generate_adunit(self.account, self.app,
                                key=self.adunit.key(),
                                name=post_data['adunit-name'][0])
        model_eq(adunit, expected_adunit)

    @confirm_db()
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

        # Obtain the adunit.
        adunit = adunits_dict.values()[0]

        # Compare the adunit to its expected models. Nothing should have changed
        # due to the validation error.
        expected_adunit = generate_adunit(self.account, self.app,
                                key=self.adunit.key(),)
        model_eq(adunit, expected_adunit)

    @confirm_db()
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

        # Compare the adunit to its expected models. Nothing should have changed
        # due to the authorization error.
        expected_adunit = generate_adunit(self.account, self.app,
                                key=self.adunit.key(),)
        model_eq(adunit, expected_adunit)


class DeleteAppViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(DeleteAppViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.url = reverse('publisher_delete_app', args=[str(self.app.key())])

    @confirm_db(app=EDITED_1, adunit=EDITED_1)
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

    @confirm_db()
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

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.url = reverse('publisher_delete_adunit',
                           args=[str(self.adunit.key())])

    @confirm_db(adunit=EDITED_1)
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

    @confirm_db()
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
