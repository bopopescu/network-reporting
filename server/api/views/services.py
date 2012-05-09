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

        for app in apps:

            # if the adgroup key was specified, then we only want the app's
            # stats to reflect how it performed within that adgroup. Likewise
            # for campaign.
            if adgroup_key:
                s = stats.get_adgroup_specific_app_stats(str(app['id']),
                                                         adgroup_key,
                                                         self.start_date,
                                                         self.end_date)
            elif campaign_key:
                s = stats.get_campaign_specific_app_stats(str(app['id']),
                                                          campaign_key,
                                                          self.start_date,
                                                          self.end_date)
            else:
                s = stats.get_app_stats(str(app['id']),
                                        self.start_date,
                                        self.end_date)
            app.update(s)

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


        # If an adgroup key was specified instead of an app key,
        # then we'll only get stats data from that adgroup. AdUnit
        # stats will only reflect how adunits performed in that
        # adgroup.
        if adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if adgroup.account.key() != self.account.key():
                raise Http404

            if adunit_key:
                adunits = [AdUnitQueryManager.get(adunit_key)]
            else:
                adunits = AdUnitQueryManager.get_adunits(keys=adgroup.site_keys)
            
            response = [adunit.toJSON() for adunit in adunits]

            # Update each app with stats from the selected endpoint
            for adunit in response:
                adunit_stats = stats.get_adgroup_specific_adunit_stats(adunit['id'],
                                                                       adgroup_key,
                                                                       self.start_date,
                                                                       self.end_date)
                if str(adunit['id']) == "ag1kZXZ-bW9wdWItaW5jcgoLEgRTaXRlGEUM":
                    logging.warn(adunit_stats)
                # We update with the app and adgroup id/key because our
                # backbone models often need it for reference
                adunit_stats.update({'app_id': str(adunit['app_key'])})
                adunit.update(adunit_stats)

            if adunit_key:
                return JSONResponse(response[0])
            else:
                return JSONResponse(response)
            
        elif campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if campaign.account.key() != self.account.key():
                raise Http404

            adunits = [AdUnitQueryManager.get(adunit_key)]
            response = [adunit.toJSON() for adunit in adunits]

            # Update each app with stats from the selected endpoint
            for adunit in response:
                adunit_stats = stats.get_campaign_specific_adunit_stats(adunit['id'],
                                                                       campaign_key,
                                                                       self.start_date,
                                                                       self.end_date)

                
                # We update with the app and adgroup id/key because our
                # backbone models often need it for reference
                adunit_stats.update({
                    'app_id': str(adunit['app_key']),
                    'campaign_id': str(campaign_key)
                })
                adunit.update(adunit_stats)
                
            return JSONResponse(response[0])
            
        # REFACTOR: The app key isn't necessary (we can fetch an
        # adunit directly with it's key)
        elif app_key:
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
            return JSONResponse({'error': 'not yet implemented'})


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


#######################
# Advertiser services #
#######################

