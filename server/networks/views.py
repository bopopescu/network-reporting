import logging

from account.forms import AccountNetworkConfigForm, \
        AppNetworkConfigForm
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
from common.constants import NETWORKS, \
        REPORTING_NETWORKS, \
        NETWORKS_WITHOUT_REPORTING, \
        NETWORK_ADGROUP_TRANSLATION

from common.utils.date_magic import gen_last_days
from common.utils.decorators import staff_login_required
from common.ragendja.template import render_to_response, \
        render_to_string, \
        TextResponse, \
        JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils import sswriter

from advertiser.query_managers import AdvertiserQueryManager
from publisher.query_managers import AppQueryManager, \
        AdUnitContextQueryManager, \
        PublisherQueryManager
from networks.forms import NetworkCampaignForm, \
        NetworkAdGroupForm, \
        AdUnitAdGroupForm
from datetime import date, time
from django.contrib.auth.decorators import login_required
from django.forms import ModelForm
from django.http import HttpResponseRedirect, Http404
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

# Form imports
from publisher.query_managers import AdUnitQueryManager

DEFAULT_NETWORKS = set(['admob', 'iad', 'inmobi', 'jumptap', 'millennial'])

ADGROUP_FIELD_EXCLUSION_LIST = set(['account', 'campaign', 'net_creative',
        'site_keys', 'name', 'bid', 'bid_strategy', 'active', 'network_type'])

NETWORKS_WITH_PUB_IDS = set(['admob', 'brightroll', 'ejam', 'jumptap', \
        'millennial', 'mobfox', 'inmobi'])

DEFAULT_BID = 0.05

class NetworksHandler(RequestHandler):
    def get(self):
        """
        Create the index page for ad network reports for an account.
        Create a manager and get required stats for the webpage.
        Return a webpage with the list of stats in a table.
        """
        if not self.account.display_new_networks:
            return HttpResponseRedirect(reverse('network_index'))

        additional_networks_set = set(NETWORKS.keys())
        networks = []
        reporting = False

        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
                self.account).values()

        apps = PublisherQueryManager.get_objects_dict_for_account(
                self.account).values()

        for campaign in CampaignQueryManager.get_network_campaigns(
                self.account, is_new=True):
            network = str(campaign.network_type)

            # MoPub reported campaign cpm comes from meta data not stats so
            # we calculate it here instead of over ajax
            campaign_adgroups = filter_adgroups_for_campaign(campaign, adgroups)
            bid_range = get_bid_range(campaign_adgroups)
            network_data = {'name': network,
                            'pretty_name': campaign.name,
                            'active': campaign.active,
                            'key': campaign.key(),
                            'min_cpm': bid_range[0],
                            'max_cpm': bid_range[1],
                            }

            # If this campaign is the first campaign of this
            # network type and they have valid network
            # credentials, then we can mark this as a campaign
            # for which we have scraped network stats.
            if campaign.network_state == NetworkStates. \
                    DEFAULT_NETWORK_CAMPAIGN and network in \
                    REPORTING_NETWORKS:
                login = AdNetworkLoginManager.get_logins(self.account,
                        network).get()

                if login:
                    reporting = True
                    network_data['reporting'] = True

            adgroups_by_adunit = get_adgroups_by_adunit(campaign_adgroups)

            app_bids = []
            for app in apps:
                app_adgroups = filter_adgroups_for_app(app, adgroups_by_adunit)
                bid_range = get_bid_range(app_adgroups)
                app_bids.append({'min_cpm': bid_range[0],
                                 'max_cpm': bid_range[1]})
            network_data['apps'] = zip(apps, app_bids)
            network_data['apps'] = sorted(network_data['apps'], key=lambda
                    app_and_bid: app_and_bid[0].identifier)

            # Add this network to the list that goes in the page
            networks.append(network_data)

        # Sort networks alphabetically
        networks = sorted(networks, key=lambda network_data:
                network_data['pretty_name'])

        networks_to_setup = []
        if not networks:
            # Generate list of primary networks that can be setup. This is
            # shown only on initial setup
            for network in DEFAULT_NETWORKS:
                network_data = {}
                network_data['name'] = network
                network_data['pretty_name'] = NETWORKS[network]

                networks_to_setup.append(network_data)
                additional_networks_set.remove(network)

        networks_to_setup = sorted(networks_to_setup, key=lambda
                network_data: network_data['pretty_name'])

        additional_networks = []
        custom_networks = []
        # Generate list of additional networks that can be setup
        for network in additional_networks_set:
            network_data = {}
            network_data['name'] = network
            network_data['pretty_name'] = NETWORKS[network]

            if 'custom' in network:
                custom_networks.append(network_data)
            else:
                additional_networks.append(network_data)
        additional_networks += custom_networks

        additional_networks = sorted(additional_networks, key=lambda
                network_data: network_data['pretty_name'])

        apps = sorted(apps, key=lambda app: app.identifier)

        return render_to_response(self.request,
              'networks/index.html',
              {
                  'start_date': self.days[0],
                  'end_date': self.days[-1],
                  'date_range': self.date_range,
                  'days': self.days,
                  'graph': True if networks else False,
                  'networks': networks,
                  'networks_to_setup': networks_to_setup,
                  'additional_networks': additional_networks,
                  'apps': apps,
                  'reporting': reporting,
              })

