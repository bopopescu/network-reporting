__doc__ = """
API for fetching JSON serialized data for Apps, AdUnits, AdGroups, and
AdNetworkReports.
"""
from advertiser.query_managers import AdGroupQueryManager
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
     NetworkStatsFetcher, \
     DirectSoldStatsFetcher
     DirectSoldStatsFetcher, \
     AdNetworkStatsFetcher

from common.utils import date_magic
from common.utils.timezones import Pacific_tzinfo
from common_templates.templatetags.filters import campaign_status

from django.contrib.auth.decorators import login_required
from django.utils import simplejson

import datetime
import logging


class Types:
    APP = 'app'
    NETWORK = 'network'

class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None):
        try:

            # Where are we getting stats from?
            # Choices are 'mpx', 'direct', 'networks', or 'all'
            stats_endpoint = self.request.GET.get('endpoint', 'all')

            # Formulate the date range
            if self.request.GET.get('s', None):
                year, month, day = str(self.request.GET.get('s')).split('-')
                end_date = datetime.date(int(year), int(month), int(day))
            else:
                end_date = datetime.date.today()

            if self.request.GET.get('r', None):
                days_in_range = int(self.request.GET.get('r')) - 1
                start_date = end_date - datetime.timedelta(days_in_range)
            else:
                start_date = end_date - datetime.timedelta(13)

            # Get the stats fetcher
            if stats_endpoint == 'mpx':
                stats = MarketplaceStatsFetcher(self.account.key())
            elif stats_endpoint == 'direct':
                stats = DirectSoldStatsFetcher(self.account.key())
                stats = []
            elif stats_endpoint == 'networks':
                stats = NetworkStatsFetcher(self.account.key())
                stats = []
            else:
                stats = SummedStatsFetcher(self.account.key())

            # If an app key is provided, return the single app
            if app_key:
                apps = [AppQueryManager.get_app_by_key(app_key).toJSON()]
            # If no app key is provided, return a list of all apps for the account
            else:
                apps = [app.toJSON() for app in AppQueryManager.get_apps(self.account)]


            # get stats for each app
            for app in apps:
                app.update(stats.get_app_stats(str(app['id']), start_date, end_date))

            return JSONResponse(apps)

        except Exception, e:
            logging.warn("APPS FETCH ERROR "  + str(e))
            return JSONResponse({'error': str(e)})


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
    def get(self, app_key = None, adunit_key = None):
        try:

            # where are we getting stats from?
            # choices are 'mpx', 'direct', 'networks', or 'all'
            stats_endpoint = self.request.GET.get('endpoint', 'all')

            if stats_endpoint == 'mpx':
                stats = MarketplaceStatsFetcher(self.account.key())
            elif stats_endpoint == 'direct':
                stats = DirectSoldStatsFetcher(self.account.key())
                stats = []
            elif stats_endpoint == 'networks':
                stats = NetworkStatsFetcher(self.account.key())
                stats = []
            else:
                stats = SummedStatsFetcher(self.account.key())

            # formulate the date range
            if self.request.GET.get('s', None):
                year, month, day = str(self.request.GET.get('s')).split('-')
                end_date = datetime.date(int(year), int(month), int(day))
            else:
                end_date = datetime.date.today()

            if self.request.GET.get('r', None):
                days_in_range = int(self.request.GET.get('r')) - 1
                start_date = end_date - datetime.timedelta(days_in_range)
            else:
                start_date = end_date - datetime.timedelta(13)

            # REFACTOR: The app key isn't necessary (we can fetch an adunit directly
            # with it's key)
            if app_key:
                # Get each adunit for the app and convert it to JSON
                app = AppQueryManager.get_app_by_key(app_key)
                adunits = AdUnitQueryManager.get_adunits(app=app)
                response = [adunit.toJSON() for adunit in adunits]

                # Update each app with stats from the selected endpoint
                for adunit in response:
                    adunit_stats = stats.get_adunit_stats(adunit['id'],
                                                          start_date,
                                                          end_date)
                    # We update with the app id/key because our backbone models
                    # often need it for reference
                    adunit_stats.update({'app_id':app_key})
                    adunit.update(adunit_stats)

                    # We include some marketplace data by default. Possibly
                    # not neccessary.
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
            else:
                return JSONResponse({'error': 'No parameters provided'})
        except Exception, e:
            logging.warn("ADUNITS FETCH ERROR " + str(e))
            return JSONResponse({'error': str(e)})

    def post(self):
        pass

    def put(self, app_key = None, adunit_key = None):
        try:
            # Hack. Django doesn't have request.PUT by default, and instead
            # includes the PUT params in request.raw_post_data
            put_data = simplejson.loads(self.request.raw_post_data)

            new_price_floor = put_data['price_floor']
            activity = put_data['active']

            account_key = self.account.key()
            adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key, account_key)

            if new_price_floor:
                try:
                    adgroup.mktplace_price_floor = float(new_price_floor)
                    adgroup.active = activity
                    AdGroupQueryManager.put(adgroup)
                except ValueError, e:
                    logging.warn(e)
                    return JSONResponse({'error': 'price floor must be a float or an integer'})

            return JSONResponse({'success':'success'})

        except Exception, error:
            logging.warn(error)
            return JSONResponse({"error": "error"})


    def delete(self):
        pass


@login_required
def adunit_service(request, *args, **kwargs):
    return AdUnitService()(request, use_cache=False, *args, **kwargs)


