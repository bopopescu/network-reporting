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

from common.utils.request_handler import RequestHandler
from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.marketplace_helpers import MarketplaceStatsFetcher

from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.core.urlresolvers import reverse


import logging


class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None):
        try:
            # If an app key is provided, return the single app
            if app_key:
                apps = [AppQueryManager.get_app_by_key(app_key).toJSON()]
                mpxstats = MarketplaceStatsFetcher([app_key])

            # If no app key is provided, return a list of all apps for the account
            else:
                apps = [app.toJSON() for app in AppQueryManager.get_apps(self.account)]
                mpxstats = MarketplaceStatsFetcher([app['id'] for app in apps])

            # get stats for each app
            for app in apps:
                app.update(mpxstats.get_app_stats(str(app['id'])))

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
    return AppService()(request, *args, **kwargs)


class AdUnitService(RequestHandler):
    """
    API Service for delivering serialized AdUnit data
    """
    def get(self, app_key = None, adunit_key = None):
 #       try:
            if app_key:

                app = AppQueryManager.get_app_by_key(app_key)
                adunits = AdUnitQueryManager.get_adunits(app=app)
                mpxstats = MarketplaceStatsFetcher([app_key])

                response = [adunit.toJSON() for adunit in adunits]

                for au in response:
                    adunit_stats = mpxstats.get_adunit_stats(au['id'])
                    adunit_stats.update({'app_id':app_key})

                    adgroup = AdGroupQueryManager.get_marketplace_adgroup(au['id'],
                                                                          str(self.account.key()),
                                                                          get_from_db=True)
                    try:
                        au.update(price_floor = adgroup.mktplace_price_floor)
                    except AttributeError:
                        au.update(price_floor = "0.25")

                    au.update(adunit_stats)

                return JSONResponse(response)
            else:
                return JSONResponse({'error':'No parameters provided'})
#        except Exception, e:
#            logging.warn(e)
#            return JSONResponse({'error': str(e)})

    def post(self):
        pass

    def put(self, app_key = None, adunit_key = None):


        put_data = simplejson.loads(self.request.raw_post_data)
        try:
            new_price_floor = put_data['price_floor']

            account_key = self.account.key()
            adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit_key, account_key)

            adgroup.mktplace_price_floor = float(new_price_floor)
            AdGroupQueryManager.put(adgroup)

        except KeyError, e:
            return JSONResponse({'error':str(e)})

        return JSONResponse({'success':'success'})

    def delete(self):
        pass


@login_required
def adunit_service(request, *args, **kwargs):
    return AdUnitService()(request, *args, **kwargs)


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
    return CampaignService()(request, *args, **kwargs)


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
    return AdGroupService()(request, *args, **kwargs)


class CreativeService(RequestHandler):
    """
    API Service for delivering serialized Creative data
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
def creative_service(request, *args, **kwargs):
    return CreativeService()(request, *args, **kwargs)





