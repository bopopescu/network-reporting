import datetime
import logging
import os
import simplejson as json
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from django.core.urlresolvers import reverse
from nose.tools import ok_, eq_

from account.models import (DEFAULT_CATEGORIES, LOW_CATEGORIES,
                            MODERATE_CATEGORIES, STRICT_CATEGORIES,
                            DEFAULT_ATTRIBUTES, LOW_ATTRIBUTES,
                            MODERATE_ATTRIBUTES, STRICT_ATTRIBUTES)
from account.query_managers import (NetworkConfigQueryManager,
                                    AccountQueryManager)
from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager)
from common.utils.date_magic import gen_days
from common.utils.test.fixtures import (generate_app, generate_adunit,
                                        generate_campaign, generate_adgroup,
                                        generate_marketplace_creative,
                                        generate_html_creative,
                                        generate_network_campaign,
                                        generate_network_config)
from common.utils.test.test_utils import (confirm_db, dict_eq, list_eq,
                                          model_key_eq, time_almost_eq,
                                          model_eq, ADDED_1, EDITED_1)
from common.utils.test.views import BaseViewTestCase
from common.utils.timezones import Pacific_tzinfo
from publisher.forms import AppForm, AdUnitForm
from publisher.query_managers import PublisherQueryManager, AppQueryManager
from reporting.models import StatsModel


class MarketplaceIndexViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(MarketplaceIndexViewTestCase, self).setUp()

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)
        self.marketplace_campaign.put()

        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

    @confirm_db()
    def mptest_get(self):
        """
        Confirm that marketplace_index returns an appropriate response by
        checking the status_code and context.
        """
        url = reverse('marketplace_index')

        get_response = self.client.get(url)
        eq_(get_response.status_code, 200)

        model_eq(get_response.context['marketplace'], self.marketplace_campaign)
        list_eq(get_response.context['apps'], [self.app])
        list_eq(get_response.context['app_keys'], json.dumps([str(self.app.key())]))
        list_eq(get_response.context['adunit_keys'], [self.adunit.key()])
        eq_(get_response.context['pub_key'], self.account.key())

        end_date = datetime.datetime.now(Pacific_tzinfo()).date()
        start_date = end_date - datetime.timedelta(days=13)

        mpx_stats = {
            'rev': 0.0,
            'daily': [],
            'imp': 0,
            'clk': 0,
            'cpm': 0,
        }
        for date in gen_days(start_date, end_date):
            mpx_stats['daily'].append({
                'rev': 0,
                'date': unicode(date),
                'imp': 0,
                'clk': 0,
                'cpm': 0,
            })
        dict_eq(json.loads(get_response.context['mpx_stats']), mpx_stats)

        list_eq(get_response.context['stats_breakdown_includes'], ['revenue', 'impressions', 'ecpm'])
        dict_eq(get_response.context['totals'], mpx_stats)

        today_stats = mpx_stats["daily"][-1]
        yesterday_stats = mpx_stats["daily"][-2]

        dict_eq(get_response.context['today_stats'], today_stats)
        dict_eq(get_response.context['yesterday_stats'], yesterday_stats)

        stats = {
            'rev': {
                'today': 0,
                'yesterday': 0,
                'total': 0,
            },
            'imp': {
                'today': 0,
                'yesterday': 0,
                'total': 0,
            },
            'cpm': {
                'today': 0,
                'yesterday': 0,
                'total': 0,
            },
        }

        dict_eq(get_response.context['stats'], stats)
        list_eq(get_response.context['blocklist'], [])
        eq_(get_response.context['start_date'], start_date)
        eq_(get_response.context['end_date'], end_date)
        eq_(get_response.context['date_range'], 14)
        ok_(not get_response.context['blind'])

        expected_network_config = generate_network_config(self.account,
                                                          put=False)
        model_eq(get_response.context['network_config'],
                 expected_network_config, check_primary_key=False)


class BlocklistViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(BlocklistViewTestCase, self).setUp()

        self.url = reverse('marketplace_blocklist_change')

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)
        self.marketplace_campaign.put()

        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

    @confirm_db(network_config=EDITED_1)
    def mptest_add(self):
        post_response = self.client.post(self.url, {
            'action': 'add',
            'blocklist': 'http://www.mopub.com',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {
            'success': 'blocklist item(s) added',
            'new': ['http://www.mopub.com'],
        })

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(
            self.account, blocklist=['http://www.mopub.com'])

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def mptest_remove(self):
        self.account.network_config.blocklist = ['http://www.mopub.com']

        AccountQueryManager.update_config_and_put(self.account, self.account.network_config)

        post_response = self.client.post(self.url, {
            'action': 'remove',
            'blocklist': 'http://www.mopub.com',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {
            'success': 'blocklist item(s) removed',
        })

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(self.account)

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)

    @confirm_db()
    def mptest_fail(self):
        post_response = self.client.post(self.url, {
            'blocklist': 'http://www.mopub.com',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {
            'error': 'you must provide an action (add|remove) and a blockist'
        })


class ContentFilterViewTestCase(BaseViewTestCase):
    """
    author: Ignatius, Peter
    """

    def setUp(self):
        super(ContentFilterViewTestCase, self).setUp()

        self.url = reverse('marketplace_content_filter')

        self.app = generate_app(self.account, put=True)
        self.adunit = generate_adunit(self.account, self.app, put=True)

        self.marketplace_campaign = CampaignQueryManager.get_marketplace(self.account)
        self.marketplace_campaign.put()

        self.marketplace_adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                self.adunit.key(), self.account.key())
        self.marketplace_adgroup.put()

    def mptest_none(self):
        post_response = self.client.post(self.url, {
            'filter_level': 'none',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {'success': 'success'})

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(
            self.account, attribute_blocklist=DEFAULT_ATTRIBUTES,
            category_blocklist=DEFAULT_CATEGORIES)

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)

    def mptest_low(self):
        post_response = self.client.post(self.url, {
            'filter_level': 'low',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {'success': 'success'})

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(
            self.account, attribute_blocklist=LOW_ATTRIBUTES,
            category_blocklist=LOW_CATEGORIES)

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)

    def mptest_moderate(self):
        post_response = self.client.post(self.url, {
            'filter_level': 'moderate',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {'success': 'success'})

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(
            self.account, attribute_blocklist=MODERATE_ATTRIBUTES,
            category_blocklist=MODERATE_CATEGORIES)

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)

    def mptest_strict(self):
        post_response = self.client.post(self.url, {
            'filter_level': 'strict',
        })
        ok_(post_response.status_code, 200)

        dict_eq(json.loads(post_response.content), {'success': 'success'})

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
        eq_(len(network_configs_dict.values()), 1)

        expected_network_config = generate_network_config(
            self.account, attribute_blocklist=STRICT_ATTRIBUTES,
            category_blocklist=STRICT_CATEGORIES)

        model_eq(network_configs_dict.values()[0], expected_network_config,
                 check_primary_key=False)
