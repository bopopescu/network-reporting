import logging
import datetime

from django.utils import simplejson
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response, JSONResponse
from common.utils.timezones import Pacific_tzinfo

from google.appengine.api import urlfetch

from account.query_managers import AccountQueryManager
from advertiser.query_managers import CampaignQueryManager
from publisher.query_managers import AdUnitQueryManager, \
     AppQueryManager, \
     AdUnitContextQueryManager, \
     PublisherQueryManager
from common.utils.stats_helpers import MarketplaceStatsFetcher, \
     MPStatsAPIException



class MarketplaceIndexHandler(RequestHandler):
    """
    Rendering of the Marketplace page. At this point, this is the only
    Marketplace page, and everything is rendered here.
    """
    def get(self):

        # Marketplace settings are kept as a single campaign.  Only
        # one should exist per account.
        marketplace_campaign = CampaignQueryManager.get_marketplace(self.account, from_db=True)

        apps_dict = PublisherQueryManager.get_objects_dict_for_account(self.account)
        alphabetically_sorted_apps = sorted(apps_dict.values(), lambda x, y: cmp(x.name, y.name))
        app_keys_json = simplejson.dumps(apps_dict.keys())

        adunit_keys = []
        for app_key, app in apps_dict.iteritems():
            if app.adunits is not None:
                adunit_keys += [adunit.key() for adunit in app.adunits]

        # Set up a MarketplaceStatsFetcher with this account
        stats_fetcher = MarketplaceStatsFetcher(self.account.key())

        # Form the date range
        # REFACTOR this into a helper function
        if self.start_date:
            year, month, day = str(self.start_date).split('-')
            start_date = datetime.date(int(year), int(month), int(day))
            if self.date_range:
                end_date = start_date + datetime.timedelta(int(self.date_range) - 1)
            else:
                end_date = start_date + datetime.timedelta(13)
        else:
            end_date = datetime.datetime.now(Pacific_tzinfo()).date()
            if self.date_range:
                start_date = end_date - datetime.timedelta(int(self.date_range) - 1)
            else:
                start_date = end_date - datetime.timedelta(13)

        try:
            mpx_stats = stats_fetcher.get_account_stats(start_date,
                    end_date, daily=True)
        except MPStatsAPIException, error:
            logging.warning("MPStatsAPIException: %s" % error)
            mpx_stats = {}

        # Set up the blocklist
        blocklist = []
        network_config = self.account.network_config
        if network_config:
            blocklist = [str(domain) for domain in network_config.blocklist
                    if not str(domain) in ("", "#")]

        # Get today and yesterday's stats for the graph
        today_stats = []
        yesterday_stats = []
        stats = {}
        try:
            today_stats = mpx_stats["daily"][-1]
            yesterday_stats = mpx_stats["daily"][-2]

            # REFACTOR: load this data via ajax and use CollectionGraphView
            def cpm(rev, imp):
                if imp:
                    return rev / imp * 1000
                else:
                    return 0

            mpx_stats['cpm'] = cpm(mpx_stats['rev'], mpx_stats['imp'])

            for stats in mpx_stats['daily']:
                stats['cpm'] = cpm(stats['rev'], stats['imp'])

            stats = {
                'rev': {
                    'today': today_stats['rev'],
                    'yesterday': yesterday_stats['rev'],
                    'total': mpx_stats['rev']
                },
                'imp': {
                    'today': today_stats['imp'],
                    'yesterday': yesterday_stats['imp'],
                    'total': mpx_stats['imp'],
                },
                'cpm': {
                    'today': cpm(today_stats['rev'], today_stats['imp']),
                    'yesterday': cpm(yesterday_stats['rev'],
                        yesterday_stats['imp']),
                    'total': cpm(mpx_stats['rev'], mpx_stats['imp']),
                },
            }

        except Exception, e:
            logging.warn(e)

        try:
            blind = self.account.network_config.blind
        except AttributeError:
            blind = False

        return render_to_response(self.request,
                                  "advertiser/marketplace_index.html",
                                  {
                                      'marketplace': marketplace_campaign,
                                      'apps': alphabetically_sorted_apps,
                                      'app_keys': app_keys_json,
                                      'adunit_keys': adunit_keys,
                                      'pub_key': self.account.key(),
                                      'mpx_stats': simplejson.dumps(mpx_stats),
                                      'stats_breakdown_includes': ['revenue', 'impressions', 'ecpm'],
                                      'totals': mpx_stats,
                                      'today_stats': today_stats,
                                      'yesterday_stats': yesterday_stats,
                                      'stats': stats,
                                      'blocklist': blocklist,
                                      'start_date': start_date,
                                      'end_date': end_date,
                                      'date_range': self.date_range,
                                      'blind': blind,
                                      'network_config': network_config
                                  })


@login_required
def marketplace_index(request, *args, **kwargs):
    return MarketplaceIndexHandler()(request, use_cache=False, *args, **kwargs)


