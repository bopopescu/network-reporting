import logging
import datetime

from google.appengine.api import urlfetch

from urllib import urlencode

from copy import deepcopy

import base64, binascii
from google.appengine.api import users, images, files, mail

from google.appengine.ext import db

from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson

from account.forms import (AccountNetworkConfigForm, AppNetworkConfigForm,
                           AdUnitNetworkConfigForm)
from account.models import NetworkConfig
from account.query_managers import AccountQueryManager, NetworkConfigQueryManager
# NOTE: don't be tempted to change this to import *
# Some of these modules import datetime from datetime, which will
# screw up all of the datetime calls in this module.
from advertiser.forms import (CampaignForm, AdGroupForm, BaseCreativeForm,
                              TextCreativeForm, ImageCreativeForm,
                              TextAndTileCreativeForm, HtmlCreativeForm)
from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager,
                                       TextCreativeQueryManager,
                                       ImageCreativeQueryManager,
                                       TextAndTileCreativeQueryManager,
                                       HtmlCreativeQueryManager)
from advertiser.models import Campaign, AdGroup, Creative
from account.models import Account
from ad_server.optimizer.optimizer import DEFAULT_CTR
from budget import budget_service
from common.ragendja.template import (JSONResponse, render_to_response,
                                      render_to_string)
from common.utils import date_magic, helpers, sswriter
from common.utils.helpers import campaign_stats
from common.utils.request_handler import RequestHandler
from common.utils.stats_helpers import (MarketplaceStatsFetcher,
                                        MPStatsAPIException)
from common.utils.timezones import Pacific_tzinfo
from common.utils.tzinfo import Pacific, utc
from publisher.models import Site, App, AdUnit
from publisher.query_managers import (AdUnitQueryManager, AppQueryManager,
                                      AdUnitContextQueryManager, PublisherQueryManager)
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from google.appengine.api import memcache
CAMPAIGN_LEVELS = ['gtee_high', 'gtee', 'gtee_low', 'promo', 'backfill_promo']


class AdGroupIndexHandler(RequestHandler):

    def get(self):
        # Set up the date range
        num_days = 90
        today = datetime.datetime.now(Pacific_tzinfo()).date()
        days = date_magic.gen_days(today - datetime.timedelta(days=(num_days-1)), today)

        # Get all adgroups, filtering out those that are archived or deleted.
        adgroups = AdGroupQueryManager.get_adgroups(account=self.account,
                network_type=None)

        # Divide adgroups into buckets based on priorities, and sort each bucket by bid.
        promo_adgroups, gtee_adgroups, backfill_promo_adgroups = _sort_adgroups(adgroups,
                                                                                self.account)
        promo_adgroups = self._attach_targeted_app_keys_to_adgroups(promo_adgroups,
                self.account)
        gtee_adgroups = self._attach_targeted_app_keys_to_adgroups(gtee_adgroups,
                self.account)
        backfill_promo_adgroups = self._attach_targeted_app_keys_to_adgroups(backfill_promo_adgroups,
                self.account)


        apps = PublisherQueryManager.get_apps_dict_for_account(self.account).values()
        apps = sorted(apps, lambda x, y: cmp(x.name, y.name))

        # TODO: do I need to add 'account': self.account,?
        return render_to_response(self.request,
                                  'advertiser/adgroup_index.html', {
                                      'apps': apps,
                                      'gtee_adgroups': gtee_adgroups,
                                      'promo_adgroups': promo_adgroups,
                                      'backfill_promo_adgroups': backfill_promo_adgroups,
                                      'start_date': days[0],
                                      'end_date': days[-1],
                                      'date_range': num_days,
                                      'offline': self.offline,
                                  })

    def _attach_targeted_app_keys_to_adgroups(self, adgroups, account):
        """
        Takes in a list of adgroups. For each adgroup, determines the apps targeted by that adgroup,
        and attaches this information to the adgroup. Returns the list of updated adgroups.
        """
        # Get all adunits for this account. Important: include the deleted ones, because adgroups
        # can still technically target deleted adunits.
        adunits_dict = PublisherQueryManager.get_adunits_dict_for_account(account,
                                                                          include_deleted=True)

        for adgroup in adgroups:
            # Figure out which adunits are targeted by this adgroup.
            targeted_adunits = []
            for adunit_key in adgroup.site_keys:
                try:
                    adunit = adunits_dict[str(adunit_key)]
                except KeyError:
                    body = "KeyError: Adgroup %s is targeting adunit %s which is not owned by %s" % (str(adgroup.key()), str(adunit_key), account.mpuser.email)
                    mail.send_mail_to_admins(sender="olp@mopub.com",
                                             subject="/campaigns error",
                                             body="%s"%body)
                if adunit.deleted:
                    continue
                targeted_adunits.append(adunit)

            # Determine the apps that the targeted adunits belong to.
            set_of_targeted_apps = set()
            for adunit in targeted_adunits:
                # Looks weird, but we're just avoiding adunit.app_key.key() since it incurs a fetch.
                # TODO: adunit._app works without a fetch right?
                app_key = str(Site.app_key.get_value_for_datastore(adunit))
                set_of_targeted_apps.add(app_key)

            # Attach to the adgroup object.
            adgroup.targeted_app_keys = list(set_of_targeted_apps)

        return adgroups


@login_required
def adgroups(request, *args, **kwargs):
    return AdGroupIndexHandler()(request, use_cache=False, *args, **kwargs)

####### Helpers for campaign page #######
def _sort_guarantee_levels(guaranteed_campaigns):
    """ Sort guaranteed campaigns according to levels """
    levels = ('high', '', 'low')
    gtee_str = "gtee_%s"
    gtee_levels = []
    for level in levels:
        this_level = gtee_str % level if level else "gtee"
        name = level if level else 'normal'
        level_camps = filter(lambda x: x.campaign.campaign_type == this_level, guaranteed_campaigns)
        gtee_levels.append(dict(name=name, adgroups=level_camps))

    # Determine which gtee_levels to display
    for level in gtee_levels:
        if level['name'] == 'normal' and len(gtee_levels[0]['adgroups']) == 0 and len(gtee_levels[2]['adgroups']) == 0:
            level['display'] = True
        elif len(level['adgroups']) > 0:
            level['display'] = True
        else:
            level['display'] = False
    return gtee_levels

