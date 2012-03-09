import logging
import datetime


from google.appengine.api import urlfetch

from urllib import urlencode

from copy import deepcopy

import base64, binascii
from google.appengine.api import users, images, files

from google.appengine.ext import db

from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson

from account.forms import (AccountNetworkConfigForm, AppNetworkConfigForm,
                           AdUnitNetworkConfigForm)
from account.models import NetworkConfig
from account.query_managers import AccountQueryManager
# NOTE: don't be tempted to change this to import *
# Some of these modules import datetime from datetime, which will
# screw up all of the datetime calls in this module.
from advertiser.forms import (CampaignForm, AdGroupForm, BaseCreativeForm,
                              TextCreativeForm, ImageCreativeForm,
                              TextAndTileCreativeForm, HtmlCreativeForm)
from advertiser.query_managers import (CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager,
                                       TextCreativeQueryManager,
                                       ImageCreativeQueryManager,
                                       TextAndTileCreativeQueryManager,
                                       HtmlCreativeQueryManager)
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
from publisher.models import Site
from publisher.query_managers import (AdUnitQueryManager, AppQueryManager,
                                      AdUnitContextQueryManager)
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager


CAMPAIGN_LEVELS = ['gtee_high', 'gtee', 'gtee_low', 'promo', 'backfill_promo']


class AdGroupIndexHandler(RequestHandler):

    def get(self):

        # Set up the date range
        num_days = 90
        today = datetime.datetime.now(Pacific_tzinfo()).date()

        days = date_magic.gen_days(today - datetime.timedelta(days=num_days), today)

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        campaigns = CampaignQueryManager.get_campaigns_by_types(self.account, CAMPAIGN_LEVELS)

        # Get a list of adgroups (for sorting), and get a list of each adunit
        # and attach them to each adgroup
        adgroups = []
        adunits_dict = {}
        for campaign in campaigns:
            for adgroup in campaign.adgroups:
                if not (adgroup.archived or adgroup.deleted):
                    adunits = []
                    adunit_keys_to_fetch = []
                    adgroup.targeted_app_keys = []
                    adunit_keys = [adunit_key for adunit_key in adgroup.site_keys]
                    for adunit_key in adunit_keys:
                        if adunit_key in adunits_dict:
                            adunits.append(adunits_dict[adunit_key])
                        else:
                            adunit_keys_to_fetch.append(adunit_key)

                    if adunit_keys_to_fetch:
                        adunits += AdUnitQueryManager.get(adunit_keys_to_fetch)

                    for adunit in adunits:
                        adunits_dict[adunit.key()] = adunit
                        if adunit:
                            adgroup.targeted_app_keys.append(adunit._app_key)

                    adgroups.append(adgroup)

        promo_adgroups, gtee_adgroups, backfill_promo_adgroups = _sort_campaigns(adgroups)

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


def _sort_campaigns(adgroups):
    """
    Helper for the adgroup_index page which probably could be refactored
    """
    promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['promo'], adgroups)
    promo_campaigns = sorted(promo_campaigns, lambda x, y: cmp(y.bid, x.bid))

    guaranteed_campaigns = filter(lambda x: x.campaign.campaign_type in ['gtee_high', 'gtee_low', 'gtee'], adgroups)
    guaranteed_campaigns = sorted(guaranteed_campaigns, lambda x, y: cmp(y.bid, x.bid))

    backfill_promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_promo'], adgroups)
    backfill_promo_campaigns = sorted(backfill_promo_campaigns, lambda x, y: cmp(y.bid, x.bid))

    return [
        promo_campaigns,
        guaranteed_campaigns,
        backfill_promo_campaigns,
    ]


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


