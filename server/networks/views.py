import logging

from account.forms import AccountNetworkConfigForm, \
        AppNetworkConfigForm, \
        AdUnitNetworkConfigForm
from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginCredentialsForm
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

DEFAULT_REPORTING_NETWORKS = set(['admob', 'iad', 'inmobi', 'jumptap'])
DEFAULT_OTHER_NETWORKS = set(['millennial'])

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        def create_and_set(networks, network, app, network_names):
            if network not in networks:
                networks[network] = {'name': network,
                                     'pretty_name': network_names[network]}
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

        show_graph = False

        # Iterate through all networks that allow reporting
        apps_for_network = None
        for network in REPORTING_NETWORKS.keys():
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()

            if network not in DEFAULT_REPORTING_NETWORKS and not login:
                continue

            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = REPORTING_NETWORKS[network]

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

        # Iterate through all networks that don't have reporting
        for network in DEFAULT_OTHER_NETWORKS:
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
                        create_and_set(reporting_networks, network, app,
                                REPORTING_NETWORKS)
                        reporting_networks[network] \
                                ['mopub_app_stats'][app.key()]['pub_id'] = \
                                pub_id

            # Get data collected by MoPub
            adunits = []
            for adgroup in AdGroupQueryManager.get_adgroups(app=app):
                if adgroup.network_state == \
                        NetworkStates.NETWORK_ADUNIT_ADGROUP:
                    show_graph = True

                    all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                                 advertiser=adgroup,
                                                                 days=days)

                    stats = reduce(lambda x, y: x+y, all_stats, StatsModel())

                    # One adunit per adgroup for network adunits
                    adunit = db.get(adgroup.site_keys[0])
                    adunit.stats = stats
                    if adgroup.network_type in REPORTING_NETWORKS.keys():
                        create_and_set(reporting_networks,
                                adgroup.network_type, app, REPORTING_NETWORKS)
                        reporting_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        reporting_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        reporting_networks[adgroup.network_type]['mopub_stats'] += stats
                    elif adgroup.network_type in OTHER_NETWORKS.keys():
                        create_and_set(other_networks, adgroup.network_type,
                                app, OTHER_NETWORKS)
                        other_networks[adgroup.network_type] \
                                ['mopub_app_stats'][app.key()]['adunits']. \
                                append(adunit)
                        other_networks[adgroup.network_type]['mopub_app_stats'][app.key()]['stats'] += stats
                        other_networks[adgroup.network_type]['mopub_stats'] += stats

        # Sort networks alphabetically and split them based on networks with
        # statistics and networks without
        reporting_networks = sorted([network_data for network_data in
            reporting_networks.values() if network_data.get('mopub_app_stats',
                False)], key=lambda network_data: network_data['name']) + \
                        sorted([network_data for network_data in
            reporting_networks.values() if not network_data.get(
                'mopub_app_stats', False)], key=lambda network_data:
            network_data['name'])
        for network_data in reporting_networks:
            if 'mopub_app_stats' in network_data:
                network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                        app_data: app_data['app'].identifier)

        # TODO: Generalize
        other_networks = sorted([network_data for network_data in
            other_networks.values() if network_data.get('mopub_app_stats',
                False)], key=lambda network_data: network_data['name']) + \
                        sorted([network_data for network_data in
            other_networks.values() if not network_data.get(
                'mopub_app_stats', False)], key=lambda network_data:
            network_data['name'])
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
                  'show_graph' : show_graph,
                  'settings': settings,
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