def _sort_adgroups(adgroups, account):
    """
    Divides the given list of adgroups into three separate lists (promo, guaranteed, and backfill).
    Within each sub-list, adgroups will be sorted by bid in descending order.
    """
    # Populate the "campaign" property for all adgroups.
    campaigns_dict = AdvertiserQueryManager.get_campaigns_dict_for_account(account)
    filtered_adgroups = []
    for adgroup in adgroups:
        campaign_key = str(AdGroup.campaign.get_value_for_datastore(adgroup))
        if campaign_key in campaigns_dict:
            adgroup.campaign = campaigns_dict[campaign_key]
            filtered_adgroups.append(adgroup)

    promo_adgroups = _sorted_adgroups_for_types(filtered_adgroups, ['promo'])
    gtee_adgroups = _sorted_adgroups_for_types(filtered_adgroups, ['gtee_high',
        'gtee_low', 'gtee'])
    backfill_adgroups = _sorted_adgroups_for_types(filtered_adgroups,
            ['backfill_promo'])

    return [
        promo_adgroups,
        gtee_adgroups,
        backfill_adgroups,
    ]

def _sorted_adgroups_for_types(adgroups, types):
    filtered_adgroups = filter(lambda x: x.campaign_type in types, adgroups)
    return sorted(filtered_adgroups, lambda x, y: cmp(y.bid, x.bid))

def _calc_app_level_stats(adgroups):
    # adgroup1.all_stats = [StatsModel(day=1), StatsModel(day=2), StatsModel(day=3)]
    # adgroup2.all_stats = [StatsModel(day=1), StatsModel(day=2), StatsModel(day=3)]
    # adgroup3.all_stats = [StatsModel(day=1), StatsModel(day=2), StatsModel(day=3)]
    # all_daily_stats = [(StatsModel(day=1),StatsModel(day=1),StatsModel(day=1)),
    #                    (StatsModel(day=2),StatsModel(day=2),StatsModel(day=2)),
    #                    (StatsModel(day=3),StatsModel(day=3),StatsModel(day=3))]
    # returns [StatsModel(day=1)+StatsModel(day=1)+StatsModel(day=1),
    #          StatsModel(day=2)+StatsModel(day=2)+StatsModel(day=2)),
    #          StatsModel(day=3)+StatsModel(day=3)+StatsModel(day=3)]
    all_daily_stats = zip(*[adgroup.all_stats for adgroup in adgroups])
    return [sum(daily_stats, StatsModel()) for daily_stats in all_daily_stats]


def _calc_and_attach_e_cpm(adgroups_with_stats, app_level_summed_stats):
    """ Requires that adgroups already have attached stats """
    for adgroup in adgroups_with_stats:

        if adgroup.cpc:
            app_level_ctr = app_level_summed_stats.ctr
            e_ctr = adgroup.summed_stats.ctr or app_level_ctr or DEFAULT_CTR

            adgroup.summed_stats.e_cpm = float(e_ctr) * float(adgroup.cpc) * 1000

        else:
            adgroup.summed_stats.e_cpm = adgroup.cpm

    return adgroups_with_stats


def _calc_and_attach_osi_success(adgroups):
    for adgroup in adgroups:
        if adgroup.running and adgroup.campaign.budget:
            adgroup.osi_success = budget_service.get_osi(adgroup.campaign.budget_obj)

    return adgroups


class AdGroupArchiveHandler(RequestHandler):
    def get(self):
        archived_adgroups = AdGroupQueryManager().get_adgroups(account=self.account,
                                                               archived=True)
        for adgroup in archived_adgroups:
            adgroup.budget = adgroup.campaign.budget_obj

        return render_to_response(self.request,
                                  'advertiser/archived_adgroups.html',
                                  {
                                      'archived_adgroups': archived_adgroups,
                                  })


@login_required
def archive(request, *args, **kwargs):
    return AdGroupArchiveHandler()(request, *args, **kwargs)


