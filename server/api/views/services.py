__doc__ = """
API for fetching JSON serialized data for Apps, AdUnits, and AdGroups.
"""
from datetime import datetime, time, date
from advertiser.query_managers import AdGroupQueryManager, \
        CampaignQueryManager, \
        CreativeQueryManager
from ad_network_reports.query_managers import AD_NETWORK_NAMES as \
        REPORTING_NETWORKS, \
        AdNetworkLoginManager, \
        AdNetworkMapperManager
# TODO: move this
from networks.views import OTHER_NETWORKS

from publisher.query_managers import AdUnitQueryManager, \
     AppQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from ad_server.optimizer.optimizer import DEFAULT_CTR

from budget import budget_service

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse
from common.utils.stats_helpers import MarketplaceStatsFetcher, \
     SummedStatsFetcher, \
     DirectSoldStatsFetcher, \
     AdNetworkStatsFetcher, \
     MPStatsAPIException

from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import Http404

import logging


class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None, adgroup_key=None):

        # make sure app_key/adgroup_key are for apps/adgroups that
        # belong to this user
        if app_key:
            app = AppQueryManager.get_app_by_key(app_key)
            if app.account.key() != self.account.key():
                raise Http404

        if adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)
            if adgroup.account.key() != self.account.key():
                raise Http404

        # Where are we getting stats from?
        # Choices are 'mpx', 'direct', 'networks', or 'all'
        stats_endpoint = self.request.GET.get('endpoint', 'all')

        # Get the stats fetcher
        stats = get_stats_fetcher(self.account.key(), stats_endpoint)

        # If an app key is provided, return the single app
        if app_key:
            apps = [AppQueryManager.get_app_by_key(app_key).toJSON()]
        # If no app key is provided, return a list of all apps for the account
        else:
            apps = [a.toJSON() for a in AppQueryManager.get_apps(self.account)]

        # get stats for each app
        for app in apps:

            # if the adgroup key was specified, then we only want the app's
            # stats to reflect how it performed within that adgroup.
            if adgroup_key:

                app.update(stats.get_adgroup_specific_app_stats(str(app['id']),
                                                                adgroup_key,
                                                                self.start_date,
                                                                self.end_date))
            else:
                app.update(stats.get_app_stats(str(app['id']),
                                               self.start_date,
                                               self.end_date))

        return JSONResponse(apps)


    def post(self):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, app_key=None, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})


    def delete(self, app_key=None):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def app_service(request, *args, **kwargs):
    return AppService()(request, use_cache=False, *args, **kwargs)


