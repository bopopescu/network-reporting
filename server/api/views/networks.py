import logging
from datetime import datetime, date

from common.utils.request_handler import RequestHandler
from common.utils.date_magic import gen_days
from common.ragendja.template import JSONResponse
from django.http import Http404

from account.query_managers import AccountQueryManager
from publisher.query_managers import AppQueryManager
# TODO: on merge of new networks uncomment NetworkStats stuff
#from advertiser.models import NetworkStates
from advertiser.query_managers import CampaignQueryManager

from ad_network_reports.models import AdNetworkStats
from ad_network_reports.query_managers import AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkNetworkStatsManager, \
        AdNetworkAppStatsManager, \
        AdNetworkStatsManager

class NetworksApi(RequestHandler):
    def get(self):
        app_key = self.request.GET.get('app')
        campaign_key = self.request.GET.get('campaign')
        account_key = self.request.GET.get('account')

        start_date = datetime.strptime(self.request.GET.get('start_date'),
                '%Y-%m-%d').date()
        end_date = datetime.strptime(self.request.GET.get('end_date'),
                '%Y-%m-%d').date()

        all_stats = get_all_stats(app_key, campaign_key, account_key,
                start_date, end_date)

        return JSONResponse({'status': 200,
                             'all_stats': all_stats})

    def post(self):
        # what I want to do:
        #arg_list = self.request.POST.get('arg_list')
        # TODO: find in api / be smarter
        arg_list = []
        arg_exists = True
        counter = 0
        while arg_exists:
            args = {}
            for field in ['app', 'campaign', 'account']:
                args[field] = self.request.POST.get('arg_list[%s][%s]' %
                        (counter, field), None)
                if not args[field]:
                    arg_exists = False
                    break
            if args['app']:
                arg_list.append(args)
                counter += 1

        start_date = datetime.strptime(self.request.POST.get('start_date'),
                '%Y-%m-%d').date()
        end_date = datetime.strptime(self.request.POST.get('end_date'),
                '%Y-%m-%d').date()

        # get stats for each arg in the arg list and put them into a single
        # dict
        temp_stats = [get_all_stats(args['app'], args['campaign'],
            args['account'], start_date, end_date).items() for args in
            arg_list]
        logging.info(temp_stats)
        all_stats = dict(sum(temp_stats, []))

        return JSONResponse({'status': 200,
                             'all_stats': all_stats})

def networks_api(request, *args, **kwargs):
    return NetworksApi()(request, *args, **kwargs)

# helpers
def get_all_stats(app_key, campaign_key, account_key, start_date, end_date):
    days = gen_days(start_date, end_date)

    account = AccountQueryManager.get(account_key)

    if app_key != '*':
        app = AppQueryManager.get(app_key)
        # sanity check
        if app.account.key() != account.key():
            raise Http404
    else:
        app = None

    if campaign_key != '*':
        campaign = CampaignQueryManager.get(campaign_key)
        # sanity check
        if campaign.account.key() != account.key():
            raise Http404
    else:
        campaign = None

    if campaign:
#            if campaign.network_state == \
#                    NetworkStates.DEFAULT_NETWORK_CAMPAIGN:
#                network = campaign.network_type
        network = campaign.adgroups.get().network_type.replace('_native',
                '').lower()
        if app:
            login = AdNetworkLoginManager.get_logins(account,
                    network=network).get()
            # multiple mappers can exist for an app if the pub id has
            # changed
            mappers = AdNetworkMapperManager.get_mappers_for_app(
                    login=login, app=app)
            # sum stats accross day for each list of mapper stats by
            # day
            all_stats = [sum(stats, AdNetworkStats()) for stats in zip(*[
                AdNetworkStatsManager.get_stats_for_days(mapper.key(),
                    days) for mapper in mappers])]
        else:
            all_stats = AdNetworkNetworkStatsManager.get_stats_for_days(
                    account, network, days)
#            else:
#                # create empty models
#                all_stats = [AdNetworkStats(date=day) for day in days]
    else:
        if app:
            all_stats = AdNetworkAppStatsManager.get_stats_for_days(account,
                    app, days)
        else:
            # get the networks that this account could have stats for
            networks = [login.ad_network_name for login in
                    AdNetworkLoginManager.get_logins(account)]
            # get all network stats and sum for each day
            all_stats = [sum(stats, AdNetworkStats()) for stats in \
                    zip(*[AdNetworkNetworkStatsManager.get_stats_for_days(
                        account, network, days) for network in networks])]

    if not all_stats:
        # create empty models
        all_stats = [AdNetworkStats(date=day) for day in days]

    return api_format(app_key, campaign_key, account_key, all_stats)

def api_format(app_key, campaign_key, account_key, all_stats):
    """
    return stats dict formatted for json response
    """
    return {app_key + '||' + campaign_key + '||' + account_key:
        {'daily_stats': [{'revenue': stats.revenue,
                         'impression_count': stats.impressions,
                         'attempt_count': stats.attempts,
                         'click_count': stats.clicks,
                         'date': stats.date.strftime('%Y-%m-%d'),}
                         for stats in all_stats],
         'sum': {'revenue': sum([stats.revenue for stats in all_stats]),
                 'impression_count': sum([stats.impressions for stats in
                     all_stats]),
                 'attempt_count': sum([stats.attempts for stats in all_stats]),
                 'click_count': sum([stats.clicks for stats in all_stats]),}}}