class CreateOrEditCampaignAndAdGroupHandler(RequestHandler):
    """
    Handler for creating or editing campaigns / adgroups.
    """

    class MPFormValidationException(Exception):
        pass

    def get(self, adgroup_key=''):
        """
        Keyword arguments:
        adgroup_key -- the key of the adgroup we want to edit (only used for editing, not creating)
        """

        adgroup_to_edit = AdGroupQueryManager.get(adgroup_key) if adgroup_key else None
        campaign_form = self._campaign_form(adgroup=adgroup_to_edit)
        adgroup_form = self._adgroup_form(adgroup=adgroup_to_edit, apps_choices=get_apps_choices(self.account))
        account_network_config_form = AccountNetworkConfigForm(instance=self.account.network_config)
        apps = self._apps_with_network_config_forms_for_account(self.account)

        if adgroup_to_edit:
            template = 'advertiser/edit_campaign_and_adgroup.html'
        else:
            template = 'advertiser/create_campaign_and_adgroup.html'

        return render_to_response(self.request,
                                  template,
                                  {
                                      'is_staff': self.request.user.is_staff,
                                      'campaign_form': campaign_form,
                                      'adgroup': adgroup_to_edit,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form': account_network_config_form,
                                      'apps': apps,
                                  })

    ### BEGIN helpers for get()

    def _campaign_form(self, adgroup=None):
        """
        Returns a form that can create a campaign. If an adgroup object is provided as an argument
        to this method, the adgroup's campaign will be used as the instance for the form.
        Additionally, the adgroup's bid and bid_strategy will be used as initial values.

        Keyword arguments:
        adgroup -- an adgroup object used to populate CampaignForm values (default None)
        """
        instance = None
        initial = None
        if adgroup:
            instance = adgroup.campaign
            initial = {'bid': adgroup.bid, 'bid_strategy': adgroup.bid_strategy}
        return CampaignForm(instance=instance,
                            initial=initial,
                            is_staff=self.request.user.is_staff,
                            account=self.account)

    def _adgroup_form(self, adgroup=None, apps_choices=[]):
        """
        Returns a form that can create an adgroup. If an adgroup object is provided as an argument
        to this method, the adgroup will be used as the instance for the form.

        Keyword arguments:
        adgroup -- an adgroup object used as the instance for the AdGroupForm (default None)
        """
        return AdGroupForm(instance=adgroup, is_staff=self.request.user.is_staff, apps_choices=apps_choices)

    def _apps_with_network_config_forms_for_account(self, account):
        """
        Given an account, returns a list of app objects with their network config forms attached
        (via the network_config_form property). Additionally, each app in the list has a list of
        adunits attached, each of which has a network config form.

        Arguments:
        account -- the account whose apps we want to fetch
        """
        # Retrieve the list of apps for this account.
        apps = PublisherQueryManager.get_objects_dict_for_account(account).values()

        # Retrieve the dictionary which maps publisher object keys to their network config objects.
        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(account)

        # Add network config forms to each app and adunit.
        for app in apps:
            app_network_config_key = str(App.network_config.get_value_for_datastore(app))
            app_network_config = network_configs_dict.get(app_network_config_key) or app.network_config
            app_key = str(app.key())
            app.network_config_form = AppNetworkConfigForm(instance=app_network_config,
                                                           prefix="app_%s" % app_key)
            for adunit in app.adunits:
                adunit_network_config_key = str(Site.network_config.get_value_for_datastore(adunit))
                adunit_network_config = network_configs_dict.get(adunit_network_config_key) or adunit.network_config
                adunit_key = str(adunit.key())
                adunit.network_config_form = AdUnitNetworkConfigForm(instance=adunit_network_config,
                                                                     prefix="adunit_%s" % adunit_key)

        return apps

    ### END helpers for get()

    def post(self, adgroup_key=''):
        if not self.request.is_ajax():
            raise Http404

        # We're either editing an existing adgroup or creating a new one.
        adgroup_to_edit = AdGroupQueryManager.get(adgroup_key) if adgroup_key else None
        if adgroup_to_edit:
            # Once we start editing, we might change the set of adunits targeted by this adgroup.
            # Therefore, before doing anything, we need to invalidate all adunit contexts relating
            # to the adgroup as it currently stands.
            self._flush_adunit_contexts_affected_by_adgroup(adgroup_to_edit)

        apps = PublisherQueryManager.get_apps_dict_for_account(self.account).values()
        apps_choices = get_apps_choices(self.account)
        adunits = PublisherQueryManager.get_adunits_dict_for_account(self.account).values()

        # Construct the campaign and adgroup objects from the form data. Return an error response
        # if anything goes wrong with the forms.
        try:
            campaign = self._campaign_from_form_data_with_adgroup(adgroup=adgroup_to_edit)

            # XXX: We have to save this campaign before we can assign it to its adgroup. However,
            # we don't need/want to use CampaignQueryManager.put() for this, since that triggers
            # actions that we'll want only after we're completely done editing this campaign.
            campaign.save()

            adgroup = self._adgroup_from_form_data_with_campaign_and_adunits(campaign, adunits,
                    instance=adgroup_to_edit, apps_choices=apps_choices)
        except self.MPFormValidationException, ex:
            errors = ex[0] if len(ex.args) > 0 else {}
            return self._json_failure_response_with_errors(errors)

        # Network campaigns require a few additional steps: generating a "network creative" and
        # updating all of the relevant network config objects.
        if campaign.campaign_type == 'network':
            creative = self._generate_creative_for_adgroup(adgroup)
            self._assign_creative_to_adgroup_and_save(creative, adgroup)

            configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)
            self._update_network_configs_using_adgroup(adgroup, configs_dict, apps, adunits, self.account)

        # Miscellaneous tasks.
        self._flush_adunit_contexts_affected_by_adgroup(adgroup)
        self._mark_user_onboarding_complete_for_account(self.account)

        # Finally, save the objects.
        CampaignQueryManager.put(campaign)
        AdGroupQueryManager.put(adgroup)

        return JSONResponse({
            'success': True,
            'redirect': reverse('advertiser_adgroup_show', args=(adgroup.key(),)),
        })

    ### BEGIN helper methods for post()

    def _campaign_from_form_data_with_adgroup(self, adgroup=None):
        """
        Returns a campaign object created using form data from self.request.POST. If an adgroup
        object is provided as a keyword argument to this method, the adgroup's campaign will be used
        as the instance for the form. Additionally, the adgroup's bid and bid_strategy will be used
        as initial values.

        Keyword arguments:
        adgroup -- an adgroup object (default None)

        Note: this method does not save the campaign to the datastore; you must do it yourself.
        """
        # Create the CampaignForm; if an adgroup was passed in, use it to get initial values.
        instance = None
        initial = None
        if adgroup:
            instance = adgroup.campaign
            initial = {'bid': adgroup.bid, 'bid_strategy': adgroup.bid_strategy}
        form = CampaignForm(self.request.POST,
                            instance=instance,
                            initial=initial,
                            is_staff=self.request.user.is_staff,
                            account=self.account)


        if not form.is_valid():
            errors = {}
            for key, value in form.errors.items():
                # TODO: find a less hacky way to get jQuery validator's
                # showErrors function to work with the SplitDateTimeWidget
                if key == 'start_datetime':
                    key = 'start_datetime_1'
                elif key == 'end_datetime':
                    key = 'end_datetime_1'
                errors[key] = ' '.join([error for error in value])
            raise self.MPFormValidationException(errors)

        campaign = form.save(commit=False)
        campaign.account = self.account
        return campaign

    def _adgroup_from_form_data_with_campaign_and_adunits(self, campaign, adunits, instance=None, apps=[]):
        """
        Returns an adgroup object created using form data from self.request.POST. The adgroup's
        campaign property will point to the given campaign, and its site_keys will be some subset
        of the given list of adunits.

        If an existing adgroup instance is provided as an argument, that object will be passed as
        the 'instance' keyword argument to the AdGroupForm.

        Arguments:
        campaign -- the campaign to which this adgroup should belong
        adunits  -- the list of adunits that are allowed to be targeted by this adgroup

        Keyword arguments:
        instance -- an adgroup object (default None)

        Note: this method does not save the adgroup to the datastore; you must do it yourself.
        """
        site_keys = [(unicode(adunit.key()), '') for adunit in adunits]
        form = AdGroupForm(self.request.POST, instance=instance, site_keys=site_keys,
                           is_staff=self.request.user.is_staff, apps=apps)

        if not form.is_valid():
            errors = {}
            for key, value in form.errors.items():
                errors[key] = ' '.join([error for error in value])
            raise self.MPFormValidationException(errors)

        adgroup = form.save(commit=False)

        # Update fields on the adgroup that don't come from the POST data (e.g. account).
        # IMPORTANT: don't use self.account, since that can often belong to a superuser!
        adgroup.account = campaign.account
        adgroup.campaign = campaign
        if campaign.campaign_type != 'network':
            adgroup.network_type = None

        return adgroup

    def _json_failure_response_with_errors(self, errors):
        """
        Returns an HTTP response representing failure, along with a set of errors.

        Arguments:
        errors -- a list of errors
        """
        return JSONResponse({'errors': errors, 'success': False})

    def _generate_creative_for_adgroup(self, adgroup):
        """
        Returns a creative object for the given adgroup based on form data from self.request.POST.

        Arguments:
        adgroup -- the adgroup for which we want to generate a creative

        Note: this method does not save the creative to the datastore. However, the adgroup passed
        to this method will be saved, because the adgroup's key is required to generate a creative.
        """
        html_data = None

        if adgroup.network_type == 'custom':
            html_data = self.request.POST.get('custom_html', '')
        elif adgroup.network_type == 'custom_native':
            html_data = self.request.POST.get('custom_method', '')

        # We need to save the adgroup before we can call default_creative.
        AdGroupQueryManager.put(adgroup)

        return adgroup.default_creative(html_data)

    def _assign_creative_to_adgroup_and_save(self, creative, adgroup):
        """
        Sets the given adgroup's net_creative property to be the given creative, and then saves
        both the creative and the adgroup to the datastore.

        Generally, if the given adgroup's net_creative property already exists, that creative will
        be deleted. However, if that (old) creative is of the same type as the new creative, it
        can be re-used.

        Arguments:
        creative -- the creative to be assigned
        adgroup -- the adgroup which will receive the new creative
        """
        new_creative = creative
        old_creative = adgroup.net_creative

        # Re-use the old creative if it's of the same type as the new creative.
        if old_creative and old_creative.__class__ == new_creative.__class__:
            # Use html_data from the new creative.
            if adgroup.network_type in ('custom', 'custom_native'):
                old_creative.html_data = new_creative.html_data
            new_creative = old_creative

        # Otherwise, mark the old creative as deleted, since we'll be using the new creative.
        elif old_creative:
            CreativeQueryManager.delete(old_creative)

        # Update the creative's account property and save the creative.
        # IMPORTANT: don't use self.account, since that can often belong to a superuser!
        new_creative.account = adgroup.account
        CreativeQueryManager.put(new_creative)

        # Assign the new creative to the adgroup and save the adgroup.
        adgroup.net_creative = new_creative.key()
        AdGroupQueryManager.put(adgroup)

    def _update_network_configs_using_adgroup(self, adgroup, all_configs, apps, adunits, account):
        """
        Updates all app-, adunit-, and account-level NetworkConfig objects related to the given
        adgroup.

        Arguments:
        adgroup     -- the adgroup
        all_configs -- a dictionary mapping publisher object keys to NetworkConfig objects
        apps        -- the list of apps belonging to the owner of this adgroup
        adunits     -- the list of adunits belonging to the owner of this adgroup
        account     -- the account belonging to the owner of this adgroup
        """
        self._update_app_network_configs_using_adgroup(adgroup, all_configs, apps)
        self._update_adunit_network_configs_using_adgroup(adgroup, all_configs, adunits)
        self._update_account_network_configs_using_adgroup(adgroup, all_configs, account)

    def _update_app_network_configs_using_adgroup(self, adgroup, all_configs, apps):
        """
        Updates all app-level NetworkConfig objects related to the given adgroup.

        Arguments:
        adgroup     -- the adgroup
        all_configs -- a dictionary mapping publisher object keys to NetworkConfig objects
        apps        -- the list of apps belonging to the owner of this adgroup
        """
        # Only certain networks have app-level IDs.
        if adgroup.network_type not in ('admob_native', 'brightroll',
                                        'ejam', 'inmobi', 'jumptap',
                                        'millennial_native', 'mobfox'):
            return

        # Get rid of _native in admob_native, millennial_native.
        network_config_field = "%s_pub_id" % adgroup.network_type.replace('_native', '')

        configs = []
        for app in apps:
            app_network_config_key = str(App.network_config.get_value_for_datastore(app))
            network_config = all_configs.get(app_network_config_key) or app.network_config or NetworkConfig(account=self.account)
            setattr(network_config, network_config_field,
                    self.request.POST.get("app_%s-%s" % (app.key(), network_config_field), ''))
            configs.append(network_config)

        AppQueryManager.update_config_and_put_multi(apps, configs)

    def _update_adunit_network_configs_using_adgroup(self, adgroup, all_configs, adunits):
        """
        Updates all adunit-level NetworkConfig objects related to the given adgroup.

        Arguments:
        adgroup     -- the adgroup
        all_configs -- a dictionary mapping publisher object keys to NetworkConfig objects
        adunits     -- the list of adunits belonging to the owner of this adgroup
        """
        # Only certain networks have adunit-level IDs.
        if adgroup.network_type not in ('admob_native', 'jumptap', 'millennial_native'):
            return

        # Get rid of _native in admob_native, millennial_native.
        network_config_field = "%s_pub_id" % adgroup.network_type.replace('_native', '')

        configs = []
        for adunit in adunits:
            adunit_network_config_key = str(AdUnit.network_config.get_value_for_datastore(adunit))
            network_config = all_configs.get(adunit_network_config_key) or adunit.network_config or NetworkConfig(account=self.account)
            setattr(network_config, network_config_field,
                    self.request.POST.get("adunit_%s-%s" % (adunit.key(), network_config_field), ''))
            configs.append(network_config)

        AdUnitQueryManager.update_config_and_put_multi(adunits, configs)

    def _update_account_network_configs_using_adgroup(self, adgroup, all_configs, account):
        """
        Updates the account-level NetworkConfig object for this adgroup.

        Arguments:
        adgroup     -- the adgroup
        all_configs -- a dictionary mapping publisher object keys to NetworkConfig objects
        account     -- the account belonging to the owner of this adgroup
        """
        # Only Jumptap requires an account-level publisher alias.
        if adgroup.network_type != 'jumptap':
            return

        network_config_field = "%s_pub_id" % adgroup.network_type
        account_network_config_key = str(Account.network_config.get_value_for_datastore(account))
        network_config = all_configs.get(account_network_config_key) or account.network_config or NetworkConfig(account=account)
        setattr(network_config, network_config_field, self.request.POST.get('jumptap_pub_id', ''))
        AccountQueryManager.update_config_and_put(account, network_config)

    def _flush_adunit_contexts_affected_by_adgroup(self, adgroup):
        """
        Clears from memcache any adunit contexts that are affected by changes to this adgroup.

        Arguments:
        adgroup -- the adgroup that has been changed
        """
        if not adgroup or not adgroup.site_keys:
            return

        adunits = AdUnitQueryManager.get(adgroup.site_keys)
        AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

    def _mark_user_onboarding_complete_for_account(self, account):
        """
        Conditionally updates the given account's onboarding status. If the only remaining step was
        to add campaigns, the onboarding process is now complete. Otherwise, don't do anything.

        Arguments:
        account -- the account to update
        """
        if account.status != 'step4':
            return

        account.status = ''
        AccountQueryManager.put_accounts(account)

    ### END helper methods for post()