class EditNetworkHandler(RequestHandler):
    def get(self,
            network):
        login_form = LoginCredentialsForm()
        adgroup_form = AdGroupForm(is_staff=self.request.user.is_staff)
        account_network_config_form = AccountNetworkConfigForm(instance=self.account.network_config)

        reporting_networks = ' '.join(REPORTING_NETWORKS.keys()) + ' admob_native'

        # TODO: Strip campaign crap from edit_network_form.html
        return render_to_response(self.request,
                                  'networks/templates/forms/edit_network_form.html',
                                  {
                                      'network': network,
                                      'reporting_networks': reporting_networks,
                                      'login_form': login_form,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form': account_network_config_form,
                                  })

    # TODO: Strip campaign crap
    def post(self):
        if not self.request.is_ajax():
            raise Http404

        apps = AppQueryManager.get_apps(account=self.account)
        adunits = AdUnitQueryManager.get_adunits(account=self.account)

        campaign_form = CampaignForm(self.request.POST)
        if campaign_form.is_valid():
            campaign = campaign_form.save()
            campaign.account = self.account
            campaign.save()
            adgroup_form = AdGroupForm(self.request.POST, site_keys=[(unicode(adunit.key()), '') for adunit in adunits], is_staff=self.request.user.is_staff)
            if adgroup_form.is_valid():

                #budget_service.update_budget(campaign, save_campaign = False)
                # And then put in datastore again.
                CampaignQueryManager.put(campaign)

                # TODO: need to make sure a network type is selected if the campaign is a network campaign
                adgroup = adgroup_form.save()
                adgroup.account = campaign.account
                adgroup.campaign = campaign
                # TODO: put this in the adgroup form
                if not adgroup.campaign.campaign_type == 'network':
                    adgroup.network_type = None
                adgroup.save()

                #put adgroup so creative can have a reference to it
                AdGroupQueryManager.put(adgroup)

                if campaign.campaign_type == "network":
                    html_data = None
                    if adgroup.network_type == 'custom':
                        html_data = self.request.POST.get('custom_html', '')
                    elif adgroup.network_type == 'custom_native':
                        html_data = self.request.POST.get('custom_method', '')
                    #build default creative with custom_html data if custom or none if anything else
                    creative = adgroup.default_creative(html_data)
                    if adgroup.net_creative and creative.__class__ == adgroup.net_creative.__class__:
                        #if the adgroup has a creative AND the new creative and old creative are the same class,
                        #ignore the new creative and set the variable to point to the old one
                        creative = adgroup.net_creative
                        if adgroup.network_type == 'custom':
                            #if the network is a custom one, the creative might be the same, but the data might be new, set the old
                            #creative to have the (possibly) new data
                            creative.html_data = html_data
                        elif adgroup.network_type == 'custom_native':
                            creative.html_data = html_data
                    elif adgroup.net_creative:
                        #in this case adgroup.net_creative has evaluated to true BUT the class comparison did NOT.
                        #at this point we know that there was an old creative AND it's different from the new creative so
                        #and delete the old creative just marks as deleted!
                        CreativeQueryManager.delete(adgroup.net_creative)

                    # the creative should always have the same account as the adgroup
                    creative.account = adgroup.account
                    #put the creative so we can reference it
                    CreativeQueryManager.put(creative)
                    #set adgroup to reference the correct creative
                    adgroup.net_creative = creative.key()
                    #put the adgroup again with the new (or old) creative reference
                    AdGroupQueryManager.put(adgroup)

                    # NetworkConfig for Apps
                    if adgroup.network_type in ('admob_native', 'brightroll',
                                                'ejam', 'inmobi', 'jumptap',
                                                'millennial_native', 'mobfox'):
                        # get rid of _native in admob_native, millennial_native
                        network_config_field = "%s_pub_id" % adgroup.network_type.replace('_native', '')

                        for app in apps:
                            network_config = app.network_config or NetworkConfig()
                            setattr(network_config, network_config_field, self.request.POST.get("app_%s_pub_id" % app.key(), ''))
                            AppQueryManager.update_config_and_put(app, network_config)

                        # NetworkConfig for AdUnits
                        if adgroup.network_type in ('admob_native', 'jumptap',
                                                    'millennial_native'):
                            for adunit in adunits:
                                network_config = adunit.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get("adunit_%s_pub_id" % adunit.key(), ''))
                                AdUnitQueryManager.update_config_and_put(adunit, network_config)

                            # NetworkConfig for Account
                            if adgroup.network_type == 'jumptap':
                                network_config = self.account.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get('account_pub_id', ''))
                                AccountQueryManager.update_config_and_put(self.account, network_config)

                # Delete Cache. We leave this in views.py because we
                # must delete the adunits that the adgroup used to have as well
                if adgroup.site_keys:
                    adunits = AdUnitQueryManager.get(adgroup.site_keys)
                    AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

                # Onboarding: user is done after they set up their first campaign
                if self.account.status == "step4":
                    self.account.status = ""
                    AccountQueryManager.put_accounts(self.account)

                CampaignQueryManager.put(campaign)
                AdGroupQueryManager.put(adgroup)

                return JSONResponse({
                    'success': True,
                    'redirect': reverse('advertiser_adgroup_show', args=(adgroup.key(),)),
                })
            else:
                errors = {}
                for key, value in adgroup_form.errors.items():
                    errors[key] = ' '.join([error for error in value])
        else:
            errors = {}
            for key, value in campaign_form.errors.items():
                # TODO: find a less hacky way to get jQuery validator's
                # showErrors function to work with the SplitDateTimeWidget
                if key == 'start_datetime':
                    key = 'start_datetime_1'
                elif key == 'end_datetime':
                    key = 'end_datetime_1'
                errors[key] = ' '.join([error for error in value])

        return JSONResponse({
            'errors': errors,
            'success': False,
        })