@login_required
def networks(request, *args, **kwargs):
    return NetworksHandler()(request, *args, **kwargs)

class EditNetworkHandler(RequestHandler):
    def get(self, network='', campaign_key=''):
        """
        `network` - a network type
        `campaign_key` - the key for the campaign to be edited

        Pass in `network` if this campaign is being created for the first time,
        otherwise pass in `campaign_key` for the campaign that's being edited.
        """
        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            if not campaign or campaign.account.key() != self.account.key():
                raise Http404
            network = campaign.network_type
            campaign_name = campaign.name
            campaign_form = NetworkCampaignForm(instance=campaign)
            custom_campaign = campaign.network_state == \
                    NetworkStates.CUSTOM_NETWORK_CAMPAIGN
        else:
            # Do no other network campaigns exist or is this custom?
            custom_campaign = CampaignQueryManager.get_network_campaigns(
                    self.account, network).count(1) or 'custom' in network
            # Set the default campaign name to the network name
            campaign_name = NETWORKS[network]
            if custom_campaign and 'custom' not in network:
                campaign_name += ' - Custom'

            # set up the campaign with the default data
            campaign_form = NetworkCampaignForm({'name': campaign_name})

        network_data = {'name': network,
                        'pretty_name': campaign_name,
                        'show_login': False if campaign_key else True,
                        'login_state': LoginStates.NOT_SETUP}
        reporting = False

        # We don't make login forms for certain networks that we're unable
        # to scrape stats from.
        login_form = None

        # We try to find the login information if they have it. If login
        # is none by the time of the page rendering, it meas we don't have
        # login info for this account+network
        login = None
        if not custom_campaign and network in REPORTING_NETWORKS:
            # Create the login credentials form
            login = AdNetworkLoginManager.get_logins(self.account,
                    network).get()
            if login:
                # Can't initialize username or password because it's encrypted
                # and can only be decrypted on EC2
                login_form = LoginCredentialsForm(instance=login,
                        network=network)
                network_data['login_state'] = login.state
            else:
                login_form = LoginCredentialsForm(network=network)

        if network == 'jumptap':
            network_data['pub_id'] = getattr(self.account.network_config,
                    network + '_pub_id', '')

        apps = PublisherQueryManager.get_objects_dict_for_account(account=
                self.account).values()
        adgroup = None
        for app in apps:
            if network in NETWORKS_WITH_PUB_IDS:
                app.pub_id = getattr(app.network_config, network + '_pub_id',
                        '') or ''

            seven_day_stats = AdNetworkStats()

            # Populate network collected cpm for optimization
            fourteen_day_stats = AdNetworkStats()
            last_7_days = gen_last_days(omit=2)
            last_14_days = gen_last_days(date_range=14, omit=2)
            if login:
                reporting = True
                for mapper in AdNetworkMapperManager.get_mappers_for_app(
                        login, app):
                    seven_day_stats += AdNetworkStatsManager. \
                            get_stats_for_mapper_and_days(mapper,
                                    last_7_days)[0]
                    fourteen_day_stats += AdNetworkStatsManager. \
                            get_stats_for_mapper_and_days(mapper,
                                    last_14_days)[0]

            app.seven_day_stats = seven_day_stats
            app.fourteen_day_stats = fourteen_day_stats

            # Create different adgroup form for each adunit
            for adunit in app.adunits:
                adgroup = None
                if campaign_key:
                    # Get adgroup by key name
                    adgroup = AdGroupQueryManager.get_network_adgroup(
                            campaign, adunit.key(),
                            self.account.key(), True)

                adunit.adgroup_form = AdUnitAdGroupForm(instance=adgroup,
                        prefix=str(adunit.key()))
                adunit.adgroup_form.fields['bid'].widget.attrs['class'] += \
                        ' bid'

                if network in NETWORKS_WITH_PUB_IDS:
                    adunit_pub_id = getattr(adunit.network_config, network +
                            '_pub_id', False)
                    if adunit_pub_id != app.pub_id:
                        # only initialize th adunit level pub_id if it
                        # differs from the app level one
                        adunit.pub_id = adunit_pub_id

            # Sort adunits
            app.adunits = sorted(app.adunits, key=lambda adunit: adunit.name)

        # Create the default adgroup form
        adgroup_form = NetworkAdGroupForm(instance=adgroup)

        # Sort apps
        apps = sorted(apps, key=lambda app_data: app_data.identifier)

        return render_to_response(self.request,
                                  'networks/edit_network_form.html',
                                  {
                                      'network': network_data,
                                      'account_key': str(self.account.key()),
                                      'custom_campaign': custom_campaign,
                                      'campaign_form': campaign_form,
                                      'campaign_key': campaign_key,
                                      'REPORTING_NETWORKS': REPORTING_NETWORKS,
                                      'login_form': login_form,
                                      'adgroup_form': adgroup_form,
                                      'apps': apps,
                                      'reporting': reporting,
                                      'LoginStates': simplejson.dumps(
                                          LoginStates.__dict__),
                                      'NETWORKS_WITH_PUB_IDS': \
                                              NETWORKS_WITH_PUB_IDS,
                                  })

    def post(self,
            network='',
            campaign_key=''):
        if not self.request.is_ajax():
            raise Http404

        apps = PublisherQueryManager.get_apps_dict_for_account(account=
                self.account).values()
        adunits = PublisherQueryManager.get_adunits_dict_for_account(account=
                self.account).values()

        query_dict = self.request.POST.copy()
        query_dict['campaign_type'] = 'network'

        campaign = None
        custom_campaign = False
        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            if not campaign or campaign.account.key() != self.account.key():
                raise Http404

            network = campaign.network_type
            custom_campaign = campaign.network_state == \
                    NetworkStates.CUSTOM_NETWORK_CAMPAIGN
            if campaign:
                if not custom_campaign:
                    query_dict['name'] = campaign.name
        else:
            # Do no other network campaigns exist or is this custom?
            custom_campaign = CampaignQueryManager.get_network_campaigns(
                    self.account, network).count(1) or 'custom' in network
            if not custom_campaign:
                query_dict['name'] = NETWORKS[network]
                campaign = CampaignQueryManager. \
                        get_default_network_campaign(self.account, network)

        campaign_form = NetworkCampaignForm(query_dict, instance=campaign)

        adunit_keys = [(unicode(adunit.key())) for adunit in adunits]

        if campaign_form.is_valid():
            logging.info('campaign form is valid')
            campaign = campaign_form.save(commit=False)
            if custom_campaign:
                campaign.network_state = NetworkStates.CUSTOM_NETWORK_CAMPAIGN
            else:
                campaign.network_state = NetworkStates.DEFAULT_NETWORK_CAMPAIGN
            campaign.account = self.account
            campaign.network_type = network
            campaign.campaign_type = 'network'

            adgroup_form = NetworkAdGroupForm(query_dict)

            if adgroup_form.is_valid():
                logging.info("default adgroup form is valid")
                default_adgroup = adgroup_form.save(commit=False)

                adgroup_forms_are_valid = True
                network_config_field = "%s_pub_id" % network
                adgroup_forms = []
                for adunit in adunits:
                    adgroup_form = AdUnitAdGroupForm(query_dict,
                            prefix=str(adunit.key()))
                    if not adgroup_form.is_valid():
                        adgroup_forms_are_valid = False
                        break

                    pub_id = self.request.POST.get("adunit_%s-%s" %
                            (adunit.key(), network_config_field), '')
                    # Return error if adgroup is set to active yet
                    # the user didn't enter a pub id
                    if not pub_id and self.request.POST.get('%s-active' %
                            adunit.key(), False) and network in \
                                    NETWORKS_WITH_PUB_IDS:
                        return JSONResponse({
                            'errors': {'adunit_' + str(adunit.key()) + \
                                '-' + network + '_pub_id': "MoPub requires an" \
                                " ad network id for enabled adunits."},
                            'success': False,
                        })

                    adgroup_forms.append((adgroup_form, adunit.key()))
            else:
                adgroup_forms_are_valid = False

            adgroups = []
            if adgroup_forms_are_valid:
                logging.info('adgroup forms are valid')

                CampaignQueryManager.put(campaign)

                for adgroup_form, adunit_key in adgroup_forms:
                    adgroup = AdGroupQueryManager.get_network_adgroup(
                            campaign, adunit_key, self.account.key())

                    # copy fields from the default adgroup
                    for field in default_adgroup.properties().iterkeys():
                        if field not in ADGROUP_FIELD_EXCLUSION_LIST:
                            setattr(adgroup, field, getattr(default_adgroup,
                                field))

                    tmp_adgroup = adgroup_form.save(commit=False)
                    # copy fields from the form for this adgroup
                    for field in AdUnitAdGroupForm.base_fields.iterkeys():
                        if field not in ('custom_html', 'custom_method'):
                            setattr(adgroup, field, getattr(tmp_adgroup, field))

                    if network in NETWORK_ADGROUP_TRANSLATION:
                        adgroup.network_type = NETWORK_ADGROUP_TRANSLATION[
                                network]
                    else:
                        adgroup.network_type = network

                    html_data = None
                    if adgroup.network_type == 'custom':
                        html_data = self.request.POST.get(str(adunit_key) + \
                                '-custom_html', '')
                    elif adgroup.network_type == 'custom_native':
                        html_data = self.request.POST.get(str(adunit_key) + \
                                '-custom_method', '')
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
                    CreativeQueryManager.put(creative)
                    # set adgroup to reference the correct creative
                    adgroup.net_creative = creative.key()

                    AdGroupQueryManager.put(adgroup)
                    adgroups.append(adgroup)

                # NetworkConfig for Apps
                if network in NETWORKS_WITH_PUB_IDS:
                    for app in apps:
                        network_config = app.network_config or NetworkConfig()
                        app_pub_id = self.request.POST.get("app_%s-%s" %
                                (app.key(), network_config_field), '')
                        setattr(network_config, network_config_field,
                                app_pub_id)
                        AppQueryManager.update_config_and_put(app,
                                network_config)

                        if network in REPORTING_NETWORKS:
                            # Create an AdNetworkAppMapper if there exists a
                            # login for the network (safe to re-create if it
                            # already exists)
                            login = AdNetworkLoginManager.get_logins(
                                    self.account, network).get()
                            mappers = AdNetworkMapperManager. \
                                    get_mappers_for_app(login=login, app=app)
                            # Delete the existing mappers if there are no scrape
                            # stats for them.
                            for mapper in mappers:
                                if mapper:
                                    stats = mapper.ad_network_stats
                                    if not stats.count(1):
                                        mapper.delete()
                            if app_pub_id:
                                AdNetworkMapperManager.create(network=network,
                                        pub_id=app_pub_id, login=login,
                                        app=app)

                    # NetworkConfig for AdUnits
                    if network in NETWORKS_WITH_PUB_IDS:
                        for adgroup, adunit in zip(adgroups, adunits):
                            network_config = adunit.network_config or \
                                    NetworkConfig()
                            pub_id = self.request.POST.get("adunit_%s-%s" %
                                    (adunit.key(), network_config_field), '')

                            setattr(network_config, network_config_field,
                                    pub_id)
                            AdUnitQueryManager.update_config_and_put(adunit,
                                    network_config)

                        # NetworkConfig for Account
                        if network == 'jumptap':
                            network_config = self.account.network_config or \
                                    NetworkConfig()
                            setattr(network_config, network_config_field, \
                                    self.request.POST.get(network +
                                        '_pub_id', ''))
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
                    if adgroup_form.prefix and key in set(AdUnitAdGroupForm.
                            base_fields.keys()):
                        key = adgroup_form.prefix + '-' + key
                    errors[key] = ' '.join([error for error in value])
        else:
            errors = {}
            for key, value in campaign_form.errors.items():
                errors[key] = ' '.join([error for error in value])

        return JSONResponse({
            'errors': errors,
            'success': False,
        })

