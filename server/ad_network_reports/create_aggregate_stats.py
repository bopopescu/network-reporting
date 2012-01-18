from ad_network_reports.models import AdNetworkScrapeStats
from ad_network_reports.query_managers import AdNetworkStatsManager

MAX = 1000

# Two possible approaches:
# 1. Query for all scrape stats and then put them in the right structures
# 2. Query scrape stats by account and day and then create aggregates
# appropriately

def bulk_get(query, last_object):
    return query.filter('__key__ >', last_object).fetch(MAX)

stats_query = AdNetworkScrapeStats.all()
stats_list = stats_query.fetch(MAX)

count = 0
while stats_list:
    all_stats = []
    network_stats = {}
    app_stats = {}
    apps_by_key = {}
    accounts_by_key = {}
    for stats in stats_list:
        mapper = stats.ad_network_app_mapper
        account = mapper.ad_network_login.account

        # Fill in app stats dict
        key = (mapper.application.key(), account.key(), stats.date)
        if key in app_stats:
            print "Appending to app stats dict"
            app_stats[key].append(stats)
        else:
            print "Creating new entry in app stats dict"
            app_stats[key] = [stats]
            apps_by_key[mapper.application.key()] = mapper.application
            accounts_by_key[account.key()] = account

        # Fill in network stats dict
        key = (mapper.ad_network_name, account.key(), stats.date)
        if key in app_stats:
            print "Appending to network stats dict"
            app_stats[key].append(stats)
        else:
            print "Creating new entry in network stats dict"
            app_stats[key] = [stats]

        last_stats = stats

    # Create network stats
    for key, stats_list in network_stats.iteritems():
        network, account_key, day = key
        network_stats = AdNetworkAggregateManager.find_or_create(
                account=accounts_by_key[account_key], day=day,
                network=network)
        AdNetworkStatsManager.combined_stats(network_stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        all_stats.append(network_stats)

    # Create app stats
    for key, stats_list in app_stats.iteritems():
        app_key, account_key, day = key
        app_stats = AdNetworkAggregateManager.find_or_create(
                account=accounts_by_key[account_key], day=day,
                app=apps_by_key[app_key])
        AdNetworkStatsManager.combined_stats(app_stats,
                AdNetworkStatsManager.roll_up_stats(stats_list))
        all_stats.append(app_stats)

    # Put all stats
    #db.put(all_stats)

    count += 1
    # Print where we are
    print "%d last_account: %s" % (count * MAX, last_account.key())

    # Get next set of scrape stats
    stats_list = bulk_get(stats_query, last_stats)


