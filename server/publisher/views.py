"""
Views that handle pages for Apps and AdUnits.
"""

import logging
import datetime

import urllib
# hack to get urllib to work on snow leopard
urllib.getproxies_macosx_sysconf = lambda: {}

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, \
     render_to_string, \
     HttpResponse, \
     JSONResponse

## Models
from advertiser.models import Campaign, \
        AdGroup, \
        HtmlCreative, \
        NetworkStates
from publisher.models import Site
from publisher.forms import AppForm, AdUnitForm
from reporting.models import StatsModel, GEO_COUNTS
from account.models import NetworkConfig

## Query Managers
from account.query_managers import AccountQueryManager
from ad_network_reports.query_managers import (AdNetworkMapperManager,
                                               AdNetworkLoginManager)
from advertiser.query_managers import (AdvertiserQueryManager,
                                       CampaignQueryManager,
                                       AdGroupQueryManager,
                                       CreativeQueryManager)
from publisher.query_managers import (PublisherQueryManager, AppQueryManager,
                                      AdUnitQueryManager)
from reporting.query_managers import StatsModelQueryManager

# Util
from common.utils import sswriter, date_magic, xlwt
from common.utils.unicode_writer import UnicodeWriter
from common.utils.helpers import app_stats
from common.utils.request_handler import RequestHandler
#REFACTOR: only import what we need here
from common.constants import *
from common.utils.stats_helpers import (MarketplaceStatsFetcher,
                                        MPStatsAPIException,
                                        SummedStatsFetcher)

from budget import budget_service


class DashboardHandler(RequestHandler):
    def get(self):
        names = {
            'direct': 'Direct Sold',
            'mpx': 'Marketplace',
            'network': 'Ad Networks',
        }

        for key, campaign in AdvertiserQueryManager.get_campaigns_dict_for_account(account=self.account, include_deleted=True).items():
            names[key] = campaign.name

        for key, app in PublisherQueryManager.get_apps_dict_for_account(account=self.account, include_deleted=True).items():
            names[key] = app.name

        for key, adunit in PublisherQueryManager.get_adunits_dict_for_account(account=self.account, include_deleted=True).items():
            names[key] = adunit.name

        return {
            'page_width': 'wide',
            'names': names,
        }


@login_required
def dashboard(request, *args, **kwargs):
    handler = DashboardHandler(template="publisher/dashboard.html")
    return handler(request, use_cache=False, use_handshake=True, *args, **kwargs)


class AppIndexHandler(RequestHandler):
    """
    A list of apps and their real-time stats.
    """
    def get(self):
        # Get all of the account's apps.
        apps_dict = PublisherQueryManager.get_objects_dict_for_account(self.account)
        app_keys = simplejson.dumps([str(key) for key in apps_dict.keys()])
        sorted_apps = sorted(apps_dict.values(), lambda x, y: cmp(x.name, y.name))

        # If there are no apps, redirect to the app creation form.
        if len(apps_dict) == 0:
            return HttpResponseRedirect(reverse('publisher_create_app'))

        # account_stats property is a string because it is a json dump.
        response_dict = {
            'apps': sorted_apps,
            'app_keys': app_keys,
            'account_stats': "{}",
            'stats': {},
        }

        # If there are a lot of apps, don't fetch stats here because it could
        # result in a DeadlineExceededError.
        if len(apps_dict) > 50:
            return response_dict

        # Get stats totals for the stats breakdown pane
        account_stats_manager = StatsModelQueryManager(
                self.account, offline=self.offline)
        stats_model_list = account_stats_manager.get_stats_for_days(
                days=self.days)

        stats_dict = self._build_stats_dict_from_stats_model_list(
                stats_model_list)
        today_and_yesterday_stats = self._build_today_and_yesterday_stats_from_stats_model_list(stats_model_list)

        account_stats = {'status': 200, 'all_stats': stats_dict}

        response_dict['account_stats'] = simplejson.dumps(account_stats)
        response_dict['stats'] = today_and_yesterday_stats

        return response_dict

    def _build_stats_dict_from_stats_model_list(self, stats_model_list):
        """
        Given stats_model_list, generate the appropriate data structure for
        graphing the data using Highcharts.
        """

        # REFACTOR: StatsModel field naming
        stats_dict_list = []
        for stats_model in stats_model_list:
            stats_dict_list.append({
                'req': stats_model.request_count,
                'imp': stats_model.impression_count,
                'clk': stats_model.click_count,
                'usr': stats_model.user_count,
            })

        summed_stats_model = sum(stats_model_list, StatsModel())

        # The key '||' references the aggregate total across the entire
        # account (i.e. all apps and adunits)
        stats_dict = {
            '||': {
                'name': '||',
                'daily_stats': stats_dict_list,
                'sum': summed_stats_model.to_dict(),
            }
        }

        return stats_dict

    def _build_today_and_yesterday_stats_from_stats_model_list(self, stats_model_list):
        """
        Given stats_model_list, generate the appropriate data structure for
        displaying the stats breakdown.  Note: for a custom date range, this
        actually returns data for the final two days.
        """

        summed_stats_model = sum(stats_model_list, StatsModel())

        # This is the max active users over the date range, not total
        # unique users.
        summed_stats_model.user_count = max([stats_model.user_count for stats_model in stats_model_list])

        today = stats_model_list[-1]
        try:
            yesterday = stats_model_list[-2]
        except IndexError:
            # If there is only one date given, set yesterday to a blank
            # StatsModel with default values.
            yesterday = StatsModel()

        today_and_yesterday_stats = {
            'req': {
                'today': today.request_count,
                'yesterday': yesterday.request_count,
                'total': summed_stats_model.request_count,
            },
            'imp': {
                'today': today.impression_count,
                'yesterday': yesterday.impression_count,
                'total': summed_stats_model.impression_count,
            },
            'users': {
                'today': today.user_count,
                'yesterday': yesterday.user_count,
                'total': summed_stats_model.user_count
            },
            'ctr': {
                'today': today.ctr,
                'yesterday': yesterday.ctr,
                'total': summed_stats_model.ctr
            },
            'clk': {
                'today': today.click_count,
                'yesterday': yesterday.click_count,
                'total': summed_stats_model.click_count
            },
        }

        return today_and_yesterday_stats