@login_required
def edit_network(request, *args, **kwargs):
    return EditNetworkHandler()(request, *args, **kwargs)

class NetworkDetailsHandler(RequestHandler):
    def get(self, campaign_key):
        """
        Return a webpage with the network statistics.
        """
        campaign = CampaignQueryManager.get(campaign_key)

        if not campaign or campaign.account.key() != self.account.key():
            raise Http404

        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
                self.account).values()

        # MoPub reported campaign cpm comes from meta data not stats so
        # we calculate it here instead of over ajax
        campaign_adgroups = filter_adgroups_for_campaign(campaign, adgroups)
        bid_range = get_bid_range(campaign_adgroups)

        network = campaign.network_type
        network_data = {'name': network,
                        'pretty_name': campaign.name,
                        'key': str(campaign.key()),
                        'active': campaign.active,
                        'login_state': LoginStates.NOT_SETUP,
                        'reporting': False,
                        'targeting': [],
                        'min_cpm': bid_range[0],
                        'max_cpm': bid_range[1],}

        # Get the campaign targeting information.  We need an adunit
        # and an adgroup to determine targeting.  Any adunit will do
        # because every adunit is targeted by a network adgroup.
        adunit = AdUnitQueryManager.get_adunits(account=self.account,
                limit=1)[0]
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                adunit.key(), self.account.key(), get_from_db=True)
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

        # This campaign is a default network campaign if its the
        # only one of this type. If this is the default, and if we have
        # login info, then we have reporting stats.
        #REFACTOR: handle the case when this isnt true.
        if campaign.network_state == NetworkStates. \
                DEFAULT_NETWORK_CAMPAIGN:
            login = AdNetworkLoginManager.get_logins(self.account, network). \
                    get()
            if login:
                network_data['login_state'] = login.state
                network_data['reporting'] = True

        apps = PublisherQueryManager.get_objects_dict_for_account(
                self.account).values()


        adgroups_by_adunit = get_adgroups_by_adunit(campaign_adgroups)

        app_bids = []
        for app in apps:
            app_adgroups = filter_adgroups_for_app(app, adgroups_by_adunit)
            bid_range = get_bid_range(app_adgroups)
            app_bids.append({'min_cpm': bid_range[0],
                             'max_cpm': bid_range[1]})

        network_data['apps'] = zip(apps, app_bids)
        network_data['apps'] = sorted(network_data['apps'], key=lambda
                app_and_bid: app_and_bid[0].identifier)

        # set adunit cpms to corresponding adgroup bids
        for app in apps:
            for adunit in app.adunits:
                if str(adunit.key()) in adgroups_by_adunit:
                    adgroup = adgroups_by_adunit[str(adunit.key())]
                    adunit.cpm = adgroup.bid
                    adunit.active = adgroup.active

        apps = sorted(apps, key=lambda app: app.identifier)

        return render_to_response(self.request,
              'networks/details.html',
              {
                  'start_date' : self.days[0],
                  'end_date' : self.days[-1],
                  'date_range' : self.date_range,
                  'graph' : True,
                  'reporting' : network_data['reporting'],
                  'network': network_data,
                  'apps': apps,
                  'LoginStates': LoginStates,
              })

