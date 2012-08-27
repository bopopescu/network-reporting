__doc__ = """
API for fetching JSON serialized data for Apps, AdUnits, and AdGroups.
"""

from datetime import date
import logging
import urllib
import urllib2

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.utils import simplejson as json

from advertiser.query_managers import (AdGroupQueryManager,
                                       CampaignQueryManager)
from common.constants import PERCENT_DELIVERED_URL, PACING_URL
from common.ragendja.template import JSONResponse
from common.utils.request_handler import RequestHandler
from common.utils.stats_helpers import (MarketplaceStatsFetcher,
                                        SummedStatsFetcher,
                                        DirectSoldStatsFetcher,
                                        NetworkStatsFetcher)
from publisher.models import App, AdUnit
from publisher.query_managers import (PublisherQueryManager,
                                      AdUnitQueryManager,
                                      AppQueryManager)


class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None, adgroup_key=None, campaign_key=None):

        callback_name = self.request.GET.get('callback', None)

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

        return JSONResponse(apps, callback=callback_name)

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

            else:
                return JSONResponse(response)

        elif campaign_key:

            campaign = CampaignQueryManager.get(campaign_key)

            # REFACTOR
            # ensure the owner of this adgroup is the request's
            # current user
            if campaign.account.key() != self.account.key():
                raise Http404

            if adunit_key:
                adunits = [AdUnitQueryManager.get(adunit_key)]
            else:
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
                adunit_stats.update({'app_id': app_key})
                adunit.update(adunit_stats)

                # Update the adunit with the information from the
                # marketplace adgroup. At this time all the adunit
                # needs to know about is the adgroup's price floor
                # and whether the marketplace is on/off for that
                # adunit (active=True/False)
                adgroup = AdGroupQueryManager.get_marketplace_adgroup(
                    adunit['id'], str(self.account.key()), get_from_db=True)
                try:
                    adunit.update(price_floor=adgroup.mktplace_price_floor)
                except AttributeError, e:
                    logging.warn(e)
                    adunit.update(price_floor="0.25")

                try:
                    adunit.update(active=adgroup.active)
                except AttributeError, e:
                    logging.warn(e)
                    adunit.update(active=False)

            return JSONResponse(response)

        else:
            return JSONResponse({'error': 'not yet implemented'})

    def post(self):
        """
        Not yet implemented.
        Could be used in the future as an endpoint for adunit creation.
        """
        return JSONResponse({'error': 'Not yet implemented'})

    def put(self, app_key=None, adunit_key=None):
        """
        Update the adunit from the PUT data
        """
        # Hack. Django doesn't have request.PUT by default, and instead
        # includes the PUT params in request.raw_post_data
        put_data = json.loads(self.request.raw_post_data)

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

        return JSONResponse({'success': 'success'})

    def delete(self):
        return JSONResponse({'error': 'Not yet implemented'})


@login_required
def adunit_service(request, *args, **kwargs):
    return AdUnitService()(request, use_cache=False, *args, **kwargs)


#######################
# Advertiser services #
#######################

class CampaignServiceHandler(RequestHandler):
    def get(self, campaign_key):
        campaign = CampaignQueryManager.get(campaign_key)

        endpoint = self.request.GET.get('endpoint', 'all')
        stats_fetcher = get_stats_fetcher(campaign._account, endpoint)

        app_key = self.request.GET.get('app', None)
        if app_key:
            publisher = AppQueryManager.get(app_key)
            if publisher._account != campaign._account:
                raise Http404
        else:
            adunit_key = self.request.GET.get('adunit', None)
            if adunit_key:
                publisher = AdUnitQueryManager.get(adunit_key)
                if publisher._account != campaign._account:
                    raise Http404
            else:
                publisher = None

        include_daily = self.request.GET.get('daily', '0') == '1'

        include_adgroups = self.request.GET.get('adgroups', '0') == '1'

        include_creatives = self.request.GET.get('creatives', '0') == '1'

        campaign_dict = get_campaign_dict(
            campaign, stats_fetcher, self.start_date, self.end_date, publisher,
            include_daily, include_adgroups, include_creatives)

        return JSONResponse(campaign_dict)

    def post(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})

    def put(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})

    def delete(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})


@login_required
def campaign_service(request, *args, **kwargs):
    handler = CampaignServiceHandler(id='campaign_key')
    return handler(request, use_cache=False, *args, **kwargs)


class AdGroupServiceHandler(RequestHandler):
    """
    API Service for delivering serialized AdGroup data
    """
    def get(self, adgroup_key):
        adgroup = AdGroupQueryManager.get(adgroup_key)

        endpoint = self.request.GET.get('endpoint', 'all')
        stats_fetcher = get_stats_fetcher(adgroup._account, endpoint)

        app_key = self.request.GET.get('app', None)
        if app_key:
            publisher = AppQueryManager.get(app_key)
            if publisher._account != adgroup._account:
                raise Http404
        else:
            adunit_key = self.request.GET.get('adunit', None)
            if adunit_key:
                publisher = AdUnitQueryManager.get(adunit_key)
                if publisher._account != adgroup._account:
                    raise Http404
            else:
                publisher = None

        include_daily = self.request.GET.get('daily', '0') == '1'

        include_creatives = self.request.GET.get('creatives', '0') == '1'

        adgroup_dict = get_adgroup_dict(
            adgroup, stats_fetcher, self.start_date, self.end_date, publisher,
            include_daily, include_creatives)

        return JSONResponse(adgroup_dict)

    def post(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})

    def put(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})

    def delete(self, *args, **kwargs):
        return JSONResponse({'error': 'Not implemented'})