@login_required
def create_or_edit_campaign_and_adgroup(request, *args, **kwargs):
    return CreateOrEditCampaignAndAdGroupHandler()(request, *args, **kwargs)

class AdGroupDetailHandler(RequestHandler):
    """
    Holy christ, refactor

                     %%%%%%
                   %%%% = =
                   %%C    >
                    _)' _( .' ,
                 __/ |_/\   " *. o
                /` \_\ \/     %`= '_  .
               /  )   \/|      .^',*. ,
              /' /-   o/       - " % '_
             /\_/     <       = , ^ ~ .
             )_o|----'|          .`  '
         ___// (_  - (\
        ///-(    \'   \\
    """
    def get(self, adgroup_key):
        stats_q = StatsModelQueryManager(self.account, self.offline)

        # Load the ad group
        # 1 GET
        adgroup = AdGroupQueryManager.get(adgroup_key)

        # Direct sold campaigns have a start date, and sometimes an end date.
        # Use those values if they both exist, otherwise set the range from
        # start to start + 90 days
        # 1 GET
        if adgroup.campaign.gtee() or adgroup.campaign.promo():
            today = datetime.datetime.now(Pacific_tzinfo())

            if adgroup.campaign.end_datetime \
               and adgroup.campaign.end_datetime.replace(tzinfo=utc).astimezone(Pacific) < today:
                self.end_date = adgroup.campaign.end_datetime.replace(tzinfo=utc).astimezone(Pacific)
            else:
                self.end_date = today

            if adgroup.campaign.start_datetime:
                if adgroup.campaign.start_datetime.replace(tzinfo=utc).astimezone(Pacific) > today:
                    self.start_date = today
                else:
                    self.start_date = adgroup.campaign.start_datetime.replace(tzinfo=utc).astimezone(Pacific)
            else:
                self.start_date = self.end_date - datetime.timedelta(90)

            self.days = date_magic.gen_days(self.start_date, self.end_date)

            # We want to limit the number of stats we have to fetch.
            # We've determined 90 is a good max.
            if len(self.days) > 90:
                self.days = self.days[len(self.days) - 90:]

            # We want to display at least 7 days of data
            if len(self.days) < 7:
                better_end_date = self.days[-1] + datetime.timedelta(7 - len(self.days))
                # unless that makes us show future days
                if better_end_date > today:
                    better_end_date = today
                self.days = date_magic.gen_days(self.days[0], better_end_date)

            self.start_date = self.days[0]
            self.end_date = self.days[-1]
            self.date_range = (self.end_date - self.start_date).days + 1

        # Show a flash message recommending using reports if selecting more than 30 days
        if self.date_range > 30:
            self.request.flash['message'] = """For showing more than 30 days we recommend
                                               using the <a href='%s'>Reports</a> page.""" %  \
                                               reverse('reports_index')
        else:
            del self.request.flash['message']

        # Load stats

        ctr = lambda clicks, impressions: \
              (clicks/float(impressions) if impressions else 0)
        ecpm = lambda revenue, impressions: \
               (revenue/float(impressions)*1000 if impressions else 0)
        fill_rate = lambda requests, impressions: \
                    (impressions/float(requests) if requests else 0)

        # 1 GET
        adgroup.all_stats = stats_q.get_stats_for_days(advertiser=adgroup,
                days=self.days)
        adgroup.stats = reduce(lambda x, y: x + y, adgroup.all_stats, StatsModel())
        adgroup.percent_delivered = budget_service.percent_delivered(adgroup.campaign.budget_obj)
        try:
            # TODO: ecpm = bid or rev / imp * 1000 should be dependent on
            # campaign_type
            adgroup.stats.ecpm = ecpm(adgroup.stats.revenue,
                                      adgroup.stats.impression_count)
        except Exception:
            pass

        try:
            adgroup.stats.ctr = ctr(adgroup.stats.click_count,
                                    adgroup.stats.impression_count)
        except Exception:
            pass

        try:
            adgroup.stats.fill_rate = fill_rate(adgroup.stats.request_count,
                                                adgroup.stats.impression_count)
        except Exception:
            pass

        # Load creatives and populate
        # 1 RunQuery
        creatives = CreativeQueryManager.get_creatives(adgroup=adgroup)
        for creative in creatives:
            creative.all_stats = StatsModelQueryManager(self.account,
                                                 offline=self.offline).get_stats_for_days(advertiser=creative,
                                                                                          days=self.days)
            creative.stats = reduce(lambda x, y: x + y, creative.all_stats, StatsModel())
            # TODO: Should fix DB so that format is always there
            if not creative.format:
                creative.format = "320x50"
            creative.size = creative.format.partition('x')

        # Load all adunits targeted by this adgroup/camaign
        # 1 GET
        adunits = AdUnitQueryManager.get_adunits(keys=adgroup.site_keys)
        apps_dict = PublisherQueryManager.get_apps_dict_for_account(self.account)
        for adunit in adunits:
            # 1 GET per adunit
            app = apps_dict.get(str(adunit._app_key))
            if not app:
                logging.error("AdUnit %s was in account %s, but its App %s was not." % (adunit, self.account, adunit.app_key))
                continue
            if not hasattr(app, 'adunits'):
                app.adunits = []
            app.adunits.append(adunit)

        for app in apps_dict.values():
            if not hasattr(app, 'adunits'):
                del apps_dict[str(app.key())]

        # Load creatives if we are supposed to
        if not (adgroup.campaign.campaign_type in ['network', 'marketplace', 'backfill_marketplace']):
            # In order to have add creative
            creative_handler = AddCreativeHandler(self.request)
            creative_fragment = creative_handler.get()  # return the creative fragment

            # In order to have each creative be editable
            for c in creatives:
                c.html_fragment = creative_handler.get(creative=c)
        else:
            creative_fragment = None

        network_configs_dict = NetworkConfigQueryManager.get_network_configs_dict_for_account(self.account)

        message = []
        if adgroup.network_type and not 'custom' in adgroup.network_type and adgroup.network_type != 'iAd':
            # Get rid of _native in admob_native_pub_id and
            # millennial_native_pub_id.
            adgroup_network_type = adgroup.network_type.replace('_native', '')

            self.account.network_config = network_configs_dict.get(str(self.account._network_config))
            if not (self.account.network_config and
                    getattr(self.account.network_config, adgroup_network_type + '_pub_id')):

                for app in apps_dict.values():
                    app.network_config = network_configs_dict.get(str(app._network_config))
                    if not (app.network_config and
                            getattr(app.network_config, adgroup_network_type + '_pub_id')):

                        for adunit in app.adunits:
                            adunit.network_config = network_configs_dict.get(str(adunit._network_config))
                            if not (adunit.network_config and
                                    getattr(adunit.network_config, adgroup_network_type + '_pub_id')):
                                message.append("The application " + app.name + " needs to have a <strong>" + adgroup_network_type.title() + " Network ID</strong> in order to serve. Specify a " + adgroup_network_type.title() + " Network ID on <a href=%s>your account's ad network settings</a> page." % reverse("ad_network_settings"))
                                break
        message = "<br/>".join(message)

        # Sort apps alphabetically
        sorted_apps = sorted(apps_dict.values(), key=lambda app: app.name)

        return render_to_response(self.request,
                                  'advertiser/adgroup.html',
                                  {
                                      'account': self.account,
                                      'is_staff': self.request.user.is_staff,
                                      'campaign': adgroup.campaign,
                                      'apps': sorted_apps,
                                      'adgroup': adgroup,
                                      'adgroup_key': adgroup_key,
                                      'creatives': creatives,
                                      'totals': adgroup.stats,
                                      'start_date': self.start_date,
                                      'end_date': self.end_date,
                                      'date_range': self.date_range,
                                      'creative_fragment': creative_fragment,
                                      'message': message
                                  })

    def post(self, adgroup_key):
        """
        Used to change an adgroup's status (active/paused/archived/deleted)
        """
        adgroup = AdGroupQueryManager.get(adgroup_key)

        # Update the adgroup's status if it's changed
        opt = self.params.get('action')
        update = False
        campaign = adgroup.campaign
        if opt == 'play':
            adgroup.active = True
            adgroup.archived = False
            update = True
        elif opt == 'pause':
            adgroup.active = False
            adgroup.archived = False
            update = True
        elif opt == "archive":
            adgroup.active = False
            adgroup.archived = True
            update = True
        elif opt == "delete":
            adgroup.deleted = True
            campaign.deleted = True
            AdGroupQueryManager.put(adgroup)
            CampaignQueryManager.put(campaign)

            self.request.flash["message"] = "Campaign: %s has been deleted." % adgroup.name
            return HttpResponseRedirect(reverse('advertiser_campaign'))

        else:
            logging.error("Passed an impossible option")

        if update:
            campaign.active = adgroup.active
            campaign.deleted = adgroup.deleted
            CampaignQueryManager.put(campaign)
            AdGroupQueryManager.put(adgroup)
        return HttpResponseRedirect(reverse('advertiser_adgroup_show',
                                            kwargs={
                                                'adgroup_key': str(adgroup.key())
                                            }))