@login_required
def network_details(request, *args, **kwargs):
    return NetworkDetailsHandler()(request, *args, **kwargs)

class PauseNetworkHandler(RequestHandler):
    def post(self):
        """
        Pause / un-pause campaign
        """
        if not self.request.is_ajax():
            raise Http404

        campaign_key = self.request.POST.get('campaign_key')

        # Pause campaign
        campaign = CampaignQueryManager.get(campaign_key)

        if not campaign or campaign.account.key() != self.account.key():
            raise Http404

        campaign.active = True if self.request.POST.get('active') else False
        CampaignQueryManager.put(campaign)

        return TextResponse()

@login_required
def pause_network(request, *args, **kwargs):
    return PauseNetworkHandler()(request, *args, **kwargs)

class DeleteNetworkHandler(RequestHandler):
    def post(self):
        """
        Change campaign and login credentials deleted field to True and
        redirect to the networks index page
        """
        if not self.request.is_ajax():
            raise Http404

        campaign_key = self.request.POST.get('campaign_key')

        campaign = CampaignQueryManager.get(campaign_key)

        if not campaign or campaign.account.key() != self.account.key():
            raise Http404

        campaign.deleted = True
        CampaignQueryManager.put(campaign)

        if campaign.network_state == NetworkStates. \
                DEFAULT_NETWORK_CAMPAIGN:
            # If other campaigns exist, a new default campaign must be chosen
            default_campaign = CampaignQueryManager.get_network_campaigns(
                    self.account, network_type=campaign.network_type).get()

            if default_campaign:
                default_campaign.network_state = NetworkStates. \
                        DEFAULT_NETWORK_CAMPAIGN
                default_campaign.name = NETWORKS[default_campaign.network_type]
                CampaignQueryManager.put(default_campaign)
            elif campaign.network_type in REPORTING_NETWORKS:
                login = AdNetworkLoginManager.get_logins(self.account,
                        campaign.network_type).get()
                if login:
                    login.deleted = True
                    login.put()

        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        # Mark all adgroups as deleted
        for adunit in adunits:
            adgroup = AdGroupQueryManager.get_network_adgroup(
                    campaign, adunit.key(),
                    self.account.key(), True)
            adgroup.deleted = True
            AdGroupQueryManager.put(adgroup)

        return TextResponse()