class AdUnitService(RequestHandler):
    """
    API Service for delivering serialized AdUnit data
    """
    def get(self, app_key=None, adgroup_key=None, adunit_key=None):
        """
        Returns individual or lists of JSON-represented adunit
        metadata and stats data
        """
        # where are we getting stats from?
        # choices are 'mpx', 'direct', 'networks', or 'all'
        stats_endpoint = self.request.GET.get('endpoint', 'all')
        stats = get_stats_fetcher(self.account.key(), stats_endpoint)

        # REFACTOR: The app key isn't necessary (we can fetch an
        # adunit directly with it's key)
        if app_key:
            # Get each adunit for the app and convert it to JSON
            app = AppQueryManager.get_app_by_key(app_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if app.account.key() != self.account.key():
                raise Http404

            adunits = AdUnitQueryManager.get_adunits(app=app)
            response = [adunit.toJSON() for adunit in adunits]

            # Update each app with stats from the selected endpoint
            for adunit in response:
                adunit_stats = stats.get_adunit_stats(adunit['id'],
                                                      self.start_date,
                                                      self.end_date)
                # We update with the app id/key because our
                # backbone models often need it for reference
                adunit_stats.update({'app_id':app_key})
                adunit.update(adunit_stats)

                # Update the adunit with the information from the
                # marketplace adgroup. At this time all the adunit
                # needs to know about is the adgroup's price floor
                # and whether the marketplace is on/off for that
                # adunit (active=True/False)
                adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit['id'],
                                                                      str(self.account.key()),
                                                                      get_from_db=True)
                try:
                    adunit.update(price_floor = adgroup.mktplace_price_floor)
                except AttributeError, e:
                    logging.warn(e)
                    adunit.update(price_floor = "0.25")

                try:
                    adunit.update(active = adgroup.active)
                except AttributeError, e:
                    logging.warn(e)
                    adunit.update(active = False)

            return JSONResponse(response)

        # If an adgroup key was specified instead of an app key,
        # then we'll only get stats data from that adgroup. AdUnit
        # stats will only reflect how adunits performed in that
        # adgroup.
        elif adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if adgroup.account.key() != self.account.key():
                raise Http404

            adunits = AdUnitQueryManager.get_adunits(keys=adgroup.site_keys)
            response = [adunit.toJSON() for adunit in adunits]

            # Update each app with stats from the selected endpoint
            for adunit in response:
                adunit_stats = stats.get_adgroup_specific_adunit_stats(adunit['id'],
                                                                       adgroup_key,
                                                                       self.start_date,
                                                                       self.end_date)

                # We update with the app and adgroup id/key because our
                # backbone models often need it for reference
                adunit_stats.update({'app_id': str(adunit['app_key'])})
                adunit.update(adunit_stats)

            return JSONResponse(response)

        else:
            return JSONResponse({'error': 'No parameters provided'})


    def post(self):
        """
        Not yet implemented.
        Could be used in the future as an endpoint for adunit creation.
        """
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, app_key = None, adunit_key = None):
        """
        Update the adunit from the PUT data
        """
        # Hack. Django doesn't have request.PUT by default, and instead
        # includes the PUT params in request.raw_post_data
        put_data = simplejson.loads(self.request.raw_post_data)

        new_price_floor = put_data['price_floor']
        activity = put_data['active']

        account_key = self.account.key()
        adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key, account_key)

        # REFACTOR
        # ensure the owner of this adgroup is the request's
        # current user
        if adgroup.account.key() != self.account.key():
            raise Http404

        if new_price_floor:
            try:
                adgroup.mktplace_price_floor = float(new_price_floor)
                adgroup.active = activity
                AdGroupQueryManager.put(adgroup)
            except ValueError, e:
                logging.warn(e)
                return JSONResponse({'error': 'price floor must be a float or an integer'})

        return JSONResponse({'success':'success'})


    def delete(self):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def adunit_service(request, *args, **kwargs):
    return AdUnitService()(request, use_cache=False, *args, **kwargs)