@login_required
def advertiser_adgroup_show(request, *args, **kwargs):
    handler = AdGroupDetailHandler(id='adgroup_key')
    return handler(request, use_cache=False, *args, **kwargs)


class PauseAdGroupHandler(RequestHandler):
    """ Update the status of a collection of AdGroups, given a list of affected AdGroup keys (passed as 'id')
        and a desired status (passed as 'action'). Action can have the following values: 'resume', 'activate',
        'archive', or 'delete'. The relevant AdGroups' Campaigns and Creatives are also appropriately updated.
    """
    def post(self):
        action = self.request.POST.get("action", "pause")
        adgroups_keys = self.request.POST.getlist('id') or []

        if not adgroups_keys:
            return HttpResponseRedirect(self.request.environ.get('HTTP_REFERER'))

        account_key = self.account.key()

        adgroups = AdGroupQueryManager.get(adgroups_keys)
        # Filter out adgroups that don't belong to this account.
        adgroups_for_this_account = filter(lambda a: AdGroup.account.get_value_for_datastore(a) == account_key, adgroups)

        campaigns_keys = [str(AdGroup.campaign.get_value_for_datastore(adgroup)) for adgroup in adgroups_for_this_account]
        campaigns = CampaignQueryManager.get(campaigns_keys)

        for campaign in campaigns:
            campaign.active = action in ["resume", "activate"]
            campaign.deleted = action in ["delete"]
        CampaignQueryManager.put(campaigns)

        for adgroup in adgroups_for_this_account:
            adgroup.active = action in ["resume", "activate"]
            adgroup.archived = action in ["archive"]
            adgroup.deleted = action in ["delete"]
        AdGroupQueryManager.put(adgroups_for_this_account)

        # If deleting adgroups, grab the corresponding creatives to delete as well. If there are changes
        # at this level, make sure to update the datastore accordingly.
        if action in ["delete"]:
            creatives = Creative.all().filter('account =', self.account).filter('ad_group IN', adgroups_for_this_account).fetch(1000)
            for creative in creatives:
                creative.deleted = True
            CreativeQueryManager.put(creatives)

        # Flash a message to the user for activate/archive/delete.
        if action in ["activate"]:
            self.request.flash["message"] = "A campaign has been activated. View it within <a href='%s'>active campaigns</a>." % reverse('advertiser_campaign')
        elif action in ["archive"]:
            self.request.flash["message"] = "A campaign has been archived. View it within <a href='%s'>archived campaigns</a>." % reverse('advertiser_archive')
        elif action in ["delete"]:
            self.request.flash["message"] = "Your campaign has been successfully deleted."


        # TODO: we need a cross-platform default redirect in case
        # HTTP_REFERER doesn't exist
        return HttpResponseRedirect(self.request.environ.get('HTTP_REFERER'))