@login_required
def edit_network(request, *args, **kwargs):
    return EditNetworkHandler()(request, *args, **kwargs)

class NetworkDetailsHandler(RequestHandler):
    def get(self,
            network):
        """
        Return a webpage with the network statistics.
        """
        days = gen_days_for_range(self.start_date, self.date_range)

        network_data = {}
        network_data['name'] = network
        network_data['pretty_name'] = REPORTING_NETWORKS.get(network, False) or \
                OTHER_NETWORKS.get(network, False)

        if not network_data['pretty_name']:
            raise Http404

        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate the stats for network_data
        for app in AppQueryManager.get_apps(self.account):
            network_config = app.network_config
            # Get data from the ad network
            pub_id = getattr(network_config, network + '_pub_id', '')
            if pub_id:
                mapper = AdNetworkAppMapper.get_by_publisher_id(pub_id,
                        network)
                if mapper:
                    create_and_set(reporting_networks, network, app,
                            REPORTING_NETWORKS)
                    network_data['mopub_app_stats'][app.key()]['pub_id'] = \
                            pub_id

            # Get data collected by MoPub
            adunits = []
            for adgroup in AdGroupQueryManager.get_adgroups(app=app):
                if adgroup.network_state == \
                        NetworkStates.NETWORK_ADUNIT_ADGROUP:

                    all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                                 advertiser=adgroup,
                                                                 days=days)

                    stats = reduce(lambda x, y: x+y, all_stats, StatsModel())

                    # One adunit per adgroup for network adunits
                    adunit = db.get(adgroup.site_keys[0])
                    adunit.stats = stats
                    network_data['mopub_app_stats'][app.key()]['adunits'].append(adunit)
                    network_data['mopub_app_stats'][app.key()]['stats'] += stats
                    network_data['mopub_stats'] += stats

        if 'mopub_app_stats' in network_data:
            network_data['mopub_app_stats'] = sorted(network_data['mopub_app_stats'].values(), key=lambda
                    app_data: app_data['app'].identifier)

        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/details.html',
              {
                  'start_date' : days[0],
                  'end_date' : days[-1],
                  'date_range' : self.date_range,
                  'show_graph' : True,
                  'network': network_data,
                  'ADMOB': ADMOB,
                  'IAD': IAD,
                  'INMOBI': INMOBI,
                  'MOBFOX': MOBFOX,
                  'REPORTING_NETWORKS': REPORTING_NETWORKS,
              })

@login_required
def network_details(request, *args, **kwargs):
    return NetworkDetailsHandler()(request, *args, **kwargs)
