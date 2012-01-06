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
     DirectSoldStatsFetcher, \
     AdNetworkStatsFetcher
from common.utils import date_magic
from common.utils.timezones import Pacific_tzinfo
from common_templates.templatetags.filters import campaign_status

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
            logging.warn(self.request.GET)
            # if settings.DEBUG:
            #     mpxstats = MarketplaceStatsFetcher("agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww")
            # else:
            mpxstats = MarketplaceStatsFetcher(self.account.key())
            # If an app key is provided, return the single app
            if app_key:
                apps = [AppQueryManager.get_app_by_key(app_key).toJSON()]


            # If no app key is provided, return a list of all apps for the account
            else:
                apps = [app.toJSON() for app in AppQueryManager.get_apps(self.account)]


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

            # get stats for each app
            for app in apps:
                # if settings.DEBUG:
                #     app.update(mpxstats.get_app_stats("agltb3B1Yi1pbmNyDAsSA0FwcBiLo_8DDA", start_date, end_date))
                # else:
                app.update(mpxstats.get_app_stats(str(app['id']), start_date, end_date))

            return JSONResponse(apps)

        except Exception, e:
            logging.warn(e)
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
            mpxstats = MarketplaceStatsFetcher(self.account.key())

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



            logging.warn(start_date)
            logging.warn(end_date)


            if app_key:

                app = AppQueryManager.get_app_by_key(app_key)
                adunits = AdUnitQueryManager.get_adunits(app=app)

                response = [adunit.toJSON() for adunit in adunits]

                for au in response:
                    # if settings.DEBUG:
                    #     adunit_stats = mpxstats.get_adunit_stats("agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw", start_date, end_date)
                    # else:
                    adunit_stats = mpxstats.get_adunit_stats(au['id'], start_date, end_date)
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
                return JSONResponse({'error': 'No parameters provided'})
        except Exception, e:
            logging.warn(e)
            return JSONResponse({'error': str(e)})

    def post(self):
        pass

    def put(self, app_key = None, adunit_key = None):

        put_data = simplejson.loads(self.request.raw_post_data)
        logging.warn(put_data)
#        try:
        new_price_floor = put_data['price_floor']
        activity = put_data['active']

        account_key = self.account.key()
        adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key, account_key)

        adgroup.mktplace_price_floor = float(new_price_floor)
        adgroup.active = activity
        AdGroupQueryManager.put(adgroup)

#        except KeyError, e:
 #           logging.warn(e)
  #          return JSONResponse({'error':str(e)})

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
    def get(self):
        return JSONResponse({'error':'No parameters provided'})

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


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


class AppOnNetworkService(RequestHandler):
    """
    API Service for delivering serialized app on network data
    """
    def get(self, network, pub_id=''):
        try:

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
            days = date_magic.gen_days(start_date, end_date)

            # If an app key is provided get only stats for that app
            if pub_id:
                return JSONResponse(AdNetworkStatsFetcher.get_app_stats(
                    network, days, pub_id))
            # If no app key is provided, return stats rolled up stats for the
            # network and account
            return JSONResponse(AdNetworkStatsFetcher.get_stats(
                self.account, network, days))

        except Exception, e:
            logging.warn("APPS ON NETWORK FETCH ERROR "  + str(e))
            return JSONResponse({'error': str(e)})


@login_required
def app_on_network_service(request, *args, **kwargs):
    return AppOnNetworkService()(request, use_cache=False, *args, **kwargs)