class BlocklistHandler(RequestHandler):
    """
    Ajax handler for adding/removing marketplace blocklist items.
    Required data parameters:
    - blocklist: a comma/whitespace separated list of urls to add/remove
    - action: 'add' or 'remove', the action to take
    """
    def post(self):
        try:
            # Get the blocklist urls and the action
            blocklist_urls = self.request.POST.get('blocklist')
            blocklist = blocklist_urls.replace(',', ' ').split()
            blocklist_action = self.request.POST.get('action')

            # Set the network config
            network_config = self.account.network_config

            # Process add's (sometimes they're in bulk)
            if blocklist_action == "add" and blocklist:
                new = [d for d in blocklist if not d in network_config.blocklist]
                network_config.blocklist.extend(blocklist)
                network_config.blocklist = sorted(set(network_config.blocklist))   # Removes duplicates and sorts
                AccountQueryManager().update_config_and_put(account=self.account,
                                                            network_config=network_config)

                return JSONResponse({'success': 'blocklist item(s) added',
                                     'new': new})

            # Process removes (there should only be one at a time, but we could
            # change functionality on the client side to remove multiple urls at once
            elif blocklist_action == "remove" and blocklist:
                for url in blocklist:
                    if network_config.blocklist.count(url):
                        network_config.blocklist.remove(url)
                AccountQueryManager().update_config_and_put(account=self.account, network_config=network_config)
                return JSONResponse({'success': 'blocklist item(s) removed'})

            # If they didn't pass the action, it's an error.
            else:
                return JSONResponse({'error': 'you must provide an action (add|remove) and a blockist'})

        except Exception, e:
            logging.warn(e)
            return JSONResponse({'error': 'server error'})


@login_required
def marketplace_blocklist_change(request, *args, **kwargs):
    return BlocklistHandler()(request, *args, **kwargs)


class ContentFilterHandler(RequestHandler):
    """
    Ajax handler for changing the marketplace content filter settings.
    """
    def post(self):
        network_config = self.account.network_config
        filter_level = self.request.POST.get('filter_level', None)

        # If the account doesn't have a network config, make one
        if not network_config:
            network_config = NetworkConfig(account=self.account)
            network_config.put()
            self.account.network_config = network_config
            self.account.put()

        # Set the filter level if it was passed
        if filter_level:
            if filter_level == "none":
                network_config.set_no_filter()
            elif filter_level == "low":
                network_config.set_low_filter()
            elif filter_level == "moderate":
                network_config.set_moderate_filter()
            elif filter_level == "strict":
                network_config.set_strict_filter()
            else:
                return JSONResponse({'error': 'Invalid filter level'})
        else:
            return JSONResponse({'error': 'No filter level specified (choose one of [none, low, moderate, strict]'})

        return JSONResponse({'success': 'success'})


@login_required
def marketplace_content_filter(request, *args, **kwargs):
    return ContentFilterHandler()(request, *args, **kwargs)


class MarketplaceOnOffHandler(RequestHandler):
    """
    Ajax handler for activating/deactivating the marketplace.
    Required data parameters:
    - activate: 'on' or 'off', to set the marketplace on or off.
    """
    def post(self):
        try:
            activate = self.request.POST.get('activate', 'true')
            mpx = CampaignQueryManager.get_marketplace(self.account)
            if activate == 'true':
                mpx.active = True
            elif activate == 'false':
                mpx.active = False

            CampaignQueryManager.put(mpx)
            return JSONResponse({'success': 'success'})
        except Exception, e:
            return JSONResponse({'error': e})


@login_required
def marketplace_on_off(request, *args, **kwargs):
    return MarketplaceOnOffHandler()(request, *args, **kwargs)


class MarketplaceBlindnessChangeHandler(RequestHandler):
    """
    Ajax handler for activating/deactivating blindness
    """
    def post(self):
        try:
            network_config = self.account.network_config

            # Some accounts won't have a network config yet
            if network_config == None:
                n = NetworkConfig(account=self.account).put()
                self.account.network_config = n
                self.account.put()
                network_config = n

            activate = self.request.POST.get('activate', None)
            if activate == 'true':
                network_config.blind = True
                network_config.put()
                return JSONResponse({'success': 'activated'})
            elif activate == 'false':
                network_config.blind = False
                network_config.put()
                return JSONResponse({'success': 'deactivated'})
            else:
                return JSONResponse({'error': 'Invalid activation value'})
            return JSONResponse({'success': str(self.request.POST)})
        except Exception, e:
            return JSONResponse({'error': e})


@login_required
def marketplace_blindness_change(request, *args, **kwargs):
    return MarketplaceBlindnessChangeHandler()(request, *args, **kwargs)


class MarketplaceCreativeProxyHandler(RequestHandler):
    """
    Ajax hander that proxies requests for creative data from mongo.
    This is done so that we can use SSL (users will get https errors
    when we hit mongo directly over http).
    """
    def get(self):
        url = "http://mpx.mopub.com/stats/creatives"
        query = "?" + "&".join([key + '=' + value for key, value in self.request.GET.items()])
        url += query
        response = urlfetch.fetch(url, method=urlfetch.GET, deadline=30).content

        return HttpResponse(response)


@login_required
def marketplace_creative_proxy(request, *args, **kwargs):
    return MarketplaceCreativeProxyHandler()(request, *args, **kwargs)



# Do we still need this?
class MPXInfoHandler(RequestHandler):
    def get(self):
        return render_to_response(self.request,
                                  "advertiser/mpx_splash.html",
                                  {})


@login_required
def mpx_info(request, *args, **kwargs):
    return MPXInfoHandler()(request, *args, **kwargs)
