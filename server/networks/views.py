import logging

from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginInfoForm
from ad_network_reports.models import AdNetworkAppMapper, \
        LoginStates, \
        MANAGEMENT_STAT_NAMES
from ad_network_reports.query_managers import ADMOB, \
        IAD, \
        INMOBI, \
        MOBFOX, \
        MOBFOX_PRETTY, \
        AdNetworkReportManager, \
        AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkManagementStatsManager
from ad_network_reports.query_managers import AD_NETWORK_NAMES as \
        REPORTING_NETWORKS

from common.utils.date_magic import gen_days_for_range
from common.utils.decorators import staff_login_required
from common.ragendja.template import render_to_response, \
        render_to_string, \
        TextResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter

from publisher.query_managers import AppQueryManager, \
        ALL_NETWORKS

from datetime import date, timedelta
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.shortcuts import redirect

from google.appengine.ext import db

# Imports for getting mongo stats
from advertiser.query_managers import AdGroupQueryManager
from advertiser.models import NetworkStates
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

# Form imports
from advertiser.forms import CampaignForm, AdGroupForm
from publisher.query_managers import AdUnitQueryManager

OTHER_NETWORKS = {'millennial': 'Millennial',
                  'ejam': 'eJam',
                  'chartboost': 'ChartBoost',
                  'appnexus': 'AppNexus',
                  'brightroll': 'BrightRoll',
                  'greystripe': 'Greystripe'}

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        def create_and_set(networks, network, app):
            if network not in networks:
                networks[network] = {}
            if 'mopub_app_stats' not in networks[network]:
                networks[network]['mopub_app_stats'] = {}
            if 'mopub_stats' not in networks[network]:
                networks[network]['mopub_stats'] = StatsModel()
            if app.key() not in networks[network]['mopub_app_stats']:
                networks[network]['mopub_app_stats'][app.key()] = \
                        {'stats': StatsModel(),
                         'app': app,
                         'adunits': []}

        days = gen_days_for_range(self.start_date, self.date_range)

        reporting_networks = {}
        other_networks = {}

        # Iterate through all networks that allow reporting
        apps_for_network = None
        for network in REPORTING_NETWORKS.keys():
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = REPORTING_NETWORKS[network]
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()
            if login:
                network_data['pub_ids_without_data'] = login.app_pub_ids
                network_data['state'] = login.state
            else:
                network_data['state'] = LoginStates.NOT_SETUP

            # Get list of apps that need pub ids if they want to be included
            if not login or not login.app_pub_ids:
                if not apps_for_network:
                    apps_for_network = AppQueryManager.get_apps_without_pub_ids(
                            self.account,
                            REPORTING_NETWORKS.keys())
                apps_list = apps_for_network[network] + \
                        apps_for_network[ALL_NETWORKS]

                network_data['apps_without_pub_ids'] = apps_list

            # Create a form for each network and autopopulate fields.
            try:
                login = AdNetworkLoginCredentials. \
                        get_by_ad_network_name(self.account, network)
                form = LoginInfoForm(instance=login, prefix=network)
                # Encryption doesn't work on app engine...
                #form.initial['password'] = login.decoded_password
                #form.initial['username'] = login.decoded_password
            except Exception, error:
                form = LoginInfoForm(prefix=network)
            network_data['form'] = form
            reporting_networks[network] = network_data

        # Iterate through all networks that don't have reporting
        for network in sorted(OTHER_NETWORKS.keys()):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = OTHER_NETWORKS[network]

            other_networks[network] = network_data

        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate the stats for reporting_networks
        # and other_networks
        for app in AppQueryManager.get_apps(self.account):
            network_config = app.network_config
            # Get data from the ad networks
            for network in REPORTING_NETWORKS.keys():
                pub_id = getattr(network_config, network + '_pub_id', '')
                if pub_id:
                    mapper = AdNetworkAppMapper.get_by_publisher_id(pub_id,
                            network)
                    if mapper:
                        create_and_set(reporting_networks, network, app)
                        reporting_networks[network] \
                                ['mopub_app_stats'][app.key()]['pub_id'] = \
                                pub_id

            # Get data collected by MoPub
            adunits = []
            for adgroup in AdGroupQueryManager.get_adgroups(app=app):
                if adgroup.network_state == NetworkStates.NETWORK_ADGROUP:
                    all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                                 advertiser=adgroup,
                                                                 days=days)
                    stats = reduce(lambda x, y: x+y, all_stats, StatsModel())
                    adunit = db.get(adgroup.site_keys[0])
                    adunit.stats = stats
                    if adgroup.network_type in REPORTING_NETWORKS.keys():
                        create_and_set(reporting_networks, adgroup.network_type, app)
                        reporting_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        reporting_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        reporting_networks[adgroup.network_type]['mopub_stats'] += stats
                    elif adgroup.network_type in OTHER_NETWORKS.keys():
                        create_and_set(other_networks, adgroup.network_type, app)
                        other_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        other_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        other_networks[adgroup.network_type]['mopub_stats'] += stats

        reporting_networks = sorted(reporting_networks.values(), key=lambda
                network_data: network_data['name'])
        for network_data in reporting_networks:
            if 'mopub_app_stats' in network_data:
                network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                        app_data: app_data['app'].identifier)

        # TODO: Generalize
        other_networks = sorted(other_networks.values(), key=lambda
                network_data: network_data['name'])
        for network_data in other_networks:
            if 'mopub_app_stats' in network_data:
                network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                        app_data: app_data['app'].identifier)

        # self.account can't access ad_network_* data
        account = AccountQueryManager.get_account_by_key(self.account.key())
        # Settings
        settings = {}
        settings['email'] = account.ad_network_email
        if account.ad_network_recipients:
            settings['recipients'] = ', '.join(account.ad_network_recipients)
        else:
            settings['recipients'] = ', '.join(account.emails)

        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/index.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'show_graph' : True,
                  # Account key needed for form submission to EC2.
                  'settings': settings,
                  'account_key' : str(self.account.key()),
                  'reporting_networks': reporting_networks,
                  'other_networks': other_networks,
                  'LoginStates': LoginStates,
                  'ADMOB': ADMOB,
                  'IAD': IAD,
                  'INMOBI': INMOBI,
                  'MOBFOX': MOBFOX,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

