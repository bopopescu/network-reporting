__doc__ = """
API for fetching JSON serialized data for Apps, AdUnits, and AdGroups.
"""
from datetime import datetime, time, date
from advertiser.models import NetworkStates
from advertiser.query_managers import AdGroupQueryManager, \
        CampaignQueryManager, \
        CreativeQueryManager
from ad_network_reports.query_managers import AdNetworkLoginManager, \
        AdNetworkMapperManager

from publisher.query_managers import AdUnitQueryManager, \
     AppQueryManager, \
     PublisherQueryManager
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from ad_network_reports.models import AdNetworkAppMapper, AdNetworkStats
from ad_network_reports.query_managers import AdNetworkStatsManager

from ad_server.optimizer.optimizer import DEFAULT_CTR
from adserver_constants import ADSERVER_HOSTNAME

from budget import budget_service

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse
from common.utils.stats_helpers import MarketplaceStatsFetcher, \
     SummedStatsFetcher, \
     DirectSoldStatsFetcher, \
     NetworkStatsFetcher, \
     MPStatsAPIException
from common.constants import REPORTING_NETWORKS

from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import Http404

import logging
import urllib
import urllib2

REMOTE_PACING_URL = '/admin/budget/api/pacing'
REMOTE_DELIVERED_URL = '/admin/budget/api/delivered'


class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None, adgroup_key=None, campaign_key=None):

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

        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            if campaign.account.key() != self.account.key():
                raise Http404

        # Where are we getting stats from?
        # Choices are 'mpx', 'direct', 'networks' or 'all'
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
            # stats to reflect how it performed within that adgroup. Likewise
            # for campaign.
            if adgroup_key:

                app.update(stats.get_adgroup_specific_app_stats(str(app['id']),
                                                                adgroup_key,
                                                                self.start_date,
                                                                self.end_date))
            elif campaign_key:
                app.update(stats.get_campaign_specific_app_stats(str(app['id']),
                                                                campaign,
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
    def get(self, app_key=None, adgroup_key=None, campaign_key=None,
            adunit_key=None):
        """
        Returns individual or lists of JSON-represented adunit
        metadata and stats data
        """
        # where are we getting stats from?
        # choices are 'mpx', 'direct', 'networks' or 'all'
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

        elif campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)

            # REFACTOR
            # ensure the owner of this campaign is the request's
            # current user
            if campaign.account.key() != self.account.key():
                raise Http404

            adunits = PublisherQueryManager.get_adunits_dict_for_account(self.account).values()

            response = [adunit.toJSON() for adunit in adunits]

            # Update each app with stats from the selected endpoint
            for adunit in response:
                adunit_stats = stats.get_campaign_specific_adunit_stats(adunit['id'],
                                                                       campaign,
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
        adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key,
                account_key)

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

            api_dict = dict(key = str(adgroup.campaign.key()),
                            key_type = 'campaign',
                            )
            qs = urllib.urlencode(api_dict)

            to_adserver = 'http://' + ADSERVER_HOSTNAME
            pacing_url = to_adserver + REMOTE_PACING_URL + '?' + qs
            try:
                pacing_data = simplejson.loads(urllib2.urlopen(pacing_url).read())
                #adgroup.pace = budget_service.get_pace(adgroup.campaign.budget_obj)
                adgroup.pace = pacing_data['pacing']
            except:
                adgroup.pace = None

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

            delivered_url = to_adserver + REMOTE_DELIVERED_URL + '?' + qs

            logging.warn(summed_stats)
            
            try:
                delivered_data = simplejson.loads(urllib2.urlopen(delivered_url).read())
                percent_delivered = delivered_data['percent_delivered']
                summed_stats.percent_delivered = percent_delivered
                adgroup.percent_delivered = percent_delivered
                summed_stats.status = adgroup.status
            except:
                pass

            stats_dict = summed_stats.to_dict()

            stats_dict['daily_stats'] = [s.to_dict() for s in stats]

            return JSONResponse(stats_dict)


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
        campaign = CampaignQueryManager.get(campaign_key)

        # REFACTOR
        # ensure the owner of this campaign is the request's
        # current user
        if not campaign or campaign.account.key() != self.account.key():
            raise Http404

        # Get the stats for the campaign
        stats_endpoint = self.request.GET.get('endpoint', 'all')
        stats_fetcher = get_stats_fetcher(self.account.key(), stats_endpoint)
        campaign_stats = stats_fetcher.get_campaign_stats(campaign_key,
                self.start_date, self.end_date)

        return JSONResponse(campaign_stats)
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
        stats = NetworkStatsFetcher(account_key)
    elif stats_endpoint == 'all':
        stats = SummedStatsFetcher(account_key)
    else:
        raise Exception("""You passed an invalid stats_endpoint. Valid
                        parameters are 'mpx', 'direct', 'networks' and
                        'all'.""")
    return stats