class CreateCampaignAndAdGroupHandler(RequestHandler):
    """ Replaces CreateCampaignAJAXHandler and CreateCampaignHandler """

    def get(self):
        campaign_form = CampaignForm()
        adgroup_form = AdGroupForm(is_staff=self.request.user.is_staff)
        account_network_config_form = AccountNetworkConfigForm(instance=self.account.network_config)

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        for app in apps:
            app.network_config_form = AppNetworkConfigForm(instance=app.network_config, prefix="app_%s" % app.key())
            app.adunits = []
            for adunit in app.all_adunits:
                adunit.network_config_form = AdUnitNetworkConfigForm(instance=adunit.network_config,
                                                                     prefix="adunit_%s" % adunit.key())
                app.adunits.append(adunit)

        return render_to_response(self.request,
                                  'advertiser/create_campaign_and_adgroup.html',
                                  {
                                      'campaign_form': campaign_form,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form': account_network_config_form,
                                      'apps': apps,
                                  })

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
                            setattr(network_config, network_config_field, self.request.POST.get("app_%s-%s" % (app.key(), network_config_field), ''))
                            AppQueryManager.update_config_and_put(app, network_config)

                        # NetworkConfig for AdUnits
                        if adgroup.network_type in ('admob_native', 'jumptap',
                                                    'millennial_native'):
                            for adunit in adunits:
                                network_config = adunit.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get("adunit_%s-%s" % (adunit.key(), network_config_field), ''))
                                AdUnitQueryManager.update_config_and_put(adunit, network_config)

                            # NetworkConfig for Account
                            if adgroup.network_type == 'jumptap':
                                network_config = self.account.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get('jumptap_pub_id', ''))
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
def create_campaign_and_adgroup(request, *args, **kwargs):
    return CreateCampaignAndAdGroupHandler()(request, *args, **kwargs)


"""
class CreateAdgroupHandler(RequestHandler):
    pass


@login_required
def create_adgroup(request, *args, **kwargs):
    return CreateAdgroupHandler()(request, *args, **kwars)
"""


class EditCampaignAndAdGroupHandler(RequestHandler):
    """ Replaces CreateCampaignHandler """

    def get(self, adgroup_key):
        adgroup = AdGroupQueryManager.get(adgroup_key)

        campaign_form = CampaignForm(instance=adgroup.campaign, initial={'bid': adgroup.bid,
                                                                         'bid_strategy': adgroup.bid_strategy})
        adgroup_form = AdGroupForm(instance=adgroup, is_staff=self.request.user.is_staff)
        account_network_config_form = AccountNetworkConfigForm(instance=self.account.network_config)

        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        for app in apps:
            app.network_config_form = AppNetworkConfigForm(instance=app.network_config,
                                                           prefix="app_%s" % app.key())
            app.adunits = []
            for adunit in app.all_adunits:
                adunit.network_config_form = AdUnitNetworkConfigForm(instance=adunit.network_config,
                                                                     prefix="adunit_%s" % adunit.key())
                app.adunits.append(adunit)

        return render_to_response(self.request,
                                  'advertiser/edit_campaign_and_adgroup.html',
                                  {
                                      'campaign_form': campaign_form,
                                      'adgroup': adgroup,
                                      'adgroup_form': adgroup_form,
                                      'account_network_config_form': account_network_config_form,
                                      'apps': apps,
                                  })

    def post(self, adgroup_key):
        if not self.request.is_ajax():
            raise Http404

        adgroup = AdGroupQueryManager.get(adgroup_key)

        apps = AppQueryManager.get_apps(account=self.account)
        adunits = AdUnitQueryManager.get_adunits(account=self.account)

        campaign_form = CampaignForm(self.request.POST, instance=adgroup.campaign, initial={'bid': adgroup.bid,
                                                                                            'bid_strategy': adgroup.bid_strategy})

        if campaign_form.is_valid():
            campaign = campaign_form.save()

            adgroup_form = AdGroupForm(self.request.POST, instance=adgroup, site_keys=[(unicode(adunit.key()), '') for adunit in adunits], is_staff=self.request.user.is_staff)
            if adgroup_form.is_valid():

                # Delete Cache. We leave this in views.py because we
                # must delete the adunits that the adgroup used to have as well
                if adgroup.site_keys:
                    adunits = AdUnitQueryManager.get(adgroup.site_keys)
                    AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

                adgroup = adgroup_form.save()

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
                            setattr(network_config, network_config_field, self.request.POST.get("app_%s-%s" % (app.key(), network_config_field), ''))
                            AppQueryManager.update_config_and_put(app, network_config)

                        # NetworkConfig for AdUnits
                        if adgroup.network_type in ('admob_native', 'jumptap',
                                                    'millennial_native'):
                            for adunit in adunits:
                                network_config = adunit.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get("adunit_%s-%s" % (adunit.key(), network_config_field), ''))
                                AdUnitQueryManager.update_config_and_put(adunit, network_config)

                            # NetworkConfig for Account
                            if adgroup.network_type == 'jumptap':
                                network_config = self.account.network_config or NetworkConfig()
                                setattr(network_config, network_config_field, self.request.POST.get('jumptap_pub_id', ''))
                                AccountQueryManager.update_config_and_put(self.account, network_config)

                # Delete Cache. We leave this in views.py because we
                # must delete the adunits that the adgroup used to have as well
                if adgroup.site_keys:
                    adunits = AdUnitQueryManager.get(adgroup.site_keys)
                    AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

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
def edit_campaign_and_adgroup(request, *args, **kwargs):
    return EditCampaignAndAdGroupHandler()(request, *args, **kwargs)


