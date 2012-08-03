import logging

from account.forms import AccountNetworkConfigForm, \
        AppNetworkConfigForm
from account.query_managers import AccountQueryManager, \
        NetworkConfigQueryManager
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
        HttpResponse, \
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
from collections import defaultdict
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
from reporting.query_managers import StatsModelQueryManager

# Form imports
from publisher.query_managers import AdUnitQueryManager

from common.utils import tablib

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

        # Once memcache is fixed consider which approach is faster
#        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
#                self.account).values()

        apps = PublisherQueryManager.get_objects_dict_for_account(
                self.account).values()

        campaigns = CampaignQueryManager.get_network_campaigns(self.account,
                is_new=True)

        for campaign in campaigns:
            network = str(campaign.network_type)

            # MoPub reported campaign cpm comes from meta data not stats so
            # we calculate it here instead of over ajax
            #campaign_adgroups = filter_adgroups_for_campaign(campaign, adgroups)
            # Get adgroup by key name
            campaign_adgroups = AdGroupQueryManager.get([AdGroupQueryManager.
                get_network_adgroup(campaign, adunit.key(),
                    self.account.key()).key() for app in apps for
                    adunit in app.adunits])
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

            # TODO: determine which is faster? get by key or memcache
            #adgroups_by_adunit = get_adgroups_by_adunit(campaign_adgroups)

            app_bids = []
            index = 0
            for app in apps:
                app_adgroups = []
                for adunit in app.adunits:
                    # TODO: put bids in app?
                    adunit.adgroup = campaign_adgroups[index]
                    app_adgroups.append(adunit.adgroup)
                    index += 1
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

        display_message = self.account.display_networks_message
        if display_message:
            self.account.display_networks_message = False
            AccountQueryManager.put(self.account)

        return render_to_response(self.request,
              'networks/index.html',
              {
                  'start_date': self.days[0],
                  'end_date': self.days[-1],
                  'date_range': self.date_range,
                  'days': self.days,
                  'display_message': display_message,
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
                    self.account, network) or 'custom' in network
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
                        network=network, prefix=network)
                network_data['login_state'] = login.state
            else:
                login_form = LoginCredentialsForm(network=network,
                        prefix=network)

        network_configs_dict = NetworkConfigQueryManager. \
                get_network_configs_dict_for_account(self.account)
        if network == 'jumptap':
            if str(self.account._network_config) in network_configs_dict:
                self.account.network_config = network_configs_dict[str(
                    self.account._network_config)]
            network_data['pub_id'] = getattr(self.account.network_config,
                    network + '_pub_id', '')

        apps = PublisherQueryManager.get_objects_dict_for_account(account=
                self.account).values()
        adgroup = None
        for app in apps:
            if network in NETWORKS_WITH_PUB_IDS:
                if str(app._network_config) in network_configs_dict:
                    app.network_config = network_configs_dict[
                            str(app._network_config)]

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
                    if str(adunit._network_config) in network_configs_dict:
                        adunit.network_config = network_configs_dict[
                                str(adunit._network_config)]

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
                                      'account': self.account,
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

    def post(self, network='', campaign_key=''):
        """Create or edit a network campaign.

        Args:
            network: a base network name, must be in NETWORKS, used to create new network campaigns
            or
            campaign_key: the campaign_key for the campaign being edited, used to edit existing network campaigns

        Return:
            JSONResponse dict with either errors or success and a redirect url

        Author:
            Tiago Bandeira (7/17/2012)
        """
        if not self.request.is_ajax():
            raise Http404

        if network:
            return self.create(network)
        elif campaign_key:
            return self.edit(campaign_key)

    def edit(self, campaign_key):
        """Edit a network campaign.

        Args:
            campaign_key: the campaign_key for the campaign being edited, used to edit existing network campaigns

        Return:
            JSONResponse dict with either errors or success and a redirect url

        Author:
            Tiago Bandeira (7/17/2012)
        """
        campaign = CampaignQueryManager.get(campaign_key)

        if not campaign or campaign.account.key() != self.account.key():
            raise Http404

        campaign_fields = {}
        network_adgroup_fields = {}
        # adunit_adgroup_fields represents the adgroups that get updated based on the POST data
        adunit_adgroup_fields = defaultdict(dict)
        # pub_id_fields represents the network_configs that get updated based on the POST data
        pub_id_fields = defaultdict(dict)

        # split the QueryDict into sets of fields (campaign_fields,
        # network_adgroup_fields, adunit_adgroup_fields, pub_id_fields),
        # which are then processed in order
        for base_field, value in self.request.POST.iterlists():
            # parse field into model key and field by looking for '-'
            key_field = base_field.rsplit('-', 1)
            if len(key_field) == 1:
                key = None
                field = key_field[0]
            else:
                key = key_field[0]
                field = key_field[1]

            if len(value) == 1:
                value = value[0]

            if field in NetworkCampaignForm.base_fields:
                campaign_fields[base_field] = value
            elif field in NetworkAdGroupForm.base_fields:
                network_adgroup_fields[base_field] = value
            elif field in AdUnitAdGroupForm.base_fields:
                adunit_adgroup_fields[key][field] = value
            elif 'pub_id' in field:
                pub_id_fields[key][field] = value

        errors = {}

        campaign_form = None
        if campaign_fields:
            campaign_form = self.generate_campaign_form(campaign_fields, errors, campaign)

        network_adgroup_form = None
        if network_adgroup_fields:
            network_adgroup_form = self.generate_network_adgroup_form(network_adgroup_fields, errors, campaign)

        adunit_key_adgroup_form_dict = {}
        if adunit_adgroup_fields:
            adunit_key_adgroup_form_dict = self.generate_adunit_key_adgroup_form_dict(adunit_adgroup_fields, errors, campaign)

        # if errors exist return them to the page
        if errors:
            logging.info('errors: %s' % errors)
            return JSONResponse({
                'errors': errors,
                'success': False,
            })

        if pub_id_fields:
            self.update_network_configs_and_create_mappers(pub_id_fields, campaign.network_type)

        if campaign_form:
            # save the campaign changes
            campaign_form.save()

        adgroups = []
        if network_adgroup_form:
            # get all adunits
            adunits = PublisherQueryManager.get_adunits_dict_for_account(account=
                    self.account).values()
            # apply changes to all adunit adgroups that haven't been
            # individually modified
            for adunit in adunits:
                if str(adunit.key()) not in adunit_key_adgroup_form_dict:
                    adgroup = AdGroupQueryManager.get_network_adgroup(campaign, adunit.key(), self.account.key(), get_from_db=True)
                    adgroup = NetworkAdGroupForm(network_adgroup_fields, instance=adgroup).save(commit=False)
                    adgroups.append(adgroup)

        creatives = []
        for key, adgroup_form in adunit_key_adgroup_form_dict.iteritems():
            adgroup = adgroup_form.save(commit=False)

            # apply global changes
            if network_adgroup_form:
                for field, value in network_adgroup_form.cleaned_data.iteritems():
                    setattr(adgroup, field, value)
            adgroups.append(adgroup)

            # special case custom and custom native networks
            #
            # NOTE: There should only be one creative per adgroup but for some
            # adgroups there are multiple creatives which isn't correct but we
            # can't delete them because mongo stats relies on it in order to
            # work. 'for creative in adgroup.creatives' is a hack to make sure
            # the custom_html gets copied over the right creative if some of
            # the creatives are marked as deleted and one isn't (how the data
            # should be if it's not one-to-one). The data most likely became
            # corrupted durring one or more migration scripts being run.
            if campaign.network_type == 'custom' and key + '-custom_html' in self.request.POST:
                for creative in adgroup.creatives:
                    creative.html_data = adgroup_form.cleaned_data['custom_html']
                    creatives.append(creative)
            elif campaign.network_type == 'custom_native' and key + '-custom_method' in self.request.POST:
                for creative in adgroup.creatives:
                    creative.html_data = adgroup_form.cleaned_data['custom_method']
                    creatives.append(creative)

        # save all modified adgroups
        AdGroupQueryManager.put(adgroups)

        # save all modified creatives
        CreativeQueryManager.put(creatives)

        return JSONResponse({
            'success': True,
            'redirect': reverse('network_details',
                args=(str(campaign.key()),)),
        })

    def generate_campaign_form(self, campaign_fields, errors, campaign):
        """Create the campaign form given the campaign fields and the existing campaign

        Args:
            campaign_fields: a dict mapping modified fields to properties
            errors: a dict of errors, used for returning errors
            campaign: the existing campaign

        Return:
            errors: by modifying errors
            campaign_form: the campaign django form object

        Author:
            Tiago Bandeira (7/17/2012)
        """
        self.copy_fields(NetworkCampaignForm, campaign_fields, campaign)

        # grab campaign create campaign form
        campaign_form = NetworkCampaignForm(campaign_fields, instance=campaign)

        if not campaign_form.is_valid():
            for key, value in campaign_form.errors.items():
                errors[key] = ' '.join([error for error in value])

        return campaign_form

    def generate_network_adgroup_form(self, network_adgroup_fields, errors, campaign):
        """Create the network adgroup form given the network adgroup fields and the existing campaign

        Args:
            network_adgroup_fields: a dict mapping modified fields to properties
            errors: a dict of errors, used for returning errors
            campaign: the existing campaign

        Return:
            errors: by modifying errors
            network_adgroup_form: the network adgroup django form object

        Author:
            Tiago Bandeira (7/17/2012)
        """
        # grab single adunit adgroup and use it as an initial in form
        adgroup = campaign.adgroups.filter('deleted =', False).get()

        self.copy_fields(NetworkAdGroupForm, network_adgroup_fields, adgroup)

        # apply differences to form
        network_adgroup_form = NetworkAdGroupForm(network_adgroup_fields, instance=adgroup)

        if not network_adgroup_form.is_valid():
            for key, value in network_adgroup_form.errors.items():
                errors[key] = ' '.join([error for error in value])

        return network_adgroup_form

    def generate_adunit_key_adgroup_form_dict(self, adunit_adgroup_fields, errors, campaign):
        """Create all the adunit adgroup forms given the adunit adgroup fields and the existing campaign

        Args:
            adunit_adgroup_fields: a dict of dicts mapping adunit keys of modified adunit adgroups to a mapping
                of modified fields to properties
            errors: a dict of errors, used for returning errors
            campaign: the existing campaign

        Return:
            errors: by modifying errors
            adunit_key_adgroup_form_dict: a dict mapping adunit keys of modified adunit adgroups to
                their AdUnitAdGroup django forms

        Author:
            Tiago Bandeira (7/17/2012)
        """
        adunit_key_adgroup_form_dict = {}
        for adunit_key, adgroup_field_dict in adunit_adgroup_fields.iteritems():
            # get adgroup from db
            adgroup = AdGroupQueryManager.get_network_adgroup(campaign, adunit_key, self.account.key(),
                get_from_db=True)

            self.copy_fields(AdUnitAdGroupForm, adgroup_field_dict, adgroup)
            # create form
            adgroup_form = AdUnitAdGroupForm(adgroup_field_dict, instance=adgroup)

            if not adgroup_form.is_valid():
                for key, value in adgroup_form.errors.items():
                    if key in set(AdUnitAdGroupForm.base_fields.keys()):
                        key = adunit_key + '-' + key
                    errors[key] = ' '.join([error for error in value])
            else:
                self.user_entered_pub_id(adgroup_form, adunit_key, campaign.network_type, errors)

            # add it to dict
            adunit_key_adgroup_form_dict[adunit_key] = adgroup_form

        return adunit_key_adgroup_form_dict

    def user_entered_pub_id(self, adgroup_form, adunit_key, network_type, errors):
        """Check that a pub_id has been entered if adgroup's active property is set to True

        Return:
            errors: by modifying errors

        Author:
            Tiago Bandeira (7/17/2012)
        """
        if adgroup_form.cleaned_data['active'] and network_type in NETWORKS_WITH_PUB_IDS:
            adunit = AdUnitQueryManager.get(adunit_key)
            network_config = adunit.network_config

            if not network_config:
                network_config = NetworkConfig()
                AdUnitQueryManager.update_config_and_put(adunit, network_config)

            pub_id_field = '%s_pub_id' % network_type
            pub_id_query_dict = '%s-%s' % (network_config.key(), pub_id_field)

            query_dict = self.request.POST
            if (pub_id_query_dict not in query_dict and not getattr(network_config, pub_id_field, False)) \
                    or (pub_id_query_dict in query_dict and not query_dict[pub_id_query_dict]):
                errors['%s-%s_pub_id' % (network_config.key(), network_type)] = "MoPub requires an" \
                        " ad network id for enabled adunits."

    def update_network_configs_and_create_mappers(self, pub_id_fields, network_type):
        """Update network_configs and create or delete mappers given pub_id_fields and the network_type

        Args:
            pub_id_fields: a dict of dicts mapping network_config keys to a mapping of fields and values
            network_type: a string, the base name of the network being modified, must be in NETWORKS

        Author:
            Tiago Bandeira (7/17/2012)
        """
        for key, network_config_dict in pub_id_fields.iteritems():
            # get network config
            network_config = NetworkConfigQueryManager.get(key)
            for field, pub_id in network_config_dict.iteritems():
                # make change
                setattr(network_config, field, pub_id)

                adunit = network_config.adunits.get()
                if adunit:
                    AdUnitQueryManager.update_config_and_put(adunit, network_config)
                else:
                    app = network_config.apps.get()

                    if app:
                        AppQueryManager.update_config_and_put(app, network_config)

                        self.create_mapper(network_type, app, pub_id)

    def create_mapper(self, network_type, app, pub_id):
        """Create mapper for the given network_type, app, and pub_id. Delete existing mappers
        with the same network_type and app if they don't have stats.

        Args:
            network_type: a string, the base name of the network being modified, must be in NETWORKS
            app: an Application
            pub_id: a string, the value of the new publisher id

        Author:
            Tiago Bandeira (7/17/2012)
        """
        if network_type in REPORTING_NETWORKS:
            # Create an AdNetworkAppMapper if there exists a
            # login for the network (safe to re-create if it
            # already exists)
            login = AdNetworkLoginManager.get_logins(
                    self.account, network_type).get()
            if login:
                mappers = AdNetworkMapperManager.get_mappers_for_app(login=login, app=app)
                # Delete the existing mappers if there are no scrape
                # stats for them.
                for mapper in mappers:
                    if mapper:
                        stats = mapper.ad_network_stats
                        if not stats.count(1):
                            mapper.delete()
                if pub_id:
                    AdNetworkMapperManager.create(network=network_type,
                            pub_id=pub_id, login=login, app=app)

    def copy_fields(self, form_class, query_dict, instance, prefix=None):
        """Copy fields from the instance to the query dict if they're not already
        in the dict and in the base_fields of the form class

        Args:
            form_class: a django form class
            query_dict: a dict of form fields to values
            instance: the existing instance of what's getting modified
            prefix: a string, if the form has a prefix pass in the prefix

        Return:
            query_dict: by modifying query_dict

        Author:
            Tiago Bandeira (7/17/2012)
        """
        COERCE_FIELDS = {'device_targeting': lambda data: '1' if data else '0',
                         'keywords': lambda data: '\n'.join(data)}

        for field in form_class.base_fields.iterkeys():
            if hasattr(instance, field):
                if prefix:
                    key = prefix + '-' + field
                else:
                    key = field

                if key in query_dict:
                    continue

                value = getattr(instance, field)
                if field in COERCE_FIELDS:
                    value = COERCE_FIELDS[field](value)

                if isinstance(value, list):
                    query_dict[key] = value
                    #query_dict.setlist(key, value)
                else:
                    query_dict[key] = value


    def create(self, network):
        """Create a network campaign.

        Args:
            network: a base network name, must be in NETWORKS, used to create new network campaigns

        Return:
            JSONResponse dict with either errors or success and a redirect url

        Author:
            Tiago Bandeira (7/17/2012)
        """
        apps = PublisherQueryManager.get_apps_dict_for_account(account=
                self.account).values()
        adunits = PublisherQueryManager.get_adunits_dict_for_account(account=
                self.account).values()

        query_dict = self.request.POST.copy()
        if 'name' not in query_dict:
            query_dict['name'] = NETWORKS[network]

        query_dict['campaign_type'] = 'network'

        campaign = None

        # Do no other network campaigns exist or is this custom?
        custom_campaign = CampaignQueryManager.get_network_campaigns(
                self.account, network) or 'custom' in network
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
                            (adunit.key(), network_config_field), None)
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
                    old_creative = adgroup.creatives.get()
                    if old_creative and creative.__class__ == old_creative.__class__:
                        # if the adgroup has a creative AND the new creative and
                        # old creative are the same class,
                        # ignore the new creative and set the variable to point
                        # to the old one
                        creative = old_creative
                        creative.deleted = False
                        if adgroup.network_type == 'custom':
                            # if the network is a custom one, the creative
                            # might be the same, but the data might be new, set
                            # the old creative to have the (possibly) new data
                            creative.html_data = html_data
                        elif adgroup.network_type == 'custom_native':
                            creative.html_data = html_data
                    elif old_creative:
                        #in this case old_creative has evaluated to true BUT the class comparison did NOT.
                        #at this point we know that there was an old creative AND it's different from the new creative so
                        #and delete the old creative just marks as deleted!
                        CreativeQueryManager.delete(old_creative)

                    #put the creative so we can reference it
                    CreativeQueryManager.put(creative)

                    AdGroupQueryManager.put(adgroup)
                    adgroups.append(adgroup)

                # NetworkConfig for Apps
                if network in NETWORKS_WITH_PUB_IDS:
                    for app in apps:
                        network_config = app.network_config or NetworkConfig()
                        app_pub_id = self.request.POST.get("app_%s-%s" %
                                (app.key(), network_config_field), None)
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
                            if login:
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
                                    (adunit.key(), network_config_field), None)

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
                                        '_pub_id', None))
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

        # Once memcache is fixed consider which approach is faster
