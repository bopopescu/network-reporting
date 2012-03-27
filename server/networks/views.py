import logging

from account.forms import AccountNetworkConfigForm, \
        AppNetworkConfigForm, \
        AdUnitNetworkConfigForm
from account.query_managers import AccountQueryManager
from account.models import NetworkConfig

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

from common.utils.date_magic import gen_days_for_range, \
        gen_last_days
from common.utils.decorators import staff_login_required
from common.ragendja.template import render_to_response, \
        render_to_string, \
        TextResponse, \
        JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter

from publisher.query_managers import AppQueryManager, \
        AdUnitContextQueryManager, \
        ALL_NETWORKS

from datetime import datetime, date, timedelta, time
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.utils import simplejson
from django.shortcuts import redirect
from django.core.urlresolvers import reverse

from google.appengine.ext import db

# Imports for getting mongo stats
from advertiser.query_managers import AdGroupQueryManager, \
        CampaignQueryManager, \
        CreativeQueryManager
from advertiser.models import NetworkStates
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

# Form imports
from advertiser.forms import CampaignForm, AdGroupForm
from publisher.query_managers import AdUnitQueryManager

import copy

OTHER_NETWORKS = {'mobfox': 'MobFox',
                  'millennial': 'Millennial',
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
        campaigns_data = []
        reporting = False

        for campaign in CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True):
            network = str(campaign.network_type)

            network_data = {}
            if campaign:
                campaign_data = {'id': str(campaign.key()),
                                 'network': network}

                if campaign.network_state == NetworkStates.DEFAULT_NETWORK_CAMPAIGN \
                        and network in REPORTING_NETWORKS:
                    login = AdNetworkLoginManager.get_login(self.account,
                            network).get()

                    if login:
                        reporting = True
                        campaign_data['reporting'] = True
                        network_data['reporting'] = True

                network_data['name'] = network
                network_data['pretty_name'] = campaign.name
                network_data['campaign_key'] = campaign.key()

                networks_to_setup -= set([network])
                additional_networks.add(network)

                networks.append(network_data)
                campaigns_data.append(campaign_data)

        # Sort networks alphabetically
        networks = sorted(networks, key=lambda network_data:
                network_data['name'])

        networks_to_setup_ = []
        # Generate list of main networks that can be setup
        for network in sorted(networks_to_setup):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = get_pretty_name(network)

            networks_to_setup_.append(network_data)

        additional_networks_ = []
        # Generate list of main networks that can be setup
        for network in sorted(additional_networks):
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = get_pretty_name(network)

            additional_networks_.append(network_data)


        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/index.html',
              {
                  'start_date': days[0],
                  'end_date': days[-1],
                  'date_range': self.date_range,
                  'graph': True if networks else False,
                  'networks': networks,
                  'networks_to_setup': networks_to_setup_,
                  'additional_networks': additional_networks_,
                  'reporting': reporting,
                  'campaigns_data': simplejson.dumps(campaigns_data),
                  'MOBFOX': MOBFOX,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

class EditNetworkHandler(RequestHandler):
    def get(self,
            network='',
            campaign_key=''):
        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            network = campaign.network_type
            campaign_name = campaign.name
            campaign_form = CampaignForm(instance=campaign)
            custom_campaign = campaign.network_state == \
                    NetworkStates.CUSTOM_NETWORK_CAMPAIGN
        else:
            # Do no other network campaigns exist?
            custom_campaign = CampaignQueryManager.get_network_campaigns(
                    self.account, network).count(limit=1)
            # Set the default campaign name to the network name
            campaign_name = get_pretty_name(network)
            if custom_campaign:
                campaign_name += ' - Custom'
            default_data = {'name': campaign_name}
            campaign_form = CampaignForm(default_data)

        network_data = {}
        network_data['name'] = network
        network_data['pretty_name'] = campaign_name
        reporting = False

        login_form = None
        login = None
        if not custom_campaign:
            # Create the login credentials form
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()
            if login:
                # Can't initialize username or password because it's encrypted and
                # can only be decrypted on EC2
                login_form = LoginCredentialsForm(instance=login)
            else:
                login_form = LoginCredentialsForm()

        account_network_config_form = AccountNetworkConfigForm(instance=
                self.account.network_config)

        reporting_networks = ' '.join(REPORTING_NETWORKS.keys()) + \
                ' admob_native'

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        adgroup = None
        for app in apps:
            app.network_config_form = AppNetworkConfigForm(instance= \
                    app.network_config, prefix="app_%s" % app.key())
            app.pub_id = app.network_config_form.fields.get(network + '_pub_id',
                    False)


            seven_day_stats = AdNetworkStats()

            fourteen_day_stats = AdNetworkStats()
            last_7_days = gen_last_days(omit=1)
            last_14_days = gen_last_days(date_range=14, omit=1)
            if login:
                reporting = True
                for mapper in AdNetworkMapperManager.get_mappers_for_app(
                        login, app):
                    seven_day_stats += AdNetworkStatsManager. \
                            get_stats_for_mapper_and_days(mapper, last_7_days)[0]
                    fourteen_day_stats += AdNetworkStatsManager. \
                            get_stats_for_mapper_and_days(mapper, last_14_days)[0]

            app.seven_day_stats = seven_day_stats
            app.fourteen_day_stats = fourteen_day_stats

            # Create different adgroup form for each adunit
            app.adunits = []
            for adunit in app.all_adunits:
                adgroup = None
                if campaign_key:
                    adgroup = AdGroupQueryManager.get_network_adgroup(
                            campaign.key(), adunit.key(),
                            self.account.key(), network, True)
                adunit.adgroup_form = AdGroupForm(is_staff=
                        self.request.user.is_staff, instance=adgroup,
                        prefix=str(adunit.key()))
                # Add class based on app that adunit is under
                adunit.adgroup_form.fields['active'].widget.attrs['class'] = \
                        str(app.key()) + '-adunit'
                adunit.adgroup_form.fields['bid'].widget.attrs['class'] += \
                        ' ' + str(app.key()) + '-cpm-field bid'

                adunit.network_config_form = AdUnitNetworkConfigForm(
                        instance=adunit.network_config, prefix="adunit_%s" %
                        adunit.key())
                adunit.pub_id = adunit.network_config_form.fields.get(network +
                        '_pub_id', False)
                app.adunits.append(adunit)

        # Create the default adgroup form
        adgroup_form = AdGroupForm(is_staff=self.request.user.is_staff,
                instance=adgroup)

        return render_to_response(self.request,
                                  'networks/edit_network_form.html',
                                  {
                                      'account_key': str(self.account.key()),
                                      'network': network_data,
                                      'custom_campaign': custom_campaign,
                                      'campaign_form': campaign_form,
                                      'campaign_key': campaign_key,
                                      'REPORTING_NETWORKS': REPORTING_NETWORKS,
                                      'reporting_networks': reporting_networks,
                                      'login_form': login_form,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form':
                                            account_network_config_form,
                                      'apps': apps,
                                      'reporting': reporting,
                                  })

    def post(self,
            network='',
            campaign_key=''):
        if not self.request.is_ajax():
            raise Http404

        apps = AppQueryManager.get_apps(account=self.account)
        adunits = AdUnitQueryManager.get_adunits(account=self.account)

        query_dict = self.request.POST.copy()
        query_dict['campaign_type'] = 'network'

        campaign = None
        custom_campaign = False
        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            network = campaign.network_type
            custom_campaign = campaign.network_state == \
                    NetworkStates.CUSTOM_NETWORK_CAMPAIGN
            if campaign:
                if not custom_campaign:
                    query_dict['name'] = campaign.name
                campaign_form = CampaignForm(query_dict, instance=campaign)
        else:
            # Do no other network campaigns exist?
            custom_campaign = CampaignQueryManager.get_network_campaigns(self.account,
                    network).count(limit=1)
            campaign_form = CampaignForm(query_dict)

        adunit_keys = [(unicode(adunit.key())) for adunit in adunits]

        if campaign_form.is_valid():
            logging.info('campaign form is valid')
            campaign = campaign_form.save()
            if custom_campaign:
                campaign.network_state = NetworkStates.CUSTOM_NETWORK_CAMPAIGN
            else:
                campaign.network_state = NetworkStates.DEFAULT_NETWORK_CAMPAIGN
            campaign.account = self.account
            #TODO: convert to valid network type
            campaign.network_type = network

            # Get a set of the AdGroupForm field names
            fields = set(AdGroupForm.base_fields.keys())
            # Copy default form fields to all adgroup adunit forms
            for key, val in query_dict.iteritems():
                if key in fields:
                    for adunit in adunits:
                        if str(adunit.key()) + '-' + key not in query_dict:
                            query_dict[str(adunit.key()) + '-' + key] = val

            adgroup_forms_are_valid = True
            adgroup_forms = []
            for adunit in adunits:
                network_adgroup = AdGroupQueryManager.get_network_adgroup(
                        campaign.key(), adunit.key(), self.account.key(), network)

                query_dict[str(adunit.key()) + '-name'] = network_adgroup.name

                adgroup_form = AdGroupForm(query_dict,
                        site_keys=[(unicode(adunit.key()))],
                        is_staff=self.request.user.is_staff,
                        prefix=str(adunit.key()),
                        instance=network_adgroup)
                if not adgroup_form.is_valid():
                    adgroup_forms_are_valid = False
                    break
                adgroup_forms.append(adgroup_form)

            if adgroup_forms_are_valid:
                logging.info('adgroup forms are valid')

                # And then put in datastore again.
                CampaignQueryManager.put(campaign)

                for adgroup_form in adgroup_forms:
                    adgroup = adgroup_form.save()
                    adgroup.campaign = campaign
                    adgroup.network_type = network

                    html_data = None
                    if adgroup.network_type == 'custom':
                        html_data = self.request.POST.get('custom_html', '')
                    elif adgroup.network_type == 'custom_native':
                        html_data = self.request.POST.get('custom_method', '')
                    # build default creative with custom_html data if custom or
                    # none if anything else
                    creative = adgroup.default_creative(html_data)
                    if adgroup.net_creative and creative.__class__ == \
                            adgroup.net_creative.__class__:
                        # if the adgroup has a creative AND the new creative and
                        # old creative are the same class,
                        # ignore the new creative and set the variable to point
                        # to the old one
                        creative = adgroup.net_creative
                        if adgroup.network_type == 'custom':
                            # if the network is a custom one, the creative
                            # might be the same, but the data might be new, set
                            # the old creative to have the (possibly) new data
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
                    # TODO: must there be a seperate creative for each adunit /
                    # adgroup?
                    # CreativeQueryManager.put(creative)
                    # set adgroup to reference the correct creative
                    # adgroup.net_creative = creative.key()

                    AdGroupQueryManager.put(adgroup)

                # TODO: resolve admob / admob native
                # NetworkConfig for Apps
                if network in ('admob', 'brightroll', 'ejam', 'inmobi',
                        'jumptap', 'millennial_native', 'mobfox'):
                    # get rid of _native in admob_native, millennial_native
                    network_config_field = "%s_pub_id" % network. \
                            replace('_native', '')

                    for app in apps:
                        network_config = app.network_config or NetworkConfig()
                        setattr(network_config, network_config_field,
                                self.request.POST.get("app_%s-%s" %
                                    (app.key(), network_config_field), ''))
                        AppQueryManager.update_config_and_put(app,
                                network_config)

                    # TODO: resolve admob / admob native
                    # NetworkConfig for AdUnits
                    if network in ('admob', 'admob_native', 'jumptap',
                            'millennial_native'):
                        for adunit in adunits:
                            network_config = adunit.network_config or \
                                    NetworkConfig()
                            setattr(network_config, network_config_field,
                                    self.request.POST.get("adunit_%s-%s" %
                                        (adunit.key(), network_config_field), ''))
                            AdUnitQueryManager.update_config_and_put(adunit,
                                    network_config)

                        # NetworkConfig for Account
                        if network == 'jumptap':
                            network_config = self.account.network_config or \
                                    NetworkConfig()
                            setattr(network_config, network_config_field, \
                                    self.request.POST.get('account_pub_id', ''))
                            AccountQueryManager.update_config_and_put( \
                                    self.account, network_config)

                # Delete Cache. We leave this in views.py because we
                # must delete the adunits that the adgroups used to have as well
                if adunit_keys:
                    adunits = AdUnitQueryManager.get(adunit_keys)
                    AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

                # Onboarding: user is done after they set up their first
                # campaign
                if self.account.status == "step4":
                    self.account.status = ""
                    AccountQueryManager.put_accounts(self.account)


                return JSONResponse({
                    'success': True,
                    'redirect': reverse('network_details',
                        args=(str(campaign.key()),)),
                })
            else:
                errors = {}
                for key, value in adgroup_form.errors.items():
                    if key in set(['bid', 'active']):
                        key = adgroup_form.prefix + '-' + key
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
            campaign_key):
        """
        Return a webpage with the network statistics.
        """
        campaign = CampaignQueryManager.get(campaign_key)
        network = campaign.network_type
        network_data = {}
        network_data['name'] = network
        network_data['pretty_name'] = campaign.name

        if not campaign:
            raise Http404

        network_data['campaign_key'] = str(campaign.key())
        network_data['active'] = campaign.active
        network_data['targeting'] = []

        # Set targeting
        adunit = AdUnitQueryManager.get_adunits(account=self.account,
                limit=1)[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign.key(),
                adunit.key(), self.account.key(), network, get_from_db=True)
        if adgroup.device_targeting:
            for device, pretty_name in adgroup.DEVICE_CHOICES:
                if getattr(adgroup, 'target_' + device, False):
                    network_data['targeting'].append(pretty_name)
            if adgroup.target_other:
                network_data['targeting'].append('Other')

        if network_data['targeting']:
            network_data['targeting'] = ', '.join(network_data['targeting'])
        else:
            network_data['targeting'] = 'All'

        campaign_data = {'id': str(campaign.key()),
                         'network': network,
                         'reporting': False}

        if campaign.network_state == NetworkStates. \
                DEFAULT_NETWORK_CAMPAIGN:
            if AdNetworkLoginManager.get_login(self.account,
                    network).get():
                campaign_data['reporting'] = True

        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate the stats for network_data
        for app in AppQueryManager.get_apps(self.account):
            if 'mopub_app_stats' not in network_data:
                network_data['mopub_app_stats'] = {}
            if app.key() not in network_data['mopub_app_stats']:
                network_data['mopub_app_stats'][app.key()] = app

        if 'mopub_app_stats' in network_data:
            network_data['mopub_app_stats'] = sorted(network_data[
                'mopub_app_stats'].values(), key=lambda
                    app_data: app_data.identifier)


        # Aggregate stats (rolled up stats at the app and network level for the
        # account), daily stats needed for the graph and stats for each mapper
        # for the account all get loaded via Ajax.
        return render_to_response(self.request,
              'networks/details.html',
              {
                  'start_date' : self.days[0],
                  'end_date' : self.days[-1],
                  'date_range' : self.date_range,
                  'graph' : True,
                  'reporting' : campaign_data['reporting'],
                  'network': network_data,
                  'campaign_data': simplejson.dumps(campaign_data),
                  'ADMOB': ADMOB,
                  'IAD': IAD,
                  'INMOBI': INMOBI,
                  'MOBFOX': MOBFOX,
                  'REPORTING_NETWORKS': REPORTING_NETWORKS,
              })

@login_required
def network_details(request, *args, **kwargs):
    return NetworkDetailsHandler()(request, *args, **kwargs)

## Helpers
#
def get_pretty_name(network):
    return REPORTING_NETWORKS.get(network, False) or \
            OTHER_NETWORKS.get(network, False) or 'Custom'