@login_required
def app_index(request, *args, **kwargs):
    handler = AppIndexHandler(template='publisher/app_index.html')
    return handler(request, use_cache=False, *args, **kwargs)


class GeoPerformanceHandler(RequestHandler):
    """
    App performance stats broken down by geography.
    """
    def get(self):

        now = datetime.datetime.now()

        apps = AppQueryManager.get_apps(self.account)

        if len(apps) == 0:
            return HttpResponseRedirect(reverse('publisher_create_app'))

        geo_dict = {}
        totals = StatsModel(date=now) # sum across all days and countries

        # hydrate geo count dicts with stats counts on account level
        account_stats_mgr = StatsModelQueryManager(self.account,
                                                   self.offline,
                                                   include_geo=True)
        all_stats = account_stats_mgr.get_stats_for_days(days=self.days, use_mongo=False)

        for stats in all_stats:
            totals = totals + StatsModel(request_count=stats.request_count,
                                         impression_count=stats.impression_count,
                                         click_count=stats.click_count,
                                         user_count=stats.user_count,
                                         date=now)
            countries = stats.get_countries()
            for c in countries:
                country_info = geo_dict.get(c, StatsModel(country=c, date=now))
                geo_counts_0 = stats.get_geo(c, GEO_COUNTS[0])
                geo_counts_2 = stats.get_geo(c, GEO_COUNTS[2])
                country_stats = StatsModel(country=c,
                                           request_count = geo_counts_0,
                                           impression_count = geo_counts_0,
                                           click_count = geo_counts_2,
                                           date = now)
                geo_dict[c] =  country_info + country_stats

        # creates a sorted table based on request count
        geo_table = []
        keys = geo_dict.keys()
        keys.sort(lambda x,y: cmp(geo_dict[y].request_count, geo_dict[x].request_count))
        for k in keys:
            geo_table.append((k, geo_dict[k]))

        return render_to_response(self.request,
                                  'publisher/geo_performance.html',
                                  {
                                      'geo_dict': geo_dict,
                                      'geo_table': geo_table,
                                      'totals' : totals,
                                      'date_range': self.date_range,
                                      'account': self.account
                                  })


@login_required
def geo_performance(request, *args, **kwargs):
    return GeoPerformanceHandler()(request, *args, **kwargs)