class AdGroupServiceHandler(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, adgroup_key):
        if not adgroup_key:
            raise Http404

        # Get the adgroup
        adgroup = AdGroupQueryManager.get(adgroup_key)
            
        # REFACTOR
        # ensure the owner of this adgroup is the request's
        # current user
        if adgroup.account.key() != self.account.key():
            raise Http404

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

        # Where are we getting stats from?
        # Choices are 'mpx', 'direct', 'networks', or 'all'
        stats_endpoint = self.request.GET.get('endpoint', 'all')

        # Get the stats fetcher
        stats_fetcher = get_stats_fetcher(self.account.key(), stats_endpoint)                        
        # JSONify and update with stats
        adgroup_jsonified = adgroup.toJSON()
        stats = stats_fetcher.get_adgroup_stats(adgroup,
                                                self.start_date,
                                                self.end_date,
                                                daily=True)
        adgroup_jsonified.update(stats)

        # pacing
        pace, pace_status = get_pace(adgroup)
        adgroup_jsonified.update({
            'percent_delivered': budget_service.percent_delivered(adgroup.budget_obj),
            'pace': pace,
            'pace_status': pace_status
        })
        
        return JSONResponse(adgroup_jsonified)


    def post(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})

    def put(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})

    def delete(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def adgroup_service(request, *args, **kwargs):
    return AdGroupServiceHandler()(request, use_cache=False, *args, **kwargs)


class CampaignServiceHandler(RequestHandler):
    def get(self, campaign_key=None, *args, **kwargs):

        # Get the campaign from the campaign key if it was
        # given. Otherwise, get all of the campaigns for the account.
        if campaign_key:
            campaign = CampaignQueryManager.get(campaign_key)
            if campaign.account.key() != self.account.key():
                raise Http404
            campaigns = [campaign]

        else:
            campaigns = CampaignQueryManager.get_campaigns(self.account)
            
        # Get stats and serialize all of the data
        stats_endpoint = self.request.GET.get('endpoint', 'all')
        stats_fetcher = get_stats_fetcher(self.account.key(), stats_endpoint)
        campaigns_jsonified = []
        for campaign in campaigns:
            campaign_jsonified = campaign.toJSON()
            campaign_jsonified['adgroups'] = []
            for adgroup in campaign.adgroups:
                stats = stats_fetcher.get_adgroup_stats(adgroup,
                                                        self.start_date,
                                                        self.end_date,
                                                        daily=True)
                adgroup_jsonified = adgroup.toJSON()
                adgroup_jsonified.update(stats)
                # pacing
                pace, pace_status = get_pace(adgroup)
                adgroup_jsonified.update({
                    'percent_delivered': budget_service.percent_delivered(adgroup.budget_obj),
                    'pace': pace,
                    'pace_status': pace_status
                })

                campaign_jsonified['adgroups'].append(adgroup_jsonified)

            # Get the top level stats for the campaign by summing whats
            # in the adgroups
            campaign_jsonified.update(sum_campaign_stats(campaign_jsonified))
    
            campaigns_jsonified.append(campaign_jsonified)

        return JSONResponse(campaigns_jsonified)
                
        
            
        
    def post(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})


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
    return CampaignServiceHandler()(request, use_cache=False, *args, **kwargs)    


####################
# Helper Functions #
####################

def sum_campaign_stats(campaign):
    ctr = lambda clicks, impressions: \
          (clicks/float(impressions) if impressions else 0)
    ecpm = lambda revenue, impressions: \
           (revenue/float(impressions)*1000 if impressions else 0)
    fill_rate = lambda requests, impressions: \
                (impressions/float(requests) if requests else 0)

    stats = {
        'revenue': sum([ag['revenue'] for ag in campaign['adgroups']]),
        'ctr': 0.0,
        'ecpm': 0.0,
        'impressions': sum([ag['impressions'] for ag in campaign['adgroups']]),
        'clicks': sum([ag['clicks'] for ag in campaign['adgroups']]),
        'requests': sum([ag['requests'] for ag in campaign['adgroups']]),
        'fill_rate': 0.0,
        'conversions': sum([ag['conversions'] for ag in campaign['adgroups']]),
        
    }

    num_adgroups = len(campaign['adgroups'])
    if num_adgroups > 0:
        stats['conversion_rate'] =  sum([ag['conversion_rate'] \
                                         for ag in campaign['adgroups']]) \
                                    / len(campaign['adgroups'])
    else:
        stats['conversion_rate'] = 0
    stats['ctr'] = ctr(stats['clicks'], stats['impressions'])
    stats['ecpm'] = ecpm(stats['revenue'], stats['impressions'])
    stats['fill_rate'] = fill_rate(stats['requests'], stats['impressions'])
    
    return stats

    
def get_stats_fetcher(account_key, stats_endpoint):
    """
    Creates an appropriate fetcher for realtime stats.
    """
    if stats_endpoint == 'mpx':
        stats = MarketplaceStatsFetcher(account_key)
    elif stats_endpoint == 'direct':
        #REFACTOR: this should be DirecSoldStatsFetcher
        stats = SummedStatsFetcher(account_key)
    elif stats_endpoint == 'networks':
        stats = NetworkStatsFetcher(account_key)
    elif stats_endpoint == 'all':
        stats = SummedStatsFetcher(account_key)
    else:
        raise Exception("""You passed an invalid stats_endpoint. Valid
                        parameters are 'mpx', 'direct', 'networks' and
                        'all'.""")
    return stats


def get_pace(adgroup):
    pace = budget_service.get_pace(adgroup.budget_obj)
    if pace:
        if pace[1] < .5 :
            pace_status = 'pace-failure'
        elif pace[1] < .85:
            pace_status = 'pace-warning'
        else:
            pace_status = 'pace-succes'
            
        return (pace[1], pace_status)
        
    else:
        return (0, None)
