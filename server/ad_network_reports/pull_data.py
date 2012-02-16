import sys
import os
import csv
from datetime import date
sys.path.append(os.environ['PWD'])

from common.utils.connect_to_appengine import setup_remote_api
from common.utils import sswriter
from common.utils.date_magic import gen_days_for_range
from ad_network_reports.query_managers import AdNetworkLoginManager, \
        AD_NETWORK_NAMES
from ad_network_reports.models import AdNetworkNetworkStats, \
        AdNetworkStats
from publisher.models import App

STAT_NAMES = ['revenue', 'attempts', 'impressions', 'clicks', 'cpm', \
        'fill_rate', 'cpc', 'ctr']


def get_all_accounts_with_logins():
    logins_query = AdNetworkLoginManager.get_all_logins(order_by_account=
            True)
    last_account = None
    for login in logins_query:
        if login.account.key() != last_account:
            last_account = login.account.key()
            yield login.account

if __name__ == "__main__":
    setup_remote_api()

    days = gen_days_for_range(date(2012,1,15), 13)

    writer = csv.writer(open('network_data.csv', 'wb'))
    writer.writerow(['Email', 'Key', 'Main App', 'Network'] + STAT_NAMES)
    account_stats = []
    for account in [get_all_accounts_with_logins().next()]:
        for network in AD_NETWORK_NAMES.keys():
            network_stats = AdNetworkStats()
            for day in days:
                stats = AdNetworkNetworkStats.get_by_network_and_day(account,
                        network, day)
                if not stats:
                    break
                network_stats += stats
            if stats:
                apps = []
                apps.extend(App.all().filter('account =', account).fetch(limit=4))
                apps = ', '.join([app.full_name for app in apps])

                writer.writerow([account.emails[0], str(account.key()),
                    apps, AD_NETWORK_NAMES[network]] +
                    [network_stats.dict_[stat_name] for stat_name in STAT_NAMES])