"""
class EditCampaignHandler(RequestHandler):
    pass


@login_required
def edit_campaign(request, *args, **kwargs):
    return EditCampaignHandler()(request, *args, **kwargs)


class EditAdGroupHandler(RequestHandler):
    pass


@login_required
def edit_adgroup(request, *args, **kwargs):
    return EditAdGroupHandler()(request, *args, **kwargs)
"""


class AdgroupDetailHandler(RequestHandler):
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
        # Load the ad group
        adgroup = AdGroupQueryManager.get(adgroup_key)

        # Network campaigns have their date range set by the date picker
        # in the page
        if adgroup.campaign.network():
            if self.start_date and self.date_range:
                end_date = self.start_date + datetime.timedelta(int(self.date_range) - 1)
                days = date_magic.gen_days(self.start_date, end_date)
            else:
                days = date_magic.gen_date_range(self.date_range)

        # Direct sold campaigns have a start date, and sometimes an end date.
        # Use those values if they both exist, otherwise set the range from
        # start to start + 90 days
        else:
            today = datetime.datetime.now(Pacific_tzinfo())

            if adgroup.campaign.end_datetime \
               and adgroup.campaign.end_datetime.replace(tzinfo=utc).astimezone(Pacific) < today:
                end_date = adgroup.campaign.end_datetime.replace(tzinfo=utc).astimezone(Pacific)
            else:
                end_date = today

            if adgroup.campaign.start_datetime:
                if adgroup.campaign.start_datetime.replace(tzinfo=utc).astimezone(Pacific) > today:
                    start_date = today
                else:
                    start_date = adgroup.campaign.start_datetime.replace(tzinfo=utc).astimezone(Pacific)
            else:
                start_date = end_date - datetime.timedelta(90)

            days = date_magic.gen_days(start_date, end_date)

        # We want to limit the number of stats we have to fetch.
        # We've determined 90 is a good max.
        if len(days) > 90:
            days = days[len(days) - 90:]

        # We want to display at least 7 days of data
        if len(days) < 7:
            better_end_date = days[-1] + datetime.timedelta(7 - len(days))
            days = date_magic.gen_days(days[0], better_end_date)

        start_date = days[0]
        end_date = days[-1]

        # Show a flash message recommending using reports if selecting more than 30 days
        if self.date_range > 30:
            self.request.flash['message'] = "For showing more than 30 days we recommend using the <a href='%s'>Reports</a> page." % reverse('reports_index')
        else:
            del self.request.flash['message']

        # Load stats
        adgroup.all_stats = StatsModelQueryManager(self.account, offline=self.offline).get_stats_for_days(advertiser=adgroup, days=days)
        adgroup.stats = reduce(lambda x, y: x + y, adgroup.all_stats, StatsModel())
        adgroup.percent_delivered = budget_service.percent_delivered(adgroup.campaign.budget_obj)

        # Load creatives and populate
        creatives = CreativeQueryManager.get_creatives(adgroup=adgroup)
        creatives = list(creatives)
        for c in creatives:
            c.all_stats = StatsModelQueryManager(self.account, offline=self.offline).get_stats_for_days(advertiser=c, days=days)
            c.stats = reduce(lambda x, y: x + y, c.all_stats, StatsModel())
            # TODO: Should fix DB so that format is always there
            if not c.format:
                c.format = "320x50"
            c.size = c.format.partition('x')

        # Load all adunits targeted by this adgroup/camaign
        adunits = AdUnitQueryManager.get_adunits(keys=adgroup.site_keys)
        apps = {}
        for au in adunits:
            app = apps.get(au.app_key.key())
            if not app:
                app = AppQueryManager.get(au.app_key.key())
                app.adunits = [au]
                app.all_stats = StatsModelQueryManager(self.account, offline=self.offline).\
                                        get_stats_for_days(publisher=app,
                                                           advertiser=adgroup,
                                                           days=days)
                app.stats = reduce(lambda x, y: x + y, app.all_stats, StatsModel())
                apps[au.app_key.key()] = app
            else:
                app.adunits += [au]

            stats_manager = StatsModelQueryManager(self.account, offline=self.offline)
            au.all_stats = stats_manager.get_stats_for_days(publisher=au,
                                                            advertiser=adgroup,
                                                            days=days)
            au.stats = reduce(lambda x, y: x + y, au.all_stats, StatsModel())

        # Figure out the top 4 ad units for the graph
        adunits = sorted(adunits, key=lambda adunit: adunit.stats.impression_count, reverse=True)
        graph_adunits = adunits[0:4]
        if len(adunits) > 4:
            graph_adunits[3] = Site(name='Others')
            graph_adunits[3].all_stats = [reduce(lambda x, y: x + y, stats, StatsModel()) for stats in zip(*[au.all_stats for au in adunits[3:]])]

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

        today = None
        yesterday = None

        # Only pass back today/yesterday if the last 2 days in the date range are actually today/yesterday
        if end_date == datetime.datetime.now(Pacific_tzinfo()).date():
            today = reduce(lambda x, y: x + y, [a.all_stats[-1] for a in graph_adunits], StatsModel())
            try:
                yesterday = reduce(lambda x, y: x + y, [a.all_stats[-2] for a in graph_adunits], StatsModel())
            except:
                pass

        message = []
        if adgroup.network_type and not 'custom' in adgroup.network_type and adgroup.network_type != 'iAd':
            # gets rid of _native_ in admob_native_pub_id to become admob_pub_id
            if '_native' in adgroup.network_type:
                adgroup_network_type = adgroup.network_type.replace('_native', '')
            else:
                adgroup_network_type = adgroup.network_type

            if (self.account.network_config \
                and not getattr(self.account.network_config, adgroup_network_type + '_pub_id')) \
                or not self.account.network_config:

                for app in apps.values():
                    if not (app.network_config and
                            getattr(app.network_config, adgroup_network_type + '_pub_id')):

                        for adunit in app.all_adunits:
                            if not (adunit.network_config and
                                    getattr(adunit.network_config, adgroup_network_type + '_pub_id')):
                                message.append("The application " + app.name + " needs to have a <strong>" + adgroup_network_type.title() + " Network ID</strong> in order to serve. Specify a " + adgroup_network_type.title() + " Network ID on <a href=%s>your account's ad network settings</a> page." % reverse("ad_network_settings"))
                                break
        if message == []:
            message = None
        else:
            message = "<br/>".join(message)

        totals = adgroup.stats

        if today and yesterday:
            stats = {
                'revenue': {
                    'today': today.revenue,
                    'yesterday': yesterday.revenue,
                    'total': totals.revenue
                },
                'impressions': {
                    'today': today.impression_count,
                    'yesterday': yesterday.impression_count,
                    'total': totals.impression_count
                },
                'conversions': {
                    'today': today.conversion_count,
                    'yesterday': yesterday.conversion_count,
                    'total': totals.conversion_count
                },
                'ctr': {
                    'today': today.ctr,
                    'yesterday': yesterday.ctr,
                    'total': totals.ctr
                },
            }
        else:
            stats = {
                'revenue': {
                    'total': totals.revenue
                },
                'impressions': {
                    'total': totals.impression_count
                },
                'conversions': {
                    'total': totals.conversion_count
                },
                'ctr': {
                    'total': totals.ctr
                },
            }

        return render_to_response(self.request,
                                  'advertiser/adgroup.html',
                                  {
                                      'campaign': adgroup.campaign,
                                      'apps': apps.values(),
                                      'adgroup': adgroup,
                                      'adgroup_key': adgroup_key,
                                      'creatives': creatives,
                                      #'stats': stats,
                                      'today': today,
                                      'yesterday': yesterday,
                                      'totals': totals,
                                      'graph_adunits': graph_adunits,
                                      'start_date': days[0],
                                      'end_date': days[-1],
                                      'date_range': len(days),
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
def campaign_adgroup_show(request, *args, **kwargs):
    return AdgroupDetailHandler(id='adgroup_key')(request, use_cache=False, *args, **kwargs)


class PauseAdGroupHandler(RequestHandler):
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
    def post(self):
        action = self.request.POST.get("action", "pause")
        update_objs = []
        adgroups = []
        update_creatives = []
        ids = self.request.POST.getlist('id') or []
        if ids:
            adgroups = AdGroupQueryManager.get(ids)
        for a in adgroups:
            if a != None and a.campaign.account == self.account:
                if action == "pause":
                    a.active = False
                    a.campaign.active = False
                    a.deleted = False
                    a.campaign.deleted = False
                    a.archived = False
                    update_objs.append(a)
                elif action == "resume":
                    a.active = True
                    a.campaign.active = True
                    a.deleted = False
                    a.campaign.deleted = False
                    a.archived = False
                    update_objs.append(a)
                elif action == "activate":
                    a.active = True
                    a.campaign.active = True
                    a.deleted = False
                    a.campaign.deleted = False
                    a.archived = False
                    update_objs.append(a)
                    self.request.flash["message"] = "A campaign has been activated. View it within <a href='%s'>active campaigns</a>." % reverse('advertiser_campaign')
                elif action == "archive":
                    a.active = False
                    a.campaign.active = False
                    a.deleted = False
                    a.campaign.deleted = False
                    a.archived = True
                    update_objs.append(a)
                    self.request.flash["message"] = "A campaign has been archived. View it within <a href='%s'>archived campaigns</a>." % reverse('advertiser_archive')
                elif action == "delete":
                    a.active = False
                    a.campaign.active = False
                    a.deleted = True
                    a.campaign.deleted = True
                    a.archived = False
                    update_objs.append(a)
                    self.request.flash["message"] = "Your campaign has been successfully deleted"
                    for creative in a.creatives:
                        creative.deleted = True
                        update_creatives.append(creative)

        if update_objs:
            AdGroupQueryManager.put(update_objs)
            camp_objs = []
            for adgroup in update_objs:
                camp_objs.append(adgroup.campaign)

            CampaignQueryManager.put(camp_objs)

        if update_creatives:
            CreativeQueryManager.put(update_creatives)

        return HttpResponseRedirect(self.request.META["HTTP_REFERER"])


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
            logging.error('base_creative_form is_valid')
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
                logging.error('creative_form is_valid')

                if not creative_form.instance:  # ensure form posts do not change ownership
                    account = self.account
                else:
                    account = creative_form.instance.account
                creative = creative_form.save(commit=False)
                creative.account = account
                creative.ad_group = ad_group
                CreativeQueryManager.put(creative)
                logging.error('put')

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
