from ad_network_reports.models import AdNetworkLoginCredentials, \
        AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        AdNetworkNetworkStats, \
        AdNetworkAppStats
from ad_network_reports.query_managers import AdNetworkStatsManager, \
        AdNetworkLoginManager
from common.utils import date_magic
from common.utils.helpers import get_all

from datetime import date, datetime, timedelta
from google.appengine.ext import db

MAX = 1000

# Two possible approaches:
# 1. Query for all scrape stats and then put them in the right structures
# 2. Query scrape stats by account and day and then create aggregates
# appropriately

class Modes:
    NAIVE = 0
    BY_ACCOUNT_AND_DAY = 1

mode = Modes.NAIVE

def bulk_get(query, last_object):
    return query.filter('__key__ >', last_object).fetch(MAX)

# 1
if mode == Modes.NAIVE:
    print "Getting all logins"
    # Get all logins
    logins_dict = {}
    logins = get_all(AdNetworkLoginCredentials, limit=10000)
    for login in logins:
        logins_dict[login.key()] = login

    print "Getting all mappers"
    # Get all mappers
    mappers_dict = {}
    mappers = get_all(AdNetworkAppMapper, limit=10000)
    for mapper in mappers:
        mappers_dict[mapper.key()] = mapper

    stats_query = AdNetworkScrapeStats.all()
    stats_list = stats_query.fetch(MAX)

    print
    print "Starting traversal of scrape stats"
    print
    apps_dict = {}
    apps_set = set()
    accounts_dict = {}
    accounts_set = set()

    all_stats = []
    network_stats = {}
    app_stats = {}
    count = 0
    while stats_list:
        for stats in stats_list:
            try:
                mapper = mappers_dict[stats._ad_network_app_mapper]
                account_key = logins_dict[mapper._ad_network_login]._account

                # Fill in app stats dict
                key = (mapper._application, account_key, stats.date)
                if key in app_stats:
                    print "Appending to app stats dict"
                    print key
                    app_stats[key].append(stats)
                else:
                    print "Creating new entry in app stats dict"
                    print key
                    app_stats[key] = [stats]

                # Fill in network stats dict
                key = (mapper.ad_network_name, account_key, stats.date)
                if key in network_stats:
                    print "Appending to network stats dict"
                    print key
                    network_stats[key].append(stats)
                else:
                    print "Creating new entry in network stats dict"
                    print key
                    network_stats[key] = [stats]
            except KeyError:
                pass

            last_stats = stats

        print "Appending to apps_set and accounts_set"
        # key = (app_key, account_key, day)
        # Get list of unique app and account keys that aren't already indexed
        app_keys, account_keys = zip(*[(key[0], key[1]) for key, stats_list in
            app_stats.iteritems()])
        for app_key in app_keys:
            apps_set.add(app_key)
        #app_keys = [app_key for app_key in app_keys if app_key not in app_dict]
        for account_key in account_keys:
            accounts_set.add(account_key)
        #account_keys = [account_key for account_key in account_keys if account_key not in account_dict]

        count += 1
        # Print where we are
        print
        print "%d last_stats: %s" % (count * MAX, last_stats.key())
        print

        # Get next set of scrape stats
        stats_list = bulk_get(stats_query, last_stats)


    print "Getting and indexing apps"
    # Get and index Apps
    apps = db.get(list(apps_set))
    for app in apps:
        apps_dict[app.key()] = app

    print "Getting and indexing accounts"
    # Get and index Accounts
    accounts = db.get(list(accounts_set))
    for account in accounts:
        accounts_dict[account.key()] = account

    print "Creating %d AppStats" % len(app_stats)
    # Create app stats
    for key, stats_list in app_stats.iteritems():
        app_key, account_key, day = key
        app_stats = AdNetworkAppStats(account=accounts_dict[account_key],
                                      date=day,
                                      application=apps_dict[app_key])
        AdNetworkStatsManager.copy_stats(app_stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        all_stats.append(app_stats)

    print "Creating %d NetworkStats" % len(network_stats)
    # Create network stats
    for key, stats_list in network_stats.iteritems():
        network, account_key, day = key
        network_stats = AdNetworkNetworkStats(account=accounts_dict[account_key],
                                              date=day,
                                              ad_network_name=network)
        AdNetworkStatsManager.copy_stats(network_stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        all_stats.append(network_stats)

    print "Putting all stats to the db"
    # Put all stats
    db.put(all_stats)


#2
elif mode == Modes.BY_ACCOUNT_AND_DAY:
    yesterday = date.today() - timedelta(days=2)

    start_day = yesterday - timedelta(days=14)
    end_day = yesterday

    def get_all_accounts_with_logins():
        logins_query = AdNetworkLoginManager.get_all_logins(
                order_by_account=True)
        logins = logins_query.fetch(MAX)
        last_account = None
        while logins:
            for login in logins:
                if login.account.key() != last_account:
                    last_account = login.account.key()
                    yield login.account
            logins = bulk_get(login_query, login)

    def get_stats(account, day):
        logins = account.login_credentials
        mappers = []
        for login in logins:
            for mapper in login.ad_network_app_mappers:
                mappers.append(mapper)
        return [stats for stats in AdNetworkScrapeStats.get_by_key_name(['k:%s:%s' %
            (mapper.key(), day) for mapper in mappers]) if stats != None]

    days = date_magic.gen_days(start_day, end_day)

    all_stats = []
    for account in get_all_accounts_with_logins():
        for day in days:
            stats_list = get_stats(account, day)

            if stats_list:
                network_stats = {}
                app_stats = {}
                apps_by_key = {}
                for stats in stats_list:
                    try:
                        mapper = stats.ad_network_app_mapper

                        # Fill in app stats dict
                        key = mapper.application.key()
                        if key in app_stats:
                            print "Appending to app stats dict"
                            app_stats[key].append(stats)
                        else:
                            print "Creating new entry in app stats dict"
                            app_stats[key] = [stats]
                            apps_by_key[mapper.application.key()] = mapper.application

                        # Fill in network stats dict
                        key = mapper.ad_network_name
                        if key in network_stats:
                            print "Appending to network stats dict"
                            network_stats[key].append(stats)
                        else:
                            print "Creating new entry in network stats dict"
                            network_stats[key] = [stats]
                    except db.ReferencePropertyResolveError:
                        pass

                # Create network stats
                for network, stats_list in network_stats.iteritems():
                    network_stats = AdNetworkNetworkStats(
                            account=account,
                            date=day,
                            ad_network_name=network)
                    AdNetworkStatsManager.copy_stats(network_stats,
                            AdNetworkStatsManager.roll_up_stats(stats_list))
                    all_stats.append(network_stats)

                # Create app stats
                for app_key, stats_list in app_stats.iteritems():
                    app_stats = AdNetworkAppStats(
                            account=account,
                            date=day,
                            application=apps_by_key[app_key])
                    AdNetworkStatsManager.combined_stats(app_stats,
                            AdNetworkStatsManager.roll_up_stats(stats_list))
                    all_stats.append(app_stats)

            if len(all_stats) > MAX:
                print "Putting all_stats"
                #db.put(all_stats)
                all_stats = []

