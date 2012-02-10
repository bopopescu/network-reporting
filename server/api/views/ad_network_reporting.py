import datetime
import logging

from django.utils import simplejson
from django.contrib.auth.decorators import login_required

from common.utils import date_magic
from common.utils.timezones import Pacific_tzinfo
from common.utils.request_handler import RequestHandler
from common.ragendja.template import JSONResponse
from common.utils.stats_helpers import AdNetworkStatsFetcher
from publisher.query_managers import AppQueryManager

## Ad Network Services

class Types:
    APP = 'app'
    NETWORK = 'network'


class AccountRollUpService(RequestHandler):
    """
    API Service for delivering serialized precalculated roll up stats at the
    account level
    """

    def get(self):

        # Formulate the date range
        days = get_days(self.request)

        # Return rolled up stats at the accout level
        return JSONResponse(AdNetworkStatsFetcher.get_account_roll_up_stats(
            self.account, days))


@login_required
def account_roll_up_service(request, *args, **kwargs):
    return AccountRollUpService()(request, use_cache=False, *args, **kwargs)

class DailyStatsService(RequestHandler):
    """
    API Service for delivering serialized chart data for the ad network revenue
    reporting index page
    """
    def get(self):

        # Formulate the date range
        days = get_days(self.request)

        # Get only stats for that app
        return JSONResponse(AdNetworkStatsFetcher.get_daily_stats(
            self.account, days))


@login_required
def daily_stats_service(request, *args, **kwargs):
    return DailyStatsService()(request, use_cache=False, *args, **kwargs)

class RollUpService(RequestHandler):
    """
    API Service for delivering serialized precalculated roll up stats for ad
    networks
    """

    def get(self, type_, id_):

        # Formulate the date range
        days = get_days(self.request)

        # Return stats rolled up stats for the network and account
        if type_ == Types.APP:
            return JSONResponse(AdNetworkStatsFetcher.get_roll_up_stats(
                self.account, days, app=AppQueryManager.get_app_by_key(id_)))
        elif type_ == Types.NETWORK:
            return JSONResponse(AdNetworkStatsFetcher.get_roll_up_stats(
                self.account, days, network=id_))


@login_required
def roll_up_service(request, *args, **kwargs):
    return RollUpService()(request, use_cache=False, *args, **kwargs)

class AppOnNetworkService(RequestHandler):
    """
    API Service for delivering serialized app on network data
    """
    def get(self, network, pub_id):

        # Formulate the date range
        days = get_days(self.request)

        # Get only stats for that app
        return JSONResponse(AdNetworkStatsFetcher.get_app_on_network_stats(
            network, days, pub_id))


@login_required
def app_on_network_service(request, *args, **kwargs):
    return AppOnNetworkService()(request, use_cache=False, *args, **kwargs)


def get_days(request):
    if request.GET.get('s', None):
        year, month, day = str(request.GET.get('s')).split('-')
        start_date = datetime.date(int(year), int(month), int(day))
    else:
        start_date = datetime.date.today()
    days_in_range = int(request.GET.get('r'))

    return date_magic.gen_days_for_range(start_date, days_in_range)
