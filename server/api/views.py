from advertiser.models import *
from publisher.models import *
from advertiser.query_managers import CampaignQueryManager, \
     AdGroupQueryManager, \
     CreativeQueryManager, \
     TextCreativeQueryManager, \
     ImageCreativeQueryManager, \
     TextAndTileCreativeQueryManager, \
     HtmlCreativeQueryManager
from publisher.query_managers import AdUnitQueryManager, AppQueryManager, AdUnitContextQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from ad_server.optimizer.optimizer import DEFAULT_CTR

from budget import budget_service

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.stats_helpers import MarketplaceStatsFetcher, \
     SummedStatsFetcher, \
     NetworkStatsFetcher, \
     DirectSoldStatsFetcher
from common.utils import date_magic
from common.utils.timezones import Pacific_tzinfo
from common_templates.templatetags.filters import campaign_status, currency, percentage, percentage_rounded

from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.core.urlresolvers import reverse

import datetime
import logging
from django.conf import settings

import urllib2

class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None):
        try:

            # where are we getting stats from?
            # choices are 'mpx', 'direct', 'networks', or 'all'
            stats_endpoint = self.request.GET.get('endpoint', 'all')

            # formulate the date range
            if self.request.GET.get('s', None):
                year, month, day = str(self.request.GET.get('s')).split('-')
                end_date = datetime.date(int(year), int(month), int(day))
            else:
                end_date = datetime.date.today()

            if self.request.GET.get('r', None):
                start_date = end_date - datetime.timedelta(int(self.request.GET.get('r')) - 1)
            else:
                start_date = end_date - datetime.timedelta(13)


            # if settings.DEBUG:
            #     mpxstats = MarketplaceStatsFetcher("agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww")
            # else:
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
                # if settings.DEBUG:
                #     app.update(stats.get_app_stats("agltb3B1Yi1pbmNyDAsSA0FwcBiLo_8DDA", start_date, end_date))
                # else:
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

            logging.warn(self.request.GET)
            # if settings.DEBUG:
            #     mpxstats = MarketplaceStatsFetcher("agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww")
            # else:

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
                start_date = end_date - datetime.timedelta(int(self.request.GET.get('r')) - 1)
            else:
                start_date = end_date - datetime.timedelta(13)


            if app_key:

                app = AppQueryManager.get_app_by_key(app_key)
                adunits = AdUnitQueryManager.get_adunits(app=app)

                response = [adunit.toJSON() for adunit in adunits]

                for au in response:
                    # if settings.DEBUG:
                    #     adunit_stats = stats.get_adunit_stats("agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw", start_date, end_date)
                    # else:
                    adunit_stats = stats.get_adunit_stats(au['id'], start_date, end_date)
                    adunit_stats.update({'app_id':app_key})
                    au.update(adunit_stats)

                    adgroup = AdGroupQueryManager.get_marketplace_adgroup(au['id'],
                                                                          str(self.account.key()),
                                                                          get_from_db=True)
                    try:
                        au.update(price_floor = adgroup.mktplace_price_floor)
                    except AttributeError, e:
                        logging.warn(e)
                        au.update(price_floor = "0.25")

                    try:
                        au.update(active = adgroup.active)
                    except AttributeError, e:
                        logging.warn(e)
                        au.update(active = False)

                return JSONResponse(response)
            else:
                return JSONResponse({'error':'No parameters provided'})
        except Exception, e:
            logging.warn("ADUNITS FETCH ERROR " + str(e))
            return JSONResponse({'error': str(e)})

    def post(self):
        pass

    def put(self, app_key = None, adunit_key = None):

        put_data = simplejson.loads(self.request.raw_post_data)

        new_price_floor = put_data['price_floor']
        activity = put_data['active']

        account_key = self.account.key()
        adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key, account_key)

        adgroup.mktplace_price_floor = float(new_price_floor)
        adgroup.active = activity
        AdGroupQueryManager.put(adgroup)

        return JSONResponse({'success':'success'})

    def delete(self):
        pass


@login_required
def adunit_service(request, *args, **kwargs):
    return AdUnitService()(request, use_cache=False, *args, **kwargs)


class CampaignService(RequestHandler):
    """
    API Service for delivering serialized Campaign data
    """
    def get(self):
        return JSONResponse({'error':'No parameters provided'})

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


@login_required
def campaign_service(request, *args, **kwargs):
    return CampaignService()(request, use_cache=False, *args, **kwargs)


class AdGroupService(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, adgroup_key):
        try:
            if self.start_date:
                end_date = self.start_date + datetime.timedelta(days=self.date_range)
            else:
                today = datetime.datetime.now(Pacific_tzinfo()).date()
                self.start_date = today - datetime.timedelta(days=self.date_range)
                end_date = today
            days = date_magic.gen_days(self.start_date, end_date)

            adgroup = AdGroupQueryManager.get(adgroup_key)
            stats = StatsModelQueryManager(self.account, offline=self.offline).get_stats_for_days(advertiser=adgroup, days=days)

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
                    mpx_stats = stats_fetcher.get_account_stats(self.start_date, end_date)
                except MPStatsAPIException, e:
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
            if adgroup.running and adgroup.campaign.budget_obj and adgroup.campaign.budget_obj.delivery_type != 'allatonce':
                summed_stats.on_schedule = "on pace" if budget_service.get_osi(adgroup.campaign.budget_obj) else "behind"
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


class NetworkCampaignService(RequestHandler):
    """
    API Service for delivering serialized network campaign data
    """
    def get(self, campaign_key=None):


        start_date = request.GET.get('start_date', None)
        end_date = request.GET.get('end_date', None)
        batch = request.GET.get('batch', None)

        # If campaign_key isn't None, they want a single campaign.
        # Give it to them.
        if campaign_key:
            pass

        # If batch parameters are found, it means they want a couple
        # of campaigns at once. This is usually used to load data in chunks to
        # balance network latency with I/O, and also so that something is always
        # happening on the page.
        elif batch:
            pass

        # If no parameters are passed in any way, return all of the network campaigns.
        else:
            network_campaigns = CampaignQueryManager.get_network_campaigns(account=self.account)

        return JSONResponse({'error':'No parameters provided'})

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


@login_required
def network_campaign_service(request, *args, **kwargs):
    return NetworkCampaignService()(request, use_cache=False, *args, **kwargs)