#        adgroups = AdvertiserQueryManager.get_adgroups_dict_for_account(
#                self.account).values()
        #campaign_adgroups = filter_adgroups_for_campaign(campaign, adgroups)

        apps = PublisherQueryManager.get_objects_dict_for_account(
                self.account).values()
        # Get adgroup by key name
        campaign_adgroups = AdGroupQueryManager.get([AdGroupQueryManager.
            get_network_adgroup(campaign, adunit.key(),
                self.account.key()).key() for app in apps for
                adunit in app.adunits])

        # MoPub reported campaign cpm comes from meta data not stats so
        # we calculate it here instead of over ajax
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

        if campaign_adgroups and campaign_adgroups[0].device_targeting:
            for device, pretty_name in campaign_adgroups[0].DEVICE_CHOICES:
                if getattr(campaign_adgroups[0], 'target_' + device, False):
                    network_data['targeting'].append(pretty_name)
            if campaign_adgroups[0].target_other:
                network_data['targeting'].append('Other')

        if network_data['targeting']:
            network_data['targeting'] = ', '.join(network_data['targeting'])
        else:
            network_data['targeting'] = 'All'

        # This campaign is a default network campaign if its the
        # only one of this type. If this is the default, and if we have
        # login info, then we have reporting stats.
        if campaign.network_state == NetworkStates. \
                DEFAULT_NETWORK_CAMPAIGN:
            login = AdNetworkLoginManager.get_logins(self.account, network). \
                    get()
            if login:
                network_data['login_state'] = login.state
                network_data['reporting'] = True

        # set adunit cpms to corresponding adgroup bids
        app_bids = []
        index = 0
        for app in apps:
            app_adgroups = []
            for adunit in app.adunits:
                # TODO: put bids in app?
                adunit.adgroup = campaign_adgroups[index]
                app_adgroups.append(adunit.adgroup)
                index += 1
            bid_range = get_bid_range(app_adgroups)
            app_bids.append({'min_cpm': bid_range[0],
                             'max_cpm': bid_range[1]})

        network_data['apps'] = zip(apps, app_bids)
        network_data['apps'] = sorted(network_data['apps'], key=lambda
                app_and_bid: app_and_bid[0].identifier)


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
            default_campaigns = CampaignQueryManager.get_network_campaigns(
                    self.account, network_type=campaign.network_type)

            if default_campaigns:
                default_campaign = default_campaigns[0]
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

        adunits = PublisherQueryManager.get_adunits_dict_for_account(
                self.account).values()
        adgroups = AdGroupQueryManager.get([AdGroupQueryManager.
            get_network_adgroup(campaign, adunit.key(),
                self.account.key()).key() for adunit in adunits])
        # Mark all adgroups as deleted
        all_creatives = []
        for adgroup in adgroups:
            adgroup.deleted = True

            creatives = list(adgroup.creatives)
            for creative in creatives:
                creative.deleted = True
            all_creatives += creatives
        AdGroupQueryManager.put(adgroups)
        CreativeQueryManager.put(all_creatives)

        return TextResponse()