@login_required
def delete_network(request, *args, **kwargs):
    return DeleteNetworkHandler()(request, *args, **kwargs)

## Helpers
#
def get_bid_range(adgroups):
    adgroup_bids = [adgroup.bid for adgroup in adgroups if adgroup.active]

    min_cpm = None
    max_cpm = None
    if adgroup_bids:
        min_cpm = min(adgroup_bids)
        max_cpm = max(adgroup_bids)

    return (min_cpm, max_cpm)

def get_adgroups_by_adunit(adgroups):
    """
    Return a dict of adgroups keyed by adunit

    Network adgroups have one adunit.
    """
    adgroups_by_adunit = {}
    for adgroup in adgroups:
        if adgroup.site_keys:
            adgroups_by_adunit[str(adgroup.site_keys[0])] = adgroup

    return adgroups_by_adunit


def filter_adgroups_for_app(app, adgroups_by_adunit):
    """
    Return list of adgroups for the given app.

    Network adgroups have one adunit.
    """
    return [adgroups_by_adunit[str(adunit.key())] for adunit in
            app.adunits if str(adunit.key()) in adgroups_by_adunit]

def filter_adgroups_for_campaign(campaign, adgroups):
    """
    Filter adgroups by campaign
    """
    return [adgroup for adgroup in adgroups if adgroup._campaign ==
            campaign.key()]

