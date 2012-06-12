__doc__ = """
API for fetching JSON serialized data for Apps, AdUnits, and AdGroups.
"""
from advertiser.query_managers import (AdGroupQueryManager,
                                       CampaignQueryManager)

from publisher.query_managers import (PublisherQueryManager,
                                      AdUnitQueryManager, 
                                      AppQueryManager)

from budget import budget_service

from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse
from common.utils.stats_helpers import (MarketplaceStatsFetcher, 
                                        SummedStatsFetcher,
                                        DirectSoldStatsFetcher,
                                        NetworkStatsFetcher)

from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.http import Http404

import logging

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
    def get(self, app_key=None, adgroup_key=None,
            campaign_key=None, adunit_key=None):
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

            adunits = PublisherQueryManager.get_adunits_dict_for_account(self.account).values()
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
                
            return JSONResponse(response)
            
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

        # Where are we getting stats from?
        # Choices are 'mpx', 'direct', 'networks', or 'all'
        stats_endpoint = self.request.GET.get('endpoint', 'all')

        # Get the stats fetcher
        stats_fetcher = get_stats_fetcher(self.account.key(), stats_endpoint)                        
        # JSONify and update with stats
        adgroup_jsonified = adgroup.toJSON()
        logging.warn(adgroup_jsonified)
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

        if not adgroup_jsonified['percent_delivered']:
            adgroup_jsonified['percent_delivered'] = 0
        
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
                                                        daily=False)
                adgroup_jsonified = adgroup.toJSON()
                logging.warn('\n\n\n\n\n\n\n\n\n')
                logging.warn(adgroup_jsonified)
                adgroup_jsonified.update(stats)
                # pacing
                pace, pace_status = get_pace(adgroup)
                adgroup_jsonified.update({
                    'percent_delivered': budget_service.percent_delivered(adgroup.budget_obj),
                    'pace': pace,
                    'pace_status': pace_status
                })

                if not adgroup_jsonified['percent_delivered']:
                    adgroup_jsonified['percent_delivered'] = 0.0
        
                
                campaign_jsonified['adgroups'].append(adgroup_jsonified)

            # Get the top level stats for the campaign 
            campaign_jsonified.update(stats_fetcher.get_campaign_stats(campaign,
                                                                   self.start_date,
                                                                   self.end_date,
                                                                   daily=True))
    
            campaigns_jsonified.append(campaign_jsonified)

        return JSONResponse(campaigns_jsonified)
                
        
            
        
    def post(self, *args, **kwargs):
        return JSONResponse({'error': 'Not yet implemented'})


    def put(self, *args, **kwargs):
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
        'rev': sum([ag['rev'] for ag in campaign['adgroups']]),
        'ctr': 0.0,
        'ecpm': 0.0,
        'imp': sum([ag['imp'] for ag in campaign['adgroups']]),
        'clk': sum([ag['clk'] for ag in campaign['adgroups']]),
        'req': sum([ag['req'] for ag in campaign['adgroups']]),
        'fill_rate': 0.0,
        'conv': sum([ag['conv'] for ag in campaign['adgroups']]),
    }

    num_adgroups = len(campaign['adgroups'])
    if num_adgroups > 0:
        stats['conv_rate'] =  sum([ag['conv_rate'] \
                                   for ag in campaign['adgroups']]) \
                              / len(campaign['adgroups'])
    else:
        stats['conv_rate'] = 0
    stats['ctr'] = ctr(stats['clk'], stats['imp'])
    stats['ecpm'] = ecpm(stats['rev'], stats['imp'])
    stats['fill_rate'] = fill_rate(stats['req'], stats['imp'])
    
    return stats

    
def get_stats_fetcher(account_key, stats_endpoint):
    """
    Creates an appropriate fetcher for realtime stats.
    """
    if stats_endpoint == 'mpx':
        stats = MarketplaceStatsFetcher(account_key)
    elif stats_endpoint == 'direct':
        stats = DirectSoldStatsFetcher(account_key)
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
            pace_status = 'pace-success'

        return (pace[1], pace_status)

    else:
        return (0, None)