@login_required
def delete_network(request, *args, **kwargs):
    return DeleteNetworkHandler()(request, *args, **kwargs)


#############
# Exporting #
#############

class NetworkExporter(RequestHandler):

    def get(self):
        export_type = self.request.GET.get('type', 'html')
        stats = StatsModelQueryManager(self.account)

        stats_per_day = []
        for campaign in CampaignQueryManager.get_network_campaigns(self.account, is_new=True):
            stats_per_day.append(stats.get_stats_for_days(advertiser=campaign, num_days=self.date_range))

        network_data = []
        for day_stats in zip(*stats_per_day):
            req = sum([stat.req for stat in day_stats])
            imp = sum([stat.imp for stat in day_stats])
            fill_rate = float(imp) / req if req else 0
            clk = sum([stat.clk for stat in day_stats])
            ctr = float(clk) / imp if imp else 0

            row = (
                day_stats[0].date,
                req,
                imp,
                fill_rate,
                clk,
                ctr,
            )
            network_data.append(row)

        # Put together the header list
        headers = (
            'Date', 'Requests', 'Impressions',
            'Fill Rate', 'Clicks', 'CTR'
        )

        # Create the data to export from all of the rows
        data_to_export = tablib.Dataset(headers=headers)
        data_to_export.extend(network_data)

        response = HttpResponse(getattr(data_to_export, export_type),
                                mimetype="application/octet-stream")
        response['Content-Disposition'] = 'attachment; filename=networks.%s' %\
                   export_type

        return response

@login_required
def network_exporter(request, *args, **kwargs):
    return NetworkExporter()(request, *args, **kwargs)

###########
# Helpers #
###########

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