class AddNetworkHandler(RequestHandler):
    TEMPLATE    = 'networks/forms/add_network_form.html'
    def get(self,campaign_form=None, adgroup_form=None, adgroup_key=None):
        adgroup = None
        campaign = None

        # TODO: HACKKKK get price floors done
        initial = {}
        if campaign and campaign.campaign_type in ['marketplace', 'backfill_marketplace']:
            initial.update(price_floor=self.account.network_config.price_floor)
        campaign_form = CampaignForm(instance=campaign, initial=initial)
        adgroup_form = AdGroupForm(instance=adgroup)
        networks = [['admob_native', 'AdMob', False],["adsense","AdSense",False],["brightroll","BrightRoll",False],["ejam","TapIt",False],\
            ["iAd","iAd",False],["inmobi","InMobi",False],["jumptap","Jumptap",False],['millennial_native', 'Millennial Media', False],["mobfox","MobFox",False],\
            ['custom','Custom Network', False], ['custom_native','Custom Native Network', False]]

        all_adunits = AdUnitQueryManager.get_adunits(account=self.account)
        # sorts by app name, then adunit name
        def adunit_cmp(adunit_1, adunit_2):
            app_cmp = cmp(adunit_1.app.name, adunit_2.app.name)
            if not app_cmp:
                return cmp(adunit_1.name, adunit_2.name)
            else:
                return app_cmp

        all_adunits.sort(adunit_cmp)

        adgroup_form['site_keys'].choices = all_adunits # needed for validation TODO: doesn't actually work

        # TODO: Remove this hack to place the bidding info with the rest of campaign
        #Hackish part
        campaign_form.bid    = adgroup_form['bid']
        campaign_form.bid_strategy = adgroup_form['bid_strategy']
        campaign_form.custom_html = adgroup_form['custom_html']
        campaign_form.custom_method = adgroup_form['custom_method']
        campaign_form.network_type = adgroup_form['network_type']

        adunit_keys = adgroup_form['site_keys'].value or []
        adunit_str_keys = [unicode(k) for k in adunit_keys]
        for adunit in all_adunits:
            adunit.checked = unicode(adunit.key()) in adunit_str_keys

        if adgroup_form:
            # We hide deprecated networks by default.  Show them for pre-existing adgroups though
            if adgroup_form['network_type'].value == 'admob' or self.request.user.is_staff:
                networks.append(["admob","AdMob Javascript (deprecated)",False])
            # Allow admins to create Millennial s2s campaigns
            if adgroup_form['network_type'].value == 'millennial' or self.request.user.is_staff:
                networks.append(["millennial","Millennial Server-side (deprecated)",False])
            if adgroup_form['network_type'].value == 'greystripe':
                networks.append(["greystripe","GreyStripe (deprecated)",False])
            for n in networks:
                if adgroup_form['network_type'].value == n[0]:
                    n[2] = True
        elif adgroup:
            for n in networks:
                if adgroup.network_type == n[0]:
                    n[2] = True
        else:
            networks[0][2] = True # select the first by default

        campaign_form.add_context(dict(networks=networks))
        adgroup_form.add_context(dict(all_adunits=all_adunits))

        campaign_create_form_fragment = self.render(campaign_form=campaign_form,adgroup_form=adgroup_form)

        return render_to_response(self.request,'advertiser/new.html',
                {"adgroup_key": adgroup_key,
            "adgroup":adgroup,
            "account": self.account,
            "campaign_create_form_fragment": campaign_create_form_fragment})

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request,template_name=template_name,data=kwargs)

@login_required
def add_network(request, *args, **kwargs):
    return AddNetworkHandler()(request, *args, **kwargs)


@login_required
def network_details(request, *args, **kwargs):
    return NetworkDetailsHandler()(request, *args, **kwargs)