class AdGroupService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, adgroup_key):
        try:
            # Form the date range
            if self.start_date:
                end_date = self.start_date + datetime.timedelta(days=self.date_range)
            else:
                today = datetime.datetime.now(Pacific_tzinfo()).date()
                self.start_date = today - datetime.timedelta(days=self.date_range)
                end_date = today
            days = date_magic.gen_days(self.start_date, end_date)

            # Get the adgroup
            adgroup = AdGroupQueryManager.get(adgroup_key)

            # Get the stats for the adgroup
            stats_fetcher = StatsModelQueryManager(self.account,
                                                   offline=self.offline)
            stats = stats_fetcher.get_stats_for_days(advertiser=adgroup,
                                                     days=days)
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
                                                                end_date)
                except MPStatsAPIException, error:
                    mpx_stats = {}
                summed_stats.revenue = float(mpx_stats.get('revenue', '$0.00').replace('$','').replace(',',''))
                summed_stats.impression_count = int(mpx_stats.get('impressions', 0))
            else:
                summed_stats.cpm = adgroup.cpm

            adgroup.pace = budget_service.get_pace(adgroup.campaign.budget_obj)
            percent_delivered = budget_service.percent_delivered(adgroup.campaign.budget_obj)
            summed_stats.percent_delivered = percent_delivered
            adgroup.percent_delivered = percent_delivered

            summed_stats.status = campaign_status(adgroup)

            # Determine the pacing
            if adgroup.running and  \
               adgroup.campaign.budget_obj and  \
               adgroup.campaign.budget_obj.delivery_type != 'allatonce':

                if budget_service.get_osi(adgroup.campaign.budget_obj):
                    summed_stats.on_schedule = "on pace"
                else:
                    summed_stats.on_schedule = "behind"
            else:
                summed_stats.on_schedule = "none"

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


class CreativeService(RequestHandler):
    """
    API Service for delivering serialized Creative data
    """
    def get(self, creative_key=None):

        logging.warn(self.request.GET)

        mpxstats = MarketplaceStatsFetcher(self.account.key())

        end_date = datetime.datetime.today()
        start_date = end_date - datetime.timedelta(13)
        # url = "http://mpx.mopub.com/stats/creatives?pub_id=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY09GeAQw&dsp_id=4e8d03fb71729f4a1d000000"
        # response = urllib2.urlopen(url).read()
        # data = simplejson.loads(response)

        creative_data = mpxstats.get_all_creatives(start_date, end_date)

        creatives = []
        for creative in creative_data:
            creatives.append([
                creative["creative"]["url"],
                creative["creative"]["ad_dmn"],
                creative["stats"]["pub_rev"],
                currency(creative['stats']['ecpm']),
                creative["stats"]["imp"],
                #creative["stats"]["clk"],
                #percentage_rounded(creative['stats']['ctr']),
            ])

        return JSONResponse({
            'aaData': creatives
        })


    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


@login_required
def adgroup_service(request, *args, **kwargs):
    return AdGroupService()(request, use_cache=False, *args, **kwargs)

## Ad Network Services
#

class AccountRollUpService(RequestHandler):
    """
    API Service for delivering serialized precalculated roll up stats at the
    account level
    """

    def get(self):

        # Formulate the date range
        days = get_days(self.request)

        # Return rolled up stats at the accout level
        return JSONResponse(AdNetworkStatsFetcher.get_account_roll_up_stats(
            self.account, days))


@login_required
def account_roll_up_service(request, *args, **kwargs):
    return AccountRollUpService()(request, use_cache=False, *args, **kwargs)

class DailyStatsService(RequestHandler):
    """
    API Service for delivering serialized chart data for the ad network revenue
    reporting index page
    """
    def get(self):

        # Formulate the date range
        days = get_days(self.request)

        # Get only stats for that app
        return JSONResponse(AdNetworkStatsFetcher.get_daily_stats(
            self.account, days))


@login_required
def daily_stats_service(request, *args, **kwargs):
    return DailyStatsService()(request, use_cache=False, *args, **kwargs)

class RollUpService(RequestHandler):
    """
    API Service for delivering serialized precalculated roll up stats for ad
    networks
    """

    def get(self, type_, id_):

        # Formulate the date range
        days = get_days(self.request)

        # Return stats rolled up stats for the network and account
        if type_ == Types.APP:
            return JSONResponse(AdNetworkStatsFetcher.get_roll_up_stats(
                self.account, days, app=AppQueryManager.get_app_by_key(id_)))
        elif type_ == Types.NETWORK:
            return JSONResponse(AdNetworkStatsFetcher.get_roll_up_stats(
                self.account, days, network=id_))


@login_required
def roll_up_service(request, *args, **kwargs):
    return RollUpService()(request, use_cache=False, *args, **kwargs)

class AppOnNetworkService(RequestHandler):
    """
    API Service for delivering serialized app on network data
    """
    def get(self, network, pub_id):

        # Formulate the date range
        days = get_days(self.request)

        # Get only stats for that app
        return JSONResponse(AdNetworkStatsFetcher.get_app_on_network_stats(
            network, days, pub_id))


@login_required
def app_on_network_service(request, *args, **kwargs):
    return AppOnNetworkService()(request, use_cache=False, *args, **kwargs)

## Helper Functions
#
def get_days(request):
    if request.GET.get('s', None):
        year, month, day = str(request.GET.get('s')).split('-')
        start_date = datetime.date(int(year), int(month), int(day))
    else:
        start_date = datetime.date.today()
    days_in_range = int(request.GET.get('r'))

    return date_magic.gen_days_for_range(start_date, days_in_range)