@login_required
def adgroup_service(request, *args, **kwargs):
    handler = AdGroupServiceHandler(id='adgroup_key')
    return handler(request, use_cache=False, *args, **kwargs)


####################
# Helper Functions #
####################

def get_campaign_dict(campaign, stats_fetcher, start_date, end_date,
                      publisher=None, include_daily=False,
                      include_adgroups=False, include_creatives=False):
    campaign_dict = campaign.to_dict()

    if publisher:
        if isinstance(publisher, App):
            stats_dict = stats_fetcher.get_campaign_specific_app_stats(
                publisher, campaign, start_date, end_date, include_daily)
        elif isinstance(publisher, AdUnit):
            stats_dict = stats_fetcher.get_campaign_specific_adunit_stats(
                publisher, campaign, start_date, end_date, include_daily)
        else:
            raise TypeError("Publisher must be an instance of App or AdUnit.")
    else:
        stats_dict = stats_fetcher.get_campaign_stats(
            campaign, start_date, end_date, include_daily)
    campaign_dict.update(stats_dict)

    if include_adgroups:
        campaign_dict['adgroups'] = [
            get_adgroup_dict(adgroup, stats_fetcher, start_date, end_date,
                             publisher, False, include_creatives)
                for adgroup in campaign.adgroups if (not adgroup.deleted and
                                                     not adgroup.archived)]

    return campaign_dict


def get_adgroup_dict(adgroup, stats_fetcher, start_date, end_date,
                     publisher=None, include_daily=False,
                     include_creatives=False):
    adgroup_dict = adgroup.to_dict()

    if adgroup.gtee() and (adgroup.has_daily_budget or adgroup.has_full_budget):
        percent_delivered = get_percent_delivered(adgroup.key())
        if percent_delivered is not None:
            adgroup_dict['percent_delivered'] = percent_delivered

        if (adgroup.budget_strategy == 'evenly' and adgroup.active and
                date.today() >= adgroup.start_datetime.date() and
                (not adgroup.end_datetime or
                 date.today() <= adgroup.end_datetime.date())):
            pacing = get_pacing(adgroup.key())
            if pacing is not None:
                adgroup_dict['pacing'] = pacing

    if publisher:
        if isinstance(publisher, App):
            stats_dict = stats_fetcher.get_adgroup_specific_app_stats(
                publisher, adgroup, start_date, end_date, include_daily)
        elif isinstance(publisher, AdUnit):
            stats_dict = stats_fetcher.get_adgroup_specific_adunit_stats(
                publisher, adgroup, start_date, end_date, include_daily)
        else:
            raise TypeError("Publisher must be an instance of App or AdUnit.")
    else:
        stats_dict = stats_fetcher.get_adgroup_stats(
            adgroup, start_date, end_date, include_daily)
    adgroup_dict.update(stats_dict)

    if include_creatives:
        adgroup_dict['creatives'] = [
            get_creative_dict(creative, stats_fetcher, start_date, end_date,
                              publisher, False)
                for creative in adgroup.creatives if not creative.deleted]

    return adgroup_dict


def get_creative_dict(creative, stats_fetcher, start_date, end_date,
                      publisher=None, include_daily=False):
    creative_dict = creative.to_dict()

    if publisher:
        if isinstance(publisher, App):
            stats_dict = stats_fetcher.get_creative_specific_app_stats(
                publisher, creative, start_date, end_date, include_daily)
        elif isinstance(publisher, AdUnit):
            stats_dict = stats_fetcher.get_creative_specific_adunit_stats(
                publisher, creative, start_date, end_date, include_daily)
        else:
            raise TypeError("Publisher must be an instance of App or AdUnit.")
    else:
        stats_dict = stats_fetcher.get_creative_stats(
            creative, start_date, end_date, include_daily)
    creative_dict.update(stats_dict)

    return creative_dict


def get_percent_delivered(adgroup_key):
    percent_delivered_url = "%s?%s" % (PERCENT_DELIVERED_URL, urllib.urlencode({
        'key': str(adgroup_key),
        'key_type': 'adgroup',
    }))

    try:
        percent_delivered_dict = json.loads(
            urllib2.urlopen(percent_delivered_url).read())
    except:
        logging.error("Error reading %s" % percent_delivered_url)
        return None

    if percent_delivered_dict['percent_delivered'] is not None:
        return float(percent_delivered_dict['percent_delivered'])

    logging.error("%s return an invalid response %s" % (percent_delivered_url,
                                                        percent_delivered_dict))
    return None


def get_pacing(adgroup_key):
    pacing_url = "%s?%s" % (PACING_URL, urllib.urlencode({
        'key': str(adgroup_key),
        'key_type': 'adgroup',
    }))

    try:
        pacing_dict = json.loads(urllib2.urlopen(pacing_url).read())
    except:
        logging.error("Error reading %s" % pacing_url)
        return None

    if (pacing_dict['pacing'] is not None and
            pacing_dict['pacing'][0] == 'Pacing'):
        return float(pacing_dict['pacing'][1])

    logging.error("%s return an invalid response %s" % (pacing_url,
                                                        pacing_dict))
    return None


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