@login_required
def bid_pause(request, *args, **kwargs):
    return PauseAdGroupHandler()(request, *args, **kwargs)


class AddCreativeHandler(RequestHandler):
    """ AJAX Creative Create/Edit """
    TEMPLATE = 'advertiser/forms/creative_form.html'

    def get(self,
            base_creative_form=None,
            text_creative_form=None,
            image_creative_form=None,
            text_tile_creative_form=None,
            html_creative_form=None,
            creative=None,
            text_creative=None,
            image_creative=None,
            text_tile_creative=None,
            html_creative=None):

        # TODO: Shouldn't I be able to just cast???
        if creative:
            if creative.ad_type == "text":
                text_creative = TextCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "text_icon":
                text_tile_creative = TextAndTileCreativeQueryManager.get(creative.key())
            elif creative.ad_type == 'image':
                image_creative = ImageCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "html":
                html_creative = HtmlCreativeQueryManager.get(creative.key())

        # NOTE: creative is usually None so the default form is actually unbound
        base_creative_form = base_creative_form or BaseCreativeForm(instance=creative)
        text_creative_form = text_creative_form or TextCreativeForm(instance=text_creative)
        image_creative_form = image_creative_form or ImageCreativeForm(instance=image_creative)
        text_tile_creative_form = text_tile_creative_form or TextAndTileCreativeForm(instance=text_tile_creative)
        html_creative_form = html_creative_form or HtmlCreativeForm(instance=html_creative)

        # text_creative_form is unused in the template, why?
        return self.render(base_creative_form=base_creative_form,
                           text_creative_form=text_creative_form,
                           image_creative_form=image_creative_form,
                           text_tile_creative_form=text_tile_creative_form,
                                    html_creative_form=html_creative_form)

    def render(self, template=None, **kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request, template_name=template_name, data=kwargs)

    def json_response(self, json_dict):
        # Some browsers won't accept the application/json mimetype.
        # Transfer as text/plain if that's the case.
        # HACK
        # broken_browsers = ['Firefox', 'MSIE']
        # for browser in broken_browsers:
        #     if self.request.META['HTTP_USER_AGENT'].find(browser) > 0:
        #         json_str = simplejson.dumps(json_dict)
        #         return HttpResponse(json_str)

        return JSONResponse(json_dict)

    def post(self):
        """
        Holy christ, refactor

                     %%%%%%
                   %%%% = =
                   %%C    >
                    _)' _( .' ,
                 __/ |_/\   " *. o
                /` \_\ \/     %`= '_  .
               /  )   \/|      .^',*. ,
              /' /-   o/       - " % '_
             /\_/     <       = , ^ ~ .
             )_o|----'|          .`  '
         ___// (_  - (\
        ///-(    \'   \\
        """
        ad_group = AdGroupQueryManager.get(self.request.POST.get('adgroup_key'))
        creative_key = self.request.POST.get('creative_key')
        if creative_key:
            creative = CreativeQueryManager.get(creative_key)
        else:
            creative = None

        creative_form = None
        text_creative = None
        image_creative = None
        text_tile_creative = None
        html_creative = None

        # TODO: Shouldn't I be able to just cast???
        if creative:
            if creative.ad_type == "text":
                text_creative = TextCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "text_icon":
                text_tile_creative = TextAndTileCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "image":
                image_creative = ImageCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "html":
                html_creative = HtmlCreativeQueryManager.get(creative.key())

        base_creative_form = BaseCreativeForm(data=self.request.POST, instance=creative)
        text_creative_form = TextCreativeForm(data=self.request.POST, instance=text_creative)
        image_creative_form = ImageCreativeForm(data=self.request.POST, files=self.request.FILES, instance=image_creative)
        text_tile_creative_form = TextAndTileCreativeForm(data=self.request.POST, files=self.request.FILES, instance=text_tile_creative)
        html_creative_form = HtmlCreativeForm(data=self.request.POST, instance=html_creative)

        jsonDict = {'success': False, 'errors': []}
        if base_creative_form.is_valid():
            base_creative = base_creative_form.save(commit=False)
            ad_type = base_creative.ad_type
            if ad_type == "text":
                creative_form = text_creative_form
            elif ad_type == "text_icon":
                creative_form = text_tile_creative_form
            elif ad_type == "image":
                creative_form = image_creative_form
            elif ad_type == "html":
                creative_form = html_creative_form

            if creative_form.is_valid():

                if not creative_form.instance:  # ensure form posts do not change ownership
                    account = self.account
                else:
                    account = creative_form.instance.account
                creative = creative_form.save(commit=False)
                creative.account = account
                creative.ad_group = ad_group
                CreativeQueryManager.put(creative)

                jsonDict.update(success=True)
                return self.json_response(jsonDict)

        flatten_errors = lambda frm: [(k, unicode(v[0])) for k, v in frm.errors.items()]
        grouped_errors = flatten_errors(base_creative_form)
        if creative_form:
            grouped_errors.extend(flatten_errors(creative_form))

        jsonDict.update(success=False, errors=grouped_errors)
        return self.json_response(jsonDict)


