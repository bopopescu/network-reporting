import os
import sys

sys.path.append(os.environ['PWD'])

import common.utils.test.setup
from common.utils.test.views import BaseViewTestCase
from admin.randomgen import generate_app, generate_adunit

from account.models import NetworkConfig

from publisher.query_managers import PublisherQueryManager, \
        AppQueryManager, \
        AdUnitQueryManager

from advertiser.query_managers import CampaignQueryManager, \
        AdGroupQueryManager, \
        CreativeQueryManager

from advertiser.models import Campaign, \
        NetworkStates
from ad_network_reports.models import AdNetworkLoginCredentials

from networks.forms import NetworkCampaignForm, \
        NetworkAdGroupForm, \
        AdUnitAdGroupForm

from common.constants import NETWORKS

DEFAULT_BID = 0.05
DEFAULT_HTML = 'html_data1'
DEFAULT_PUB_ID = 'pub_id'

class NetworkTestCase(BaseViewTestCase):
    def set_up_existing_apps_and_adunits(self):
        """Creates one app with one adunit for use as a test fixture.

        This method may be overridden in a test case subclass to modify the
        test fixture.

        Author: Andrew He
        """
        app = generate_app(self.account)
        generate_adunit(app, self.account)

    def get_apps_with_adunits(self, account):
            apps = PublisherQueryManager.get_objects_dict_for_account(
                    account=account).values()
            return sorted(apps, key=lambda a: a.name)

    def generate_network_campaign(self, network_type, account, apps):
        """Creates a network campaign along with any necessary adgroups/creatives.

        NOTE: argument apps needs adunits attached.

        Author: Andrew He
        """
        campaigns = CampaignQueryManager.get_network_campaigns(account,
                network_type=network_type)
        # Generate the campaign object.
        if network_type in ('custom', 'custom_native') or campaigns:
            campaign = Campaign(name=NETWORKS[network_type],
                                campaign_type='network',
                                network_type=network_type,
                                network_state=NetworkStates.CUSTOM_NETWORK_CAMPAIGN,
                                account=account)
        else:
            campaign = CampaignQueryManager.get_default_network_campaign(
                account, network_type)

        CampaignQueryManager.put(campaign)

        # Generate one adgroup per adunit.
        for app in apps:
            AppQueryManager.update_config_and_put(app, NetworkConfig())
            for adunit in app.adunits:
                AdUnitQueryManager.update_config_and_put(app, NetworkConfig())

                adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                        adunit.key(), account.key())
                AdGroupQueryManager.put(adgroup)

                # Generate the creative for this adgroup.
                if network_type in ('custom', 'custom_native'):
                    creative = adgroup.default_creative(custom_html=DEFAULT_HTML)
                else:
                    creative = adgroup.default_creative()
                creative.account = account
                CreativeQueryManager.put(creative)

        return campaign

    def setup_post_request_data(self, apps=[], network_type=None, app_pub_ids={},
            adunit_pub_ids={}):

        post_data = {}

        campaign_name = NETWORKS[network_type]
        campaign_form = NetworkCampaignForm({'name': campaign_name})
        post_data.update(campaign_form.data)

        default_adgroup_form = NetworkAdGroupForm()
        post_data.update(default_adgroup_form.data)

        if network_type == 'jumptap':
            post_data['jumptap_pub_id'] = DEFAULT_PUB_ID

        for app in apps:
            app_post_key = 'app_%s-%s_pub_id' % (app.key(), network_type)
            post_data[app_post_key] = app_pub_ids[app.key()]

            for adunit in app.adunits:
                adunit_post_key = 'adunit_%s-%s_pub_id' % \
                        (adunit.key(), network_type)
                post_data[adunit_post_key] = adunit_pub_ids[adunit.key()]

                adgroup_form_data = {'bid': DEFAULT_BID}
                if network_type == 'custom':
                    adgroup_form_data['custom_html'] = DEFAULT_HTML
                elif network_type == 'custom_native':
                    adgroup_form_data['custom_method'] = DEFAULT_HTML
                adgroup_form = AdUnitAdGroupForm(adgroup_form_data)

                for key, item in adgroup_form.data.items():
                    prefixed_key = '%s-%s' % (adunit.key(), key)
                    post_data[prefixed_key] = item

        print post_data
        return post_data

    def generate_ad_network_login(self, network_type, account):
        """Creates and saves an AdNetworkLoginCredentials object.

        Author: Andrew He
        """
        login = AdNetworkLoginCredentials(account=account,
                                          ad_network_name=network_type)
        login.put()
        return login