class CreateAppHandler(RequestHandler):
    """
    REFACTOR

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
    def get(self, app_form=None, adunit_form=None, reg_complete=None):

        # create the forms
        app_form = app_form or AppForm()
        adunit_form = adunit_form or AdUnitForm(prefix="adunit")

        # REFACTOR
        # attach on registration related parameters to the account for template
        if reg_complete:
            self.account.reg_complete = 1

        return {
            "app_form": app_form,
            "adunit_form": adunit_form
        }

    def post(self):
        app = None
        if self.request.POST.get("app_key"):
            app = AppQueryManager.get(self.request.POST.get("app_key"))
            app_form = AppForm(data = self.request.POST,
                               files = self.request.FILES,
                               instance=app)
        else:
            app_form = AppForm(data = self.request.POST, files = self.request.FILES)

        adunit_form = AdUnitForm(data = self.request.POST, prefix = "adunit")
        if app_form.is_valid():
            if not app_form.instance: #ensure form posts do not change ownership
                account = self.account  # attach account info
            else:
                account = app_form.instance.account
            app = app_form.save(commit=False)
            app.account = account

        if adunit_form.is_valid():
            if not adunit_form.instance: #ensure form posts do not change ownership
                account = self.account
            else:
                account = adunit_form.instance.account
            adunit = adunit_form.save(commit=False)
            adunit.account = account

            # update the database
            AppQueryManager.put(app)

            create_iad_mapper(self.account, app)

            adunit.app_key = app
            AdUnitQueryManager.put(adunit)

            # see if we need to enable the marketplace or network campaigns
            enable_marketplace(adunit, self.account)
            enable_networks(adunit, self.account)

            # Check if this is the first ad unit for this account
            if len(AdUnitQueryManager.get_adunits(account=self.account, limit=2)) == 1:
                add_demo_campaign(adunit)
            # Check if this is the first app for this account
            status = "success"
            if self.account.status == "new":
                self.account.status = "step4"
                # skip to step 4 (add campaigns), but show step 2 (integrate)
                # TODO (Tiago): add the itunes info here for iOS apps for iAd syncing
                network_config = NetworkConfig(account=self.account)
                AccountQueryManager.update_config_and_put(account, network_config)

                # create the marketplace account for the first time
                mpx = CampaignQueryManager.get_marketplace(self.account)
                mpx.active = False
                CampaignQueryManager.put(mpx)

                status = "welcome"

            # Redirect to the code snippet page
            publisher_integration_url = reverse('publisher_integration_help',
                                                kwargs = {
                                                    'adunit_key': adunit.key()
                                                })
            publisher_integration_url = publisher_integration_url + '?status=' + status
            return HttpResponseRedirect(publisher_integration_url)

        return render_to_response(self.request, self.template, {
            'app_form': app_form,
            'adunit_form': adunit_form
        })


@login_required
def create_app(request, *args, **kwargs):
    handler = CreateAppHandler(template='publisher/create_app.html')
    return handler(request, *args, **kwargs)


class AppDetailHandler(RequestHandler):
    """
    REFACTOR

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
    def get(self, app_key):

        # load the site
        # 1 GET
        app = AppQueryManager.get(app_key)

        # create a stats manager
        stats_q = StatsModelQueryManager(self.account, self.offline)
        mpx_stats_q = MarketplaceStatsFetcher(self.account.key())

        # 1 RunQuery
        app.adunits = AdUnitQueryManager.get_adunits(app=app)

        # organize impressions by days
        # 1 GET per ad unit
        if len(app.adunits) > 0:
            for adunit in app.adunits:
                adunit.all_stats = stats_q.get_stats_for_days(publisher=adunit,
                                                                    days=self.days)
                adunit.stats = reduce(lambda x, y: x+y,
                                      adunit.all_stats,
                                      StatsModel())

        app.adunits = sorted(app.adunits,
                             key=lambda adunit: adunit.name,
                             reverse=True)

        # 1 GET
        app.all_stats = stats_q.get_stats_for_days(publisher=app, days=self.days)

        help_text = 'Create an Ad Unit below' if len(app.adunits) == 0 else None


        # In the graph, only show the top 3 ad units and
        # bundle the rest if there are more than 4
        app.graph_adunits = app.adunits[0:4]
        if len(app.adunits) > 4:
            app.graph_adunits[3] = Site(name='Others')
            bundled_adunits = zip(*[adunit.all_stats for adunit in app.adunits[3:]])
            app.graph_adunits[3].all_stats = [reduce(lambda x, y: x+y,
                                                     stats,
                                                     StatsModel()) \
                                              for stats in bundled_adunits]

        # Create edit form and new adunit forms
        # 1 memcache GET
        app_form_fragment = AppUpdateAJAXHandler(self.request).get(app=app)
        # 1 memcache GET
        adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(app=app)

        today = app.all_stats[-1]
        try:
            yesterday = app.all_stats[-2]
        except IndexError:
            yesterday = StatsModel()

        app.stats = reduce(lambda x, y: x+y, app.all_stats, StatsModel())

        # this is the max active users over the date range
        # NOT total unique users
        app.stats.user_count = max([sm.user_count for sm in app.all_stats])

        # get adgroups targeting this app
        # 2 RunQuery???
        adgroups = AdGroupQueryManager.get_adgroups(app=app)
        # Total: 2 GETs / 1 urlfetch per adgroup
        # 1 GET for the campaign per adgroup
        app_adunits = set([adunit.key() for adunit in app.adunits])
        def targeted(adgroup):
            # If it's a new network campaign the adgroup must be targeted and
            # active
            if adgroup.campaign.network_type:
                return set(adgroup.site_keys).intersection(app_adunits) and \
                        adgroup.active
            # Otherwiese the adgroup must be targeted
            else:
                return set(adgroup.site_keys).intersection(app_adunits)

        app.campaigns = dict([(adgroup._campaign, adgroup.campaign) for
            adgroup in adgroups if targeted(adgroup)]).values()

        for campaign in app.campaigns:
            # Used for non new network campaigns
            if not campaign.network_type:
                campaign.adgroup = campaign.adgroups[0]

            # 1 GET
            summed_fetcher = SummedStatsFetcher(self.account.key())
            campaign.stats =  summed_fetcher.get_campaign_specific_app_stats(
                    app.key(), campaign, self.start_date, self.end_date)
            #budget_object = campaign.budget_obj
            #campaign.percent_delivered = budget_service.percent_delivered(
                    #budget_object)

            # Overwrite the revenue from MPX if its marketplace
            # TODO: overwrite clicks as well
            if campaign.campaign_type in ['marketplace']:
                try:
                    # 1 urlfetch
                    mpx_stats = mpx_stats_q.get_app_stats(str(app_key),
                                                            self.start_date,
                                                            self.end_date)
                except MPStatsAPIException, error:
                    logging.warning("MPStatsAPIException: %s" % error)
                    mpx_stats = {}

                campaign.stats['rev'] = float(mpx_stats.get('rev', 0.0))
                campaign.stats['imp'] = int(mpx_stats.get('imp', 0))

            if campaign.campaign_type in ['network', 'gtee_high', 'gtee',
                    'gtee_low', 'promo'] and getattr(campaign, 'cpc', False):
                campaign.calculated_ecpm = calculate_ecpm(campaign)


        # Sort out all of the campaigns that are targeting this app
        promo_campaigns = filter_campaigns(app.campaigns, ['promo'])
        guarantee_campaigns = filter_campaigns(app.campaigns, ['gtee_high', 'gtee_low', 'gtee'])
        marketplace_campaigns = filter_campaigns(app.campaigns, ['marketplace'])
        network_campaigns = filter_campaigns(app.campaigns, ['network'])
        backfill_promo_campaigns = filter_campaigns(app.campaigns, ['backfill_promo'])

        levels = ('high', '', 'low')
        gtee_str = "gtee_%s"
        gtee_levels = []
        for level in levels:
            this_level = gtee_str % level if level else "gtee"
            name = level if level else 'normal'
            level_camps = filter(lambda x:x.campaign_type == this_level,
                                 guarantee_campaigns)
            gtee_levels.append(dict(name = name, campaigns = level_camps))

        # we don't include network or promo campaigns in the revenue totals

        # Figure out if the marketplace is activated and if it has any
        # activated adgroups so we can mark it as active/inactive
        active_mpx_adunit_exists = any([adgroup.active and (not adgroup.deleted)
                                        for adgroup in filter_campaigns(
                                            adgroups, ['marketplace'])])

        try:
            marketplace_activated = marketplace_campaigns[0].active
        except IndexError:
            marketplace_activated = False

        return {
            'app': app,
            'app_form_fragment':app_form_fragment,
            'adunit_form_fragment':adunit_form_fragment,
            'start_date': self.days[0],
            'end_date': self.days[-1],
            'date_range': self.date_range,
            'today': today,
            'yesterday': yesterday,
            'account': self.account,
            'helptext': help_text,
            'gtee': gtee_levels,
            'promo': promo_campaigns,
            'marketplace': marketplace_campaigns,
            'marketplace_activated': marketplace_activated,
            'active_mpx_adunit_exists': active_mpx_adunit_exists,
            'network': network_campaigns,
            'backfill_promo': backfill_promo_campaigns,
        }