@login_required
def creative_create(request, *args, **kwargs):
    return AddCreativeHandler()(request, *args, **kwargs)


class DisplayCreativeHandler(RequestHandler):
    def get(self, creative_key):
        if creative_key == 'mraid.js':
            return HttpResponse("")
        c = CreativeQueryManager.get(creative_key)
        if c and c.ad_type == "image":

            return HttpResponse('<html><head><style type="text/css">body{margin:0;padding:0;}</style></head><body><img src="%s"/></body></html>' % helpers.get_url_for_blob(c.image_blob))
            # return HttpResponse(c.image,content_type='image/png')
        if c and c.ad_type == "text_icon":
            c.icon_url = helpers.get_url_for_blob(c.image_blob)

            return render_to_response(self.request, 'advertiser/text_tile.html', {'c': c})
            #return HttpResponse(c.image,content_type='image/png')
        if c and c.ad_type == "html":
            return HttpResponse("<html><body style='margin:0px;'>" + c.html_data + "</body></html")


class CreativeImageHandler(RequestHandler):
    def get(self, creative_key):
        c = CreativeQueryManager.get(creative_key)
        if c and c.image:
            return HttpResponse(c.image, content_type='image/png')
        raise Http404


def creative_image(request, *args, **kwargs):
    return DisplayCreativeHandler()(request, *args, **kwargs)


def creative_html(request, *args, **kwargs):
    return DisplayCreativeHandler()(request, *args, **kwargs)


