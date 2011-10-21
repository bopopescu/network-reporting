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
from django.contrib.auth.decorators import login_required
from django.utils import simplejson
from django.core.urlresolvers import reverse

import logging
import random

class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None):
        try:
            # If an app key is provided, return the single app
            if app_key:
                mpxstats = MarketplaceStatsFetcher(app_keys = [app_key])
                apps = [AppQueryManager.get_app_by_key(app_key).toJSON()]

            # If no app key is provided, return a list of all apps for the account
            else:
                apps = [app.toJSON() for app in AppQueryManager.get_apps(self.account)]
                mpxstats = MarketplaceStatsFetcher(app_keys = [app['id'] for app in apps])

            # get stats for each app
            for app in apps:
                app.update(mpxstats.get_app_stats(str(app['id'])))

            logging.warn(apps)
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
    def get(self, app_key = None):
        try:
            if app_key:
                app = AppQueryManager.get_app_by_key(app_key)
                adunits = AdUnitQueryManager.get_adunits(app=app)
                extra_data = {
                    'app_id': app_key
                }
                response = [adunit.toJSON() for adunit in adunits]
                for d in response:
                    d.update(extra_data)
                logging.warn(response)
                return JSONResponse(response)
            else:
                return JSONResponse({'error':'No parameters provided'})
        except Exception, e:
            return JSONResponse({'error': str(e)})

    def post(self):
        pass

    def put(self):
        pass

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


class MarketplaceStatsFetcher(object):
    def __init__(self, app_keys = None, adunit_keys = None, account_keys = None):
        if not app_keys or adunit_keys or account_keys:
            raise Exception("Fuck you, pass in something")

            # payload = urllib2.urlopen('blah').read()
        payload = {}

        self.payload = payload

    def get_app_stats(self, app_key):
        return {
            "revenue": random.randint(1, 900),
            "impressions": random.randint(1, 10000),
            "clicks": random.randint(1, 1000),
        }

    def get_adunit_stats(self, adunit_key):
        return {
            "revenue": random.randint(1, 100),
            "impressions": random.randint(1, 10000),
            "clicks": random.randint(1, 1000),
        }

    def get_account_stats(self, account_key):
        return {
            "revenue": random.randint(1, 10000),
            "impressions": random.randint(1, 100000),
            "clicks": random.randint(1, 1000),
        }