@login_required
def app_detail(request, *args, **kwargs):
    handler = AppDetailHandler(id="app_key", template='publisher/app.html')
    return handler(request, use_cache=False, *args, **kwargs)


class ExportFileHandler(RequestHandler):
    def get(self, key, key_type, f_type):
        spec = self.params.get('spec')
        stat_names, stat_models = self.get_desired_stats(key, key_type,
                                                         self.days, spec=spec)
        return sswriter.write_stats( f_type, stat_names,
                                     stat_models, site=key,
                                     days=self.days, key_type=key_type)


    def get_desired_stats(self, key, key_type, days, spec=None):
        manager = StatsModelQueryManager(self.account, offline=self.offline)
        """ Given a key, key_type, and specificity, return
        the appropriate stats to get AND their names"""
        #default for all
        stat_names = (IMP_STAT, CLK_STAT, CTR_STAT)
        #sanity check
        assert key_type in ('adunit', 'app', 'adgroup', 'account')
        if spec:
            assert spec in ('creatives', 'adunits', 'campaigns', 'days', 'apps')



        #Set up attr getters/names
        if key_type == 'app' or (key_type == 'account' and spec == 'apps') or \
                (key_type == 'adunit' and spec == 'days'):
            stat_names = (REQ_STAT,) + stat_names
            if spec == 'days':
                stat_names = (DTE_STAT,) + stat_names
        elif key_type == 'account' and spec == 'campaigns':
            stat_names += (CPM_STAT, CNV_RATE_STAT, CPA_STAT)
        elif key_type == 'adgroup':
            if spec == 'days':
                stat_names = (DTE_STAT,) + stat_names
            stat_names += (REV_STAT, CNV_RATE_STAT, CPA_STAT)
        elif key_type == 'adunit' and spec == 'campaigns':
            stat_names += (REV_STAT,)



        #General rollups for all data
        if key_type == 'account':
            if spec == 'apps':
                apps = AppQueryManager.get_apps(self.account)
                if len(apps) == 0:
                    #should probably handle this more gracefully
                    logging.warning("Apps for account is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(publisher=a, days=self.days) for a in apps])
            elif spec == 'campaigns':
                camps = CampaignQueryManager.get_campaigns(account=self.account)
                if len(camps) == 0:
                    logging.warning("Campaigns for account is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=c, days=self.days) for c in camps])
        #Rollups for adgroup data
        elif key_type == 'adgroup':
            if spec == 'creatives':
                creatives = list(CreativeQueryManager.get_creatives(adgroup=key))
                if len(creatives) == 0:
                    logging.warning("Creatives for adgroup is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=c, days=self.days) for c in creatives])
            if spec == 'adunits':
                adunits = map(lambda x: Site.get(x), AdGroupQueryManager.get(key).site_keys)
                if len(adunits) == 0:
                    logging.warning("Adunits for adgroup is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=key, publisher=a, days=self.days) for a in adunits])
            if spec == 'days':
                return (stat_names, manager.get_stats_for_days(advertiser=key, days=self.days))
        #Rollups + not-rollup for adunit data
        elif key_type == 'adunit':
            if spec == 'campaigns':
                adgroups = AdGroupQueryManager.get_adgroups(adunit=key)
                if len(adgroups) == 0:
                    logging.warning("Campaigns for adunit is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(publisher=key, advertiser=a, days=self.days) for a in adgroups])
            if spec == 'days':
                return (stat_names, manager.get_stats_for_days(publisher=key, days=self.days))
        #App adunit rollup data
        elif key_type == 'app':
            adunits = AdUnitQueryManager.get_adunits(app=key)
            if len(adunits) == 0:
                logging.warning("Apps is empty")
            return (stat_name, [manager.get_stat_rollup_for_days(publisher=a, days=self.days) for a in adunits])


@login_required
def export_file(request, *args, **kwargs):
    return ExportFileHandler()(request, *args, **kwargs)


class AdUnitShowHandler(RequestHandler):
    """
    REFACTOR

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

    def get(self, adunit_key):
        # load the site
        adunit = AdUnitQueryManager.get(adunit_key)

        if adunit.account.key() != self.account.key():
            raise Http404

        stats_manager = StatsModelQueryManager(self.account, offline=self.offline)
        adunit.all_stats = stats_manager.get_stats_for_days(publisher=adunit,
                                                            days=self.days)

        adunit.stats = reduce(lambda x, y: x+y,
                              adunit.all_stats,
                              StatsModel())

        # used the get marketplace stats from mpx servers
        stats_fetcher = MarketplaceStatsFetcher(self.account.key())

        # Get all of the ad groups for this site
        adunit.adgroups = AdGroupQueryManager.get_adgroups(adunit=adunit)
        adunit.adgroups = sorted(adunit.adgroups, lambda x,y: cmp(y.bid, x.bid))
        for ag in adunit.adgroups:
            campaign = ag.campaign
            # If its a new network campaign that has been migrated and the
            # transition date is after the start date
            if campaign.campaign_type == 'network' and campaign.network_state == \
                    NetworkStates.DEFAULT_NETWORK_CAMPAIGN and \
                    campaign.old_campaign and self.start_date <= \
                    campaign.transition_date:
                new_stats = None
                if self.end_date >= campaign.transition_date:
                    # get new campaign stats (specific for the single adgroup)
                    days = date_magic.gen_days(campaign.transition_date,
                            self.end_date)
                    new_stats = stats_manager.get_stats_for_days(
                            publisher=adunit, advertiser=ag,
                            days=days)
                    days = date_magic.gen_days(self.start_date,
                            campaign.transition_date)
                else:
                    # getting only legacy campaign stats (back when campaign
                    # and adgroup were one to one)
                    days = self.days
                # get old campaign stats
                old_stats = stats_manager.get_stats_for_days(publisher=adunit,
                        advertiser=campaign.old_campaign, days=days)
                if new_stats:
                    transition_stats = old_stats[-1] + new_stats[0]
                    ag.all_stats = old_stats[:-1] + [transition_stats] + \
                            new_stats[1:]
                else:
                    ag.all_stats = old_stats
            else:
                # getting only adgroup stats (back when campaign
                # and adgroup were one to one)
                days = self.days
                ag.all_stats = stats_manager.get_stats_for_days(publisher=adunit,
                        advertiser=ag, days=days)

            ag.stats = reduce(lambda x, y: x+y, ag.all_stats, StatsModel())
            budget_object = campaign.budget_obj
            ag.percent_delivered = budget_service.percent_delivered(budget_object)

            # Overwrite the revenue from MPX if its marketplace
            # TODO: overwrite clicks as well
            if campaign.campaign_type in ['marketplace']:
                try:
                    mpx_stats = stats_fetcher.get_adunit_stats(str(adunit.key()),
                                                               self.start_date,
                                                               self.end_date)
                except MPStatsAPIException, error:
                    logging.warning("MPStatsAPIException: %s" % error)
                    mpx_stats = {}
                ag.stats.revenue = float(mpx_stats.get('rev', 0.0))
                ag.stats.impression_count = int(mpx_stats.get('imp', 0))

            if campaign.campaign_type in ['network', 'gtee_high', 'gtee', 'gtee_low', 'promo']:
                ag.calculated_ecpm = calculate_ecpm(ag)


        # to allow the adunit to be edited
        adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(adunit=adunit)


        # Sort out all of the campaigns that are targeting this app
        promo_campaigns = filter_adgroups(adunit.adgroups, ['promo'])
        guarantee_campaigns = filter_adgroups(adunit.adgroups, ['gtee_high', 'gtee_low', 'gtee'])
        marketplace_campaigns = filter_adgroups(adunit.adgroups, ['marketplace'])
        network_campaigns = filter_adgroups(adunit.adgroups, ['network'])
        backfill_promo_campaigns = filter_adgroups(adunit.adgroups, ['backfill_promo'])

        levels = ('high', '', 'low')
        gtee_str = "gtee_%s"
        gtee_levels = []
        for level in levels:
            this_level = gtee_str % level if level else "gtee"
            name = level if level else 'normal'
            level_camps = filter(lambda x:x.campaign.campaign_type == this_level,
                                 guarantee_campaigns)
            gtee_levels.append(dict(name = name, adgroups = level_camps))


        try:
            marketplace_activated = marketplace_campaigns[0].campaign.active
        except IndexError:
            marketplace_activated = False

        today = adunit.all_stats[-1]
        try:
            yesterday = adunit.all_stats[-2]
        except:
            yesterday = StatsModel()

        # write response
        return render_to_response(self.request,
                                  'publisher/adunit.html',
                                  {
                                      'site': adunit,
                                      'adunit': adunit,
                                      'today': today,
                                      'yesterday': yesterday,
                                      'start_date': self.days[0],
                                      'end_date': self.days[-1],
                                      'date_range': self.date_range,
                                      'account': self.account,
                                      'days': self.days,
                                      'adunit_form_fragment': adunit_form_fragment,
                                      'gtee': gtee_levels,
                                      'promo': promo_campaigns,
                                      'marketplace': marketplace_campaigns,
                                      'network': network_campaigns,
                                      'backfill_promo': backfill_promo_campaigns,
                                      'marketplace_activated': marketplace_activated
                                  })


@login_required
def adunit_show(request, *args, **kwargs):
    return AdUnitShowHandler(id='adunit_key')(request, use_cache=False, *args, **kwargs)


class AppUpdateAJAXHandler(RequestHandler):
    """
    REFACTOR

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
    TEMPLATE  = 'publisher/forms/app_form.html'
    def get(self,app_form=None,app=None):
        app_form = app_form or AppForm(instance=app, is_edit_form=True)
        app_form.is_edit_form = True
        return self.render(form=app_form)

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request,
                                template_name = template_name,
                                data = kwargs)

    def json_response(self,json_dict):
        return JSONResponse(json_dict)

    def post(self,app_key=None):
        logging.error(self.request.POST)
        logging.error(self.request.FILES)

        app_key = app_key or self.request.POST.get('app_key')
        if app_key:
            app = AppQueryManager.get(app_key)
        else:
            app = None

        app_form = AppForm(data = self.request.POST,
                           files = self.request.FILES,
                           instance = app,
                           is_edit_form = True)

        json_dict = {'success':False,'errors':[]}
        if app_form.is_valid():
            if not app_form.instance: #ensure form posts do not change ownership
                account = self.account
            else:
                account = app_form.instance.account
            app = app_form.save(commit=False)
            app.account = account

            AppQueryManager.put(app)

            create_iad_mapper(self.account, app)

            json_dict.update(success=True)

            return self.json_response(json_dict)

        flatten_errors = lambda frm : [(k, unicode(v[0])) for k, v in frm.errors.items()]
        grouped_errors = flatten_errors(app_form)

        json_dict.update(success = False, errors = grouped_errors)
        return self.json_response(json_dict)


@login_required
def app_update_ajax(request, *args, **kwargs):
    handler = AppUpdateAJAXHandler(id='app_key')
    return handler(request, *args, **kwargs)


class AdUnitUpdateAJAXHandler(RequestHandler):
    """
    REFACTOR

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

    TEMPLATE = 'publisher/forms/adunit_form.html'

    def get(self, adunit_form=None, adunit=None, app=None):
        initial = {}
        if app:
            initial.update(app_key=app.key())
        adunit_form = adunit_form or AdUnitForm(instance=adunit,
                                                initial=initial,
                                                prefix="adunit")
        return self.render(form=adunit_form)

    def render(self, template=None, **kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request,
                                template_name=template_name,
                                data=kwargs)

    def json_response(self, json_dict):
        return JSONResponse(json_dict)

    def post(self, adunit_key=None):
        logging.error(self.request.POST)
        logging.error(self.request.FILES)

        adunit_key = adunit_key or self.request.POST.get('adunit_key')
        if adunit_key:
            # Note this gets things from the cache ?
            adunit = AdUnitQueryManager.get(adunit_key)
        else:
            adunit = None

        adunit_form = AdUnitForm(data=self.request.POST,
                                 instance=adunit,
                                 prefix="adunit")
        json_dict = {'success': False, 'errors': []}

        if adunit_form.is_valid():
            #ensure form posts do not change ownership
            if not adunit_form.instance:
                account = self.account
            else:
                account = adunit_form.instance.account

            adunit = adunit_form.save(commit=False)
            adunit.account = account
            AdUnitQueryManager.put(adunit)

            # If the adunit already exists we don't need to enable the
            # marketplace or networks
            if not adunit_key:
                enable_marketplace(adunit, self.account)
                enable_networks(adunit, self.account)

            json_dict.update(success=True)
            return self.json_response(json_dict)

        flatten_errors = lambda frm : [(k, unicode(v[0])) for k, v in
                frm.errors.items()]
        grouped_errors = flatten_errors(adunit_form)

        json_dict.update(success=False, errors=grouped_errors)
        return self.json_response(json_dict)


def adunit_update_ajax(request, *args, **kwargs):
    return AdUnitUpdateAJAXHandler()(request, *args, **kwargs)


class DeleteAdUnitHandler(RequestHandler):
    """
    Deletes an adunit and redirects to the adunit's app.
    """
    def post(self, adunit_key):
        logging.error(self.request.POST)
        a = AdUnitQueryManager.get(adunit_key)
        if a != None and a.app_key.account == self.account:
            a.deleted = True
            AdUnitQueryManager.put(a)

        return HttpResponseRedirect(reverse('publisher_app_show',
                                            kwargs = {
                                                'app_key': a.app.key()
                                            }))


@login_required
def delete_adunit(request, *args, **kwargs):
    return DeleteAdUnitHandler()(request, *args, **kwargs)


class DeleteAppHandler(RequestHandler):
    """
    Deletes an app and redirects to the app index.
    """
    def post(self, app_key):
        logging.error(self.request.POST)
        app = AppQueryManager.get(app_key)
        adunits = AdUnitQueryManager.get_adunits(app=app)
        if app and app.account == self.account:
            app.deleted = True
            # also "delete" all the adunits associated with the app
            for adunit in adunits:
                adunit.deleted = True
            AppQueryManager.put(app)
            AdUnitQueryManager.put(adunits)

        return HttpResponseRedirect(reverse('app_index'))


@login_required
def delete_app(request, *args, **kwargs):
    return DeleteAppHandler()(request, *args, **kwargs)


class IntegrationHelpHandler(RequestHandler):
    """
    This page displays some helpful information that helps pubs get
    their apps integrated. Pubs land on this page after they've
    created a new adunit.
    """
    def get(self,adunit_key):
        adunit = AdUnitQueryManager.get(adunit_key)
        status = self.params.get('status')
        return render_to_response(self.request,
                                  'publisher/integration_help.html',
                                  {
                                      'site': adunit,
                                      'status': status,
                                      'width': adunit.get_width(),
                                      'height': adunit.get_height(),
                                      'account': self.account
                                  })


@login_required
def integration_help(request, *args, **kwargs):
    return IntegrationHelpHandler()(request, *args, **kwargs)


class AppExportHandler(RequestHandler):
    """
    REFACTOR

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
    def post(self, app_key, file_type, start, end):
        start = datetime.datetime.strptime(start,'%m%d%y')
        end = datetime.datetime.strptime(end,'%m%d%y')
        days = date_magic.gen_days(start, end)

        app = AppQueryManager.get(app_key)

        stats_manager = StatsModelQueryManager(self.account, offline=self.offline)
        all_stats = stats_manager.get_stats_for_days(publisher=app, days=days)
        f_name_dict = dict(app_title = app.name,
                           start = start.strftime('%b %d'),
                           end   = end.strftime('%b %d, %Y'),
                           )

        f_name = "%(app_title)s AppStats,  %(start)s - %(end)s" % f_name_dict
        f_name = f_name.encode('ascii', 'ignore')
        data = map(lambda x: [x[0]] + x[1],
                   zip([day.strftime('%a, %b %d, %Y') for day in days],
                       [app_stats(stat) for stat in all_stats]))
        titles = ['Date', 'Requests', 'Impressions', 'Fill Rate', 'Clicks', 'CTR']
        return sswriter.export_writer(file_type, f_name, titles, data)


@login_required
def app_export(request, *args, **kwargs):
    return AppExportHandler()(request, *args, **kwargs)


class DashboardExportHandler(RequestHandler):
    def post(self, file_type, start, end):
        start = datetime.datetime.strptime(start,'%m%d%y')
        end = datetime.datetime.strptime(end,'%m%d%y')
        days = date_magic.gen_days(start, end)

        data = []

        apps = AppQueryManager.get_apps(self.account)

        stats_fetcher = StatsModelQueryManager(self.account,
                                               offline=self.offline)

        for app in apps:
            if app.app_type=="android":
                resource_id = app.package
            else:
                resource_id = app.url
            if not resource_id:
                resource_id = 'None'
            stats = stats_fetcher.get_stats_for_days(publisher=app,
                                                     days=days)
            summed_stats = sum(stats, StatsModel())
            data.append([app.name,
                         "all",
                         str(app.key()),
                         resource_id] + \
                        app_stats(summed_stats) + \
                        ["N/A",
                         app.type])
            adunits = AdUnitQueryManager.get_adunits(app=app)

            for adunit in adunits:
                if adunit.format != "custom":
                    ad_size = adunit.format
                else:
                    ad_size = "%sx%s" % (adunit.custom_width, adunit.custom_height)
                stats = stats_fetcher.get_stats_for_days(publisher=adunit,
                                                         days=days)
                summed_stats = sum(stats,StatsModel())
                data.append([app.name,
                             adunit.name,
                             str(adunit.key()),
                             resource_id] + \
                            app_stats(summed_stats) +
                            [ad_size,
                             app.type])

        f_name_dict = {
            'start': start.strftime('%b %d'),
            'end': end.strftime('%b %d, %Y'),
        }

        f_name = "DashboardStats,  %(start)s - %(end)s" % f_name_dict
        f_name = f_name.encode('ascii', 'ignore')
        titles = ['App','Ad Unit','Pub ID','Resource ID', 'Requests',
                  'Impressions', 'Fill Rate', 'Clicks', 'CTR','Ad Size',
                  'Platform',]

        return sswriter.export_writer(file_type, f_name, titles, data)


@login_required
def dashboard_export(request, *args, **kwargs):
    return DashboardExportHandler()(request, *args, **kwargs)


class TableExportHandler(RequestHandler):
    def post(self):
        try:
            data = urllib.unquote(self.request.POST['table'])
            data = simplejson.loads(data)
            format = self.request.POST['format']
            filename = urllib.unquote(self.request.POST['filename'])
        except Exception:
            raise Http404

        headers, body = data['headers'], data['body']

        # strip both headers and body cells for leading/trailing whitespace
        headers = [header.replace('<br>',' ').strip() for header in headers]
        body = [[cell.replace('<br>',' ').strip() for cell in row] for row in body]

        if format == 'xls':
            # let's build this spreedsheet using xlwt
            xls = xlwt.Workbook()
            ws = xls.add_sheet('Worksheet')

            # set up a bold style for the header
            bold_style = xlwt.XFStyle()
            font = xlwt.Font()
            font.bold = True
            bold_style.font = font

            # write to spreadsheet
            for column, header in enumerate(headers):
                ws.write(0, column, header, bold_style)
            for i, row in enumerate(body):
                for j, col in enumerate(row):
                    ws.write(i + 1, j, body[i][j])

            # make column widths sane and submit
            ws = set_column_widths(ws, headers, body)
            response = HttpResponse(mimetype='application/ms-excel')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename
            xls.save(response)
            return response

        elif format == 'csv':
            response = HttpResponse(mimetype='text/csv')
            response['Content-Disposition'] = 'attachment; filename=%s' % filename

            csv_writer = UnicodeWriter(response)
            if headers:
                csv_writer.writerow(headers)
            csv_writer.writerows(body)

            return response

        raise Http404


@login_required
def table_export(request, *args, **kwargs):
    return TableExportHandler()(request, *args, **kwargs)


# Helper methods
def enable_networks(adunit, account):
    """
    Create network adgroups for this adunit for all ad networks.

    NOTE: The campaigns' creatives are created when the adgroups are set to
    active in the EditNetwork handler in networks/view
    """
    ntwk_adgroups = []
    for campaign in CampaignQueryManager.get_network_campaigns(account,
            is_new=True):
        adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                adunit.key(), account.key())
        # New adunits are initialized as paused for the account's network
        # campaigns
        adgroup.active = False
        adgroups = AdGroupQueryManager.get_adgroups(campaign=campaign)
        # Accounts should have adunits prior to creating campaigns but just in
        # case don't break
        if adgroups:
            preexisting_adgroup = adgroups[0]
            # Copy over targeting for the NetworkDetails page
            adgroup.device_targeting = preexisting_adgroup.device_targeting
            for device, pretty_name in adgroup.DEVICE_CHOICES:
                setattr(adgroup, 'target_' + device, getattr(
                    preexisting_adgroup, 'target_' + device, False))
            adgroup.target_other = preexisting_adgroup.target_other
        ntwk_adgroups.append(adgroup)
    AdGroupQueryManager.put(ntwk_adgroups)


def enable_marketplace(adunit, account):
    """
    Gets/creates an adgroup and a default mpx creative for an adunit.
    Use this to enable marketplace on an adunit.
    """
    # create marketplace adgroup for this adunit
    mpx_adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit.key(), account.key())
    AdGroupQueryManager.put(mpx_adgroup)

    # create appropriate marketplace creative for this adunit / adgroup (same key_name)
    mpx_creative = mpx_adgroup.default_creative(key_name=mpx_adgroup.key().name())
    mpx_creative.adgroup = mpx_adgroup
    mpx_creative.account = account
    CreativeQueryManager.put(mpx_creative)


def add_demo_campaign(site):
    """
    Helper method that creates a demo campaign.
    Use this to create a default campaign when a user just signed up.
    """
    # Set up a test campaign that returns a demo ad
    demo_description = "Demo campaign for checking that MoPub works for your application"
    c = Campaign(name="MoPub Demo Campaign",
                 u=site.account.user,
                 account=site.account,
                 campaign_type="backfill_promo",
                 description=demo_description)
    CampaignQueryManager.put(c)

    # Set up a test ad group for this campaign
    ag = AdGroup(name="MoPub Demo Campaign",
                 campaign=c,
                 account=site.account,
                 priority_level=3,
                 bid=1.0,
                 bid_strategy="cpm",
                 site_keys=[site.key()])
    AdGroupQueryManager.put(ag)

    # And set up a default creative
    default_creative_html = """
    <style type="text/css">
    body {
      font-size: 12px;
      font-family: helvetica,arial,sans-serif;
      margin:0;
      padding:0;
      text-align:center;
      background:white
    }
    .creative_headline {
      font-size: 18px;
    }
    .creative_promo {
      color: green;
      text-decoration: none;
    }
    </style>
    <div class="creative_headline">
      Welcome to mopub!
    </div>
    <div class="creative_promo">
      <a href="http://www.mopub.com">
        Click here to test ad
      </a>
    </div>
    <div>
      You can now set up a new campaign to serve other ads.
    </div>
    """

    if site.format == "custom":
        h = HtmlCreative(ad_type="html",
                         ad_group=ag,
                         account=site.account,
                         custom_height = site.custom_height,
                         custom_width = site.custom_width,
                         format=site.format,
                         name="Demo HTML Creative",
                         html_data=default_creative_html)

    else:
        h = HtmlCreative(ad_type="html",
                         ad_group=ag,
                         account=site.account,
                         format=site.format,
                         name="Demo HTML Creative",
                         html_data=default_creative_html)
    CreativeQueryManager.put(h)


def create_iad_mapper(account, app):
    """
    Create AdNetworkAppMapper for iad if itunes url is input and iad
    AdNetworkLoginCredentials exist
    """
    if app.iad_pub_id:
        login = AdNetworkLoginManager.get_logins(account, network='iad').get()
        if login:
            mappers = AdNetworkMapperManager.get_mappers_for_app(login=login,
                    app=app)
            # Delete the existing mappers if there are no scrape stats for them.
            for mapper in mappers:
                if mapper:
                    stats = mapper.ad_network_stats
                    if not stats.count():
                        mapper.delete()
            AdNetworkMapperManager.create(network='iad',
                                          pub_id=app.iad_pub_id,
                                          login=login,
                                          app=app)


def calculate_ecpm(adgroup):
    """
    Calculate the ecpm for a cpc campaign.
    REFACTOR: move this to the app/adunit models
    """
    if adgroup.cpc and adgroup.stats.impression_count:
        return (float(adgroup.stats.click_count) * float(adgroup.bid) * 1000.0 /
                float(adgroup.stats.impression_count))
    return adgroup.bid


def filter_adgroups(adgroups, cfilter):
    filtered_adgroups = filter(lambda x: x.campaign.campaign_type in
            cfilter, adgroups)
    filtered_adgroups = sorted(filtered_adgroups, lambda x,y: cmp(y.bid, x.bid))
    return filtered_adgroups


def filter_campaigns(campaigns, cfilter):
    filtered_campaigns = filter(lambda x: x.campaign_type in
            cfilter, campaigns)
    filtered_campaigns = sorted(filtered_campaigns, lambda x,y: cmp(y.name,
        x.name))
    return filtered_campaigns


def set_column_widths(ws, headers, body):
    # xlwt defines the widtht of '0' character as 256, so let's give a bit
    # of leeway
    char_width = 275

    body.insert(0, headers)

    # maximum width of each column, in characters
    def max_chars_in_column(column):
        chars_in_column = [len(cell) for cell in column]
        return max(chars_in_column)

    # Andrew hated my nested list comprehension, so here's this
    columns = zip(*body)
    column_widths = [max_chars_in_column(col) for col in columns]

    # traverse worksheet columns and set width appropriately
    for i in range(len(body[0])):
        ws.col(i).width = column_widths[i] * char_width

    return ws