class CreativeManagementHandler(RequestHandler):
    def post(self):
        adgroup_key = self.request.POST.get('adgroup_key')
        keys = self.request.POST.getlist('key')
        action = self.request.POST.get('action', 'pause')
        update_objs = []
        # TODO: bulk get before for loop
        for creative_key in keys:
            c = CreativeQueryManager.get(creative_key)
            if c != None and c.ad_group.campaign.account == self.account:  # TODO: clean up dereferences
                if action == "pause":
                    c.deleted = False
                    c.active = False
                    update_objs.append(c)
                elif action == "resume":
                    c.deleted = False
                    c.active = True
                    update_objs.append(c)
                elif action == "delete":
                    c.deleted = True
                    c.active = False
                    update_objs.append(c)

        if update_objs:
            # db.put(update_objs)
            CreativeQueryManager.put(update_objs)

        return HttpResponseRedirect(reverse('advertiser_adgroup_show', kwargs={'adgroup_key': adgroup_key}))


@login_required
def creative_manage(request, *args, **kwargs):
    return CreativeManagementHandler()(request, *args, **kwargs)


class AdServerTestHandler(RequestHandler):
    def get(self):
        devices = [('iphone', 'iPhone'), ('ipad', 'iPad'), ('nexus_s', 'Nexus S')]
        device_to_user_agent = {
            'iphone': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; %s) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7',
            'ipad': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; %s) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
            'nexus_s': 'Mozilla/5.0 (Linux; U; Android 2.1; %s) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
            'chrome': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.A.B.C Safari/525.13',
        }
        country_to_locale_ip = {
            'US': ('en-US', '204.28.127.10'),
            'FR': ('fr-FR', '96.20.81.147'),
            'HR': ('hr-HR', '93.138.74.115'),
            'DE': ('de-DE', '212.183.113.32'),
            'DA': ('dk-DA', '62.107.177.124'),
            'FI': ('fi-FI', '91.152.79.118'),
            'JA': ('jp-JA', '110.163.227.87'),
            'HD': ('us-HD', '59.181.77.74'),
            'HE': ('il-HE', '99.8.113.207'),
            'RU': ('ru-RU', '83.149.3.32'),
            'NL': ('nl-NL', '77.251.143.68'),
            'PT': ('br-PT', '189.104.89.115'),
            'NB': ('no-NB', '88.89.244.197'),
            'TR': ('tr-TR', '78.180.93.4'),
            'NE': ('go-NE', '0.1.0.2'),
            'TH': ('th-TH', '24.52.71.42'),
            'RO': ('ro-RO', '85.186.180.111'),
            'IS': ('is-IS', '194.144.110.171'),
            'PL': ('pl-PL', '193.34.3.100'),
            'EL': ('gr-EL', '62.38.244.73'),
            'EN': ('us-EN', '174.255.120.125'),
            'ZH': ('tw-ZH', '124.190.51.251'),
            'MS': ('my-MS', '120.141.166.6'),
            'CA': ('es-CA', '95.17.76.100'),
            'IT': ('it-IT', '151.56.174.44'),
            'AR': ('sa-AR', '188.55.13.170'),
            'IN': ('id-IN', '114.57.226.18'),
            'CS': ('cz-CS', '90.180.148.68'),
            'HU': ('hu-HU', '85.66.221.12'),
            'ID': ('id-ID', '180.214.232.8'),
            'ES': ('ec-ES', '190.10.214.187'),
            'KO': ('kr-KO', '112.170.242.147'),
            'SV': ('se-SV', '90.225.96.11'),
            'SK': ('sk-SK', '213.151.218.130'),
            'UK': ('ua-UK', '92.244.103.199'),
            'SL': ('si-SL', '93.103.136.7'),
            'AU': ('en-AU', '114.30.96.10'),
        }

        adunits = AdUnitQueryManager.get_adunits(account=self.account)

        return render_to_response(self.request,
                                  'advertiser/adserver_test.html',
                                  {'adunits': adunits,
                                   'devices': devices,
                                   'countries': sorted(country_to_locale_ip.keys()),
                                   'device_to_user_agent': simplejson.dumps(device_to_user_agent),
                                   'country_to_locale_ip': simplejson.dumps(country_to_locale_ip)})


@login_required
def adserver_test(request, *args, **kwargs):
    return AdServerTestHandler()(request, *args, **kwargs)


class CampaignExporter(RequestHandler):
    def post(self, adgroup_key, file_type, start, end, *args, **kwargs):
        start = datetime.datetime.strptime(start, '%m%d%y')
        end = datetime.datetime.strptime(end, '%m%d%y')
        days = date_magic.gen_days(start, end)
        adgroup = AdGroupQueryManager.get(adgroup_key)
        all_stats = StatsModelQueryManager(self.account, offline=self.offline).get_stats_for_days(advertiser=adgroup, days=days)
        f_name_dict = dict(adgroup_title=adgroup.campaign.name,
                           start=start.strftime('%m/%d/%y'),
                           end=end.strftime('%m/%d/%y'),
                           )
        # Build
        f_name = "MoPub Campaign Stats--Name:%(adgroup_title)s--DateRange:%(start)s - %(end)s" % f_name_dict
        f_name = f_name.encode('ascii', 'ignore')
        # Zip up days w/ corresponding stats object and other stuff
        data = map(lambda x: [x[0]] + x[1], zip([day.strftime('%a, %b %d, %Y') for day in days], [campaign_stats(stat, adgroup.campaign.campaign_type) for stat in all_stats]))
        # Row titles
        c_type = adgroup.campaign.campaign_type
        titles = ['Date']
        if c_type == 'network':
            titles += ['Attempts', 'Impressions', 'Fill Rate', 'Clicks', 'CTR']
        elif 'gtee' in c_type:
            titles += ['Impressions', 'Clicks', 'CTR', 'Revenue']
        elif 'promo' in c_type:
            titles += ['Impressions', 'Clicks', 'CTR', 'Conversions', 'Conversion Rate']
        return sswriter.export_writer(file_type, f_name, titles, data)


def campaign_export(request, *args, **kwargs):
    return CampaignExporter()(request, *args, **kwargs)


def get_apps_choices(account):
    apps = PublisherQueryManager.get_apps_dict_for_account(account).values()
    apps.sort(key=lambda app: app.name.lower())
    return [(str(app.key()), "%s (%s)" % (app.name, app.type)) for app in apps]
