from django.http import Http404
from common.utils.date_magic import gen_days

from account.query_managers import AccountQueryManager
from publisher.query_managers import AppQueryManager

from ad_network_reports.models import AdNetworkStats
from ad_network_reports.query_managers import AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkNetworkStatsManager, \
        AdNetworkAppStatsManager, \
        AdNetworkStatsManager

# helpers
def get_all_stats(app_key, network, account_key, start_date, end_date):
    days = gen_days(start_date, end_date)

    account = AccountQueryManager.get(account_key)

    if app_key != '*':
        app = AppQueryManager.get(app_key)
        # sanity check
        if app.account.key() != account.key():
            raise Http404
    else:
        app = None

    if network == '*':
        network = None

    if network:
        network = network.replace('_native', '').lower()
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

    all_stats = [stats if stats else AdNetworkStats(date=day) for stats, day in
            zip(all_stats, days)]

    return api_format(app_key, network, account_key, all_stats)

def api_format(app_key, network, account_key, all_stats):
    """
    return stats dict formatted for json response
    """
    return {app_key + '||' + network + '||' + account_key:
        {'daily_stats': [{'rev': stats.revenue,
                         'imp': stats.impressions,
                         'att': stats.attempts,
                         'clk': stats.clicks,
                         'date': stats.date.strftime('%Y-%m-%d'),}
                         for stats in all_stats],
         'sum': {'rev': sum([stats.revenue for stats in all_stats]),
                 'imp': sum([stats.impressions for stats in
                     all_stats]),
                 'att': sum([stats.attempts for stats in all_stats]),
                 'clk': sum([stats.clicks for stats in all_stats]),}}}

