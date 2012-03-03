import logging

from account.forms import AccountNetworkConfigForm, \
        AppNetworkConfigForm, \
        AdUnitNetworkConfigForm
from account.query_managers import AccountQueryManager

from ad_network_reports.forms import LoginCredentialsForm
from ad_network_reports.models import AdNetworkAppMapper, \
        AdNetworkStats, \
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
from advertiser.query_managers import AdGroupQueryManager, \
        CampaignQueryManager
from advertiser.models import NetworkStates
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

# Form imports
from advertiser.forms import CampaignForm, AdGroupForm
from publisher.query_managers import AdUnitQueryManager

import copy

OTHER_NETWORKS = {'millennial': 'Millennial',
                  'ejam': 'eJam',
                  'chartboost': 'ChartBoost',
                  'appnexus': 'AppNexus',
                  'brightroll': 'BrightRoll',
                  'greystripe': 'Greystripe'}

DEFAULT_NETWORKS = set(['admob', 'iad', 'inmobi', 'jumptap', 'millennial'])

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        days = gen_days_for_range(self.start_date, self.date_range)

        networks_to_setup = copy.copy(DEFAULT_NETWORKS)
        additional_networks = set(OTHER_NETWORKS.keys())
        networks = []
        reporting_networks = []
        reporting = False

        logging.info(DEFAULT_NETWORKS)

        graph_stats = []
        stats_manager = StatsModelQueryManager(account=self.account)
        for network in DEFAULT_NETWORKS.union(set(OTHER_NETWORKS.keys())):
            campaign = CampaignQueryManager.get_network_campaign(self. \
                    account.key(), network)

            login = False
            network_data = {}
            if network in REPORTING_NETWORKS:
                login = AdNetworkLoginManager.get_login(self.account,
                        network).get()

                if login:
                    reporting_networks.append(network)
                    network_data['reporting'] = True

            if campaign or login:
                logging.info(campaign)
                if campaign:
                    logging.info(str(campaign.key()))

                network_data['name'] = network
                network_data['pretty_name'] = REPORTING_NETWORKS.get(network,
                        False) or OTHER_NETWORKS[network]

                all_stats = stats_manager.get_stats_for_days(publisher=None,
                                                             advertiser= \
                                                                     campaign,
                                                             days=days)
                stats = reduce(lambda x, y: x+y, all_stats, StatsModel())

                # Format graph stats
                temp_stats = copy.copy(stats)
                temp_stats = temp_stats.to_dict()
                temp_stats['daily_stats'] = [s2.to_dict() for s2 in
                        sorted(all_stats, key=lambda s1: s1.date)]
                temp_stats['name'] = network_data['pretty_name']
                graph_stats.append(temp_stats)

                network_data['mopub_stats'] = stats

                networks_to_setup -= set([network])
                additional_networks -= set([network])

                networks.append(network_data)


        networks_to_setup_ = []
        # Generate list of main networks that can be setup
        for network in sorted(networks_to_setup):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] =  REPORTING_NETWORKS.get(network,
                        False) or OTHER_NETWORKS[network]

            networks_to_setup_.append(network_data)

        additional_networks_ = []
        # Generate list of main networks that can be setup
        for network in sorted(additional_networks):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] =  REPORTING_NETWORKS.get(network,
                        False) or OTHER_NETWORKS[network]

            additional_networks_.append(network_data)

        # Sort networks alphabetically
        networks = sorted(networks, key=lambda network_data:
                network_data['name'])

        from django.utils import simplejson

        graph_stats = simplejson.dumps(graph_stats)

        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/index.html',
              {
                  'start_date': days[0],
                  'end_date': days[-1],
                  'date_range': self.date_range,
                  'graph_stats': graph_stats,
                  'networks': networks,
                  'networks_to_setup': networks_to_setup_,
                  'additional_networks': additional_networks_,
                  'reporting_networks': reporting_networks,
                  'MOBFOX': MOBFOX,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

class EditNetworkHandler(RequestHandler):
    def get(self,
            network):
        network_data = {}
        network_data['name'] = network
        network_data['pretty_name'] = REPORTING_NETWORKS.get(network, False) or \
                OTHER_NETWORKS.get(network, False)

        campaign_form = CampaignForm()
        login_form = LoginCredentialsForm()
        adgroup_form = AdGroupForm(is_staff=self.request.user.is_staff)
        account_network_config_form = AccountNetworkConfigForm(instance=self.account.network_config)

        reporting_networks = ' '.join(REPORTING_NETWORKS.keys()) + ' admob_native'

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        for app in apps:
            app.network_config_form = AppNetworkConfigForm(instance=app.network_config, prefix="app_%s" % app.key())
            app.adunits = []
            for adunit in app.all_adunits:
                adunit.network_config_form = AdUnitNetworkConfigForm(instance=adunit.network_config, prefix="adunit_%s" % adunit.key())
                app.adunits.append(adunit)

        # TODO: Strip campaign crap from edit_network_form.html
        return render_to_response(self.request,
                                  'networks/edit_network_form.html',
                                  {
                                      'account_key': str(self.account.key()),
                                      'network': network_data,
                                      'campaign_form': campaign_form,
                                      'REPORTING_NETWORKS': REPORTING_NETWORKS,
                                      'reporting_networks': reporting_networks,
                                      'login_form': login_form,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form': account_network_config_form,
                                      'apps': apps,
                                  })

    # TODO: Add campaign to form
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

        network_data['reporting'] = False

        stats_by_day = {}
        for day in days:
            stats_by_day[day] = StatsModel()

        reporting_stats_by_day = {}
        for day in days:
            reporting_stats_by_day[day] = AdNetworkStats()

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
                    if 'mopub_app_stats' not in network_data:
                        network_data['mopub_app_stats'] = {}
                    if app.key() not in network_data['mopub_app_stats']:
                        network_data['mopub_app_stats'][app.key()] = app
                    network_data['mopub_app_stats'][app.key()].pub_id = pub_id

                    # Get reporting graph stats
                    reporting_stats = AdNetworkStatsManager. \
                            get_stats_list_for_mapper_and_days(mapper.key(),
                                    days)
                    for stats in reporting_stats:
                        if stats.date in reporting_stats_by_day:
                            reporting_stats_by_day[stats.date] += stats

                    network_data['reporting'] = True

            # Get data collected by MoPub
            adunits = []
            for adunit in AdUnitQueryManager.get_adunits(account=self.account,
                    app=app):
                # One adunit per adgroup for network adunits
                adgroup = AdGroupQueryManager.get_network_adunit_adgroup(
                        adunit.key(),
                        self.account.key(), network)

                all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                             advertiser=adgroup,
                                                             days=days)
                for stats in all_stats:
                    if stats.date.date() in stats_by_day:
                        stats_by_day[stats.date.date()] += stats

                stats = reduce(lambda x, y: x+y, all_stats, StatsModel())

                adunit.stats = stats
                if 'mopub_app_stats' not in network_data:
                    network_data['mopub_app_stats'] = {}
                if app.key() not in network_data['mopub_app_stats']:
                    network_data['mopub_app_stats'][app.key()] = app
                if not hasattr(network_data['mopub_app_stats'][app.key()],
                        'adunits'):
                    network_data['mopub_app_stats'][app.key()].adunits = []

                network_data['mopub_app_stats'][app.key()].adunits.append(
                        adunit)

                if hasattr(network_data['mopub_app_stats'][app.key()],
                        'stats'):
                    network_data['mopub_app_stats'][app.key()].stats += \
                            stats
                else:
                    network_data['mopub_app_stats'][app.key()].stats = \
                            stats

                if 'mopub_stats' in network_data:
                    network_data['mopub_stats'] += stats
                else:
                    network_data['mopub_stats'] = stats

        if 'mopub_app_stats' in network_data:
            network_data['mopub_app_stats'] = sorted(network_data[
                'mopub_app_stats'].values(), key=lambda
                    app_data: app_data.identifier)
            for app in network_data['mopub_app_stats']:
                app.adunits = sorted(app.adunits, key=lambda adunit:
                        adunit.name)


        # Format graph stats
        from django.utils import simplejson

        graph_stats = []
        # Format mopub collected graph stats
        mopub_graph_stats = reduce(lambda x, y: x+y, stats_by_day.values(),
                StatsModel())

        daily_stats = sorted(stats_by_day.values(), key=lambda
                stats: stats.date)
        daily_stats = [s.to_dict() for s in daily_stats]


        mopub_graph_stats = mopub_graph_stats.to_dict()
        mopub_graph_stats['daily_stats'] = daily_stats
        mopub_graph_stats['name'] = "From MoPub"

        graph_stats.append(mopub_graph_stats)

        # Format network collected graph stats
        if network_data['reporting']:
            reporting_graph_stats = reduce(lambda x, y: x+y,
                    reporting_stats_by_day.values(), AdNetworkStats())

            daily_stats = sorted(reporting_stats_by_day.values(), key=lambda
                    stats: stats.date)
            daily_stats = [StatsModel(request_count=stats.attempts,
                impression_count=stats.impressions,
                click_count=stats.clicks).to_dict()
                for stats in daily_stats]



            reporting_graph_stats = StatsModel(request_count= \
                    reporting_graph_stats.attempts,
                    impression_count=reporting_graph_stats.impressions,
                    click_count=reporting_graph_stats.clicks).to_dict()
            reporting_graph_stats['daily_stats'] = daily_stats
            reporting_graph_stats['name'] = "From Networks"

            graph_stats.append(reporting_graph_stats)

        graph_stats = simplejson.dumps(graph_stats)


        # TODO: look for ways to make simpeler by getting stats keyed on
        # campaign
        campaign = CampaignQueryManager.get_network_campaign(self. \
                account.key(), network)
        network_data['active'] = campaign.active

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
                  'graph_stats' : graph_stats,
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