class AdGroupService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, adgroup_key):
        try:

            # Get the adgroup
            adgroup = AdGroupQueryManager.get(adgroup_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if adgroup.account.key() != self.account.key():
                raise Http404

            # Get the stats for the adgroup
            stats_fetcher = StatsModelQueryManager(self.account,
                                                   offline=self.offline)
            stats = stats_fetcher.get_stats_for_days(advertiser=adgroup,
                                                     days=self.days)
            summed_stats = sum(stats, StatsModel())

            # adds ECPM if the adgroup is a CPC adgroup
            if adgroup.cpc:
                e_ctr = summed_stats.ctr or DEFAULT_CTR
                summed_stats.cpm = float(e_ctr) * float(adgroup.cpc) * 1000
            elif 'marketplace' in adgroup.campaign.campaign_type:
                # Overwrite the revenue from MPX if its marketplace
                # TODO: overwrite clicks as well
                stats_fetcher = MarketplaceStatsFetcher(self.account.key())
                try:
                    mpx_stats = stats_fetcher.get_account_stats(self.start_date,
                                                                self.end_date)
                except MPStatsAPIException, error:
                    logging.error('MPStatsAPIException: ' + str(error))
                    mpx_stats = {}
                summed_stats.revenue = float(mpx_stats.get('revenue', '$0.00').replace('$','').replace(',',''))
                summed_stats.impression_count = int(mpx_stats.get('impressions', 0))
            else:
                summed_stats.cpm = adgroup.cpm

            adgroup.pace = budget_service.get_pace(adgroup.campaign.budget_obj)
            if adgroup.pace:
                summed_stats.pace = adgroup.pace[1]
                if adgroup.pace[0] == "Pacing":
                    if summed_stats.pace < .5:
                        summed_stats.pace_type = "pace-failure"
                    elif summed_stats.pace < .85:
                        summed_stats.pace_type = "pace-warning"
                    else:
                        summed_stats.pace_type = "pace-success"
                else:
                    summed_stats.pace_type = "delivery"

            percent_delivered = budget_service.percent_delivered(adgroup.campaign.budget_obj)
            summed_stats.percent_delivered = percent_delivered
            adgroup.percent_delivered = percent_delivered

            summed_stats.status = adgroup.status

            stats_dict = summed_stats.to_dict()

            stats_dict['daily_stats'] = [s.to_dict() for s in stats]

            return JSONResponse(stats_dict)
        except Exception, exception:
            return JSONResponse({'error': str(exception)})


    def post(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def delete(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def adgroup_service(request, *args, **kwargs):
    return AdGroupService()(request, use_cache=False, *args, **kwargs)


class CampaignService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, campaign_key):
        #try:
        # Get the adgroup
        campaign = CampaignQueryManager.get(campaign_key)

        # REFACTOR
        # ensure the owner of this campaign is the request's
        # current user
        if campaign.account.key() != self.account.key():
            raise Http404

        # Get the stats for the campaign
        stats_fetcher = StatsModelQueryManager(self.account,
                                               offline=self.offline)
        stats = stats_fetcher.get_stats_for_days(advertiser=campaign,
                                                 days=self.days)

        summed_stats = sum(stats, StatsModel())

        stats_dict = summed_stats.to_dict()

        stats_dict['daily_stats'] = [s.to_dict() for s in stats]

        stats_dict['name'] = REPORTING_NETWORKS.get(campaign. \
                network_type, False) or OTHER_NETWORKS[campaign. \
                network_type]

        return JSONResponse(stats_dict)
        #except Exception, exception:
            #return JSONResponse({'error': str(exception)})


    def post(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def delete(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def campaign_service(request, *args, **kwargs):
    return CampaignService()(request, use_cache=False, *args, **kwargs)


class NetworkAppsService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, network, adunits=False):
        from ad_network_reports.models import AdNetworkAppMapper, AdNetworkStats
        from ad_network_reports.query_managers import AdNetworkStatsManager

        campaign = CampaignQueryManager.get_network_campaign(self.account,
                network)

        #try:
        network_apps_ = {}
        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate the stats for network_apps_
        for app in AppQueryManager.get_apps(self.account):
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()
            all_stats = False
            if login:
                mappers = AdNetworkMapperManager.get_mappers_for_app(login,
                        app)
                if mappers.count(limit=1):
                    stats_by_day = {}
                    for day in self.days:
                        stats_by_day[day] = AdNetworkStats(date=date.today())

                    for mapper in mappers:
                        all_stats = AdNetworkStatsManager. \
                                get_stats_list_for_mapper_and_days(mapper.key(),
                                        self.days)
                        for stats in all_stats:
                            if stats.date in stats_by_day:
                                stats_by_day[stats.date] += stats

                    all_stats = sorted(stats_by_day.values(), key=lambda stats:
                            stats.date)

            if all_stats:
                stats = reduce(lambda x, y: x+y, all_stats,
                        AdNetworkStats())
                if app.key() not in network_apps_:
                    network_apps_[app.key()] = app
                if hasattr(network_apps_[app.key()], 'network_stats'):
                    network_apps_[app.key()].network_stats += stats
                else:
                    network_apps_[app.key()].network_stats = stats

            # Get data collected by MoPub
            for adunit in AdUnitQueryManager.get_adunits(account=self.
                    account, app=app):
                # One adunit per adgroup for network adunits
                adgroup = AdGroupQueryManager.get_network_adgroup(
                        campaign.key(), adunit.key(),
                        self.account.key(), network)

                all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                             advertiser=
                                                                adgroup,
                                                             days=self.days)
                stats = reduce(lambda x, y: x+y, all_stats, StatsModel())

                if app.key() not in network_apps_:
                    network_apps_[app.key()] = app
                if hasattr(network_apps_[app.key()], 'mopub_stats'):
                    network_apps_[app.key()].mopub_stats += stats
                else:
                    network_apps_[app.key()].mopub_stats = stats

                if adunits:
                    adunit_data = adunit.toJSON()
                    adunit_data['url'] = '/inventory/adunit/' + str(adunit.key())
                    adunit_data['stats'] = stats.to_dict()
                    if hasattr(network_apps_[app.key()], 'adunits'):
                        network_apps_[app.key()].adunits.append(adunit_data)
                    else:
                        network_apps_[app.key()].adunits = [adunit_data]

        network_apps_ = sorted(network_apps_.values(), key=lambda app_data:
                app_data.identifier)

        network_apps = []
        for app in network_apps_:
            app_data = app.toJSON()
            app_data['url'] = '/inventory/app/' + str(app.key())
            if adunits:
                app_data['adunits'] = app.adunits
            app_data['mopub_stats'] = app.mopub_stats.to_dict()
            if hasattr(app, 'network_stats'):
                app_data['network_stats'] = \
                    StatsModel(ad_network_stats=app.network_stats).to_dict()
            else:
                app_data['network_stats'] = StatsModel().to_dict()
            app_data['network'] = network
            network_apps.append(app_data)


        return JSONResponse(network_apps)

    #except Exception, exception:
            #return JSONResponse({'error': str(exception)})


    def post(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def delete(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def network_apps_service(request, *args, **kwargs):
    return NetworkAppsService()(request, use_cache=False, *args, **kwargs)


class NetworkDetailsDailyStatsService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, network):
        from ad_network_reports.models import AdNetworkAppMapper, AdNetworkStats
        from ad_network_reports.query_managers import AdNetworkStatsManager

        #try:
        reporting = True

        campaign = CampaignQueryManager.get_network_campaign(self.account,
                network)

        stats_by_day = {}
        for day in self.days:
            stats_by_day[day] = StatsModel(date=datetime.now())

        reporting_stats_by_day = {}
        for day in self.days:
            reporting_stats_by_day[day] = AdNetworkStats(date=date.today())

        adgroups = []

        stats_manager = StatsModelQueryManager(account=self.account)
        # Iterate through all the apps and populate stats_by_day
        for app in AppQueryManager.get_apps(self.account):
            login = AdNetworkLoginManager.get_login(self.account,
                    network).get()
            if login:
                mappers = AdNetworkMapperManager.get_mappers_for_app(login,
                        app)
                if mappers.count(limit=1):
                    # Get reporting graph stats

                    for mapper in mappers:
                        reporting_stats = AdNetworkStatsManager. \
                                get_stats_list_for_mapper_and_days(mapper.key(),
                                        self.days)

                        for stats in reporting_stats:
                            if stats.date in reporting_stats_by_day:
                                reporting_stats_by_day[stats.date] += stats
                    reporting = True

            # Get data collected by MoPub
            adunits = []
            for adunit in AdUnitQueryManager.get_adunits(account=self.account,
                    app=app):
                # One adunit per adgroup for network adunits
                adgroup = AdGroupQueryManager.get_network_adgroup(
                        campaign.key(), adunit.key(),
                        self.account.key(), network)
                adgroups.append(adgroup)

                all_stats = stats_manager.get_stats_for_days(publisher=app,
                                                             advertiser=adgroup,
                                                             days=self.days)
                for stats in all_stats:
                    if stats.date.date() in stats_by_day:
                        stats_by_day[stats.date.date()] += stats


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

        # Format network collected graph stats
        if reporting:
            reporting_graph_stats = reduce(lambda x, y: x+y,
                    reporting_stats_by_day.values(), AdNetworkStats())

            daily_stats = [StatsModel(request_count=stats.attempts,
                impression_count=stats.impressions,
                click_count=stats.clicks,
                date=datetime.combine(stats.date, time())).to_dict()
                for stats in reporting_stats_by_day.values()]
            daily_stats = sorted(daily_stats, key=lambda stats: stats['date'])

            reporting_graph_stats = StatsModel(request_count= \
                    reporting_graph_stats.attempts,
                    impression_count=reporting_graph_stats.impressions,
                    click_count=reporting_graph_stats.clicks).to_dict()
            reporting_graph_stats['daily_stats'] = daily_stats
            reporting_graph_stats['name'] = "From Networks"

            graph_stats.append(reporting_graph_stats)

        graph_stats.append(mopub_graph_stats)

        #graph_stats = simplejson.dumps(graph_stats)

        return JSONResponse(graph_stats)

    #except Exception, exception:
            #return JSONResponse({'error': str(exception)})


    def post(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


    def delete(self, *args, **kwagrs):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def network_details_daily_stats_service(request, *args, **kwargs):
    return NetworkDetailsDailyStatsService()(request, use_cache=False, *args,
            **kwargs)


## Helper Functions

def get_stats_fetcher(account_key, stats_endpoint):
    """
    Creates an appropriate fetcher for realtime stats.
    """
    if stats_endpoint == 'mpx':
        stats = MarketplaceStatsFetcher(account_key)
    elif stats_endpoint == 'direct':
        stats = DirectSoldStatsFetcher(account_key)
        stats = []
    elif stats_endpoint == 'networks':
        stats = AdNetworkStatsFetcher(account_key)
        stats = []
    elif stats_endpoint == 'all':
        stats = SummedStatsFetcher(account_key)
    else:
        raise Exception("""You passed an invalid stats_endpoint. Valid
                        parameters are 'mpx', 'direct', 'networks', and
                        'all'.""")
    return stats
