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


class AppService(RequestHandler):
    """
    API Service for delivering serialized App data
    """
    def get(self, app_key=None):
        try:
            # If an app key is provided, return the single app
            if app_key:
                app = AppQueryManager.get_app_by_key(app_key)
                response = {
                    'apps': [app.toJSON()]
                }
            # If no app key is provided, return a list of all apps for the account
            else:
                apps = AppQueryManager.get_apps(self.account)
                response = {
                    'apps': [app.toJSON() for app in apps]
                }
            return JSONResponse(response)
        except Exception, e:
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
                logging.warn(adunits[0].toJSON())
                response = {
                    'app': app_key,
                    'adunits': [adunit.toJSON() for adunit in adunits]
                }
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