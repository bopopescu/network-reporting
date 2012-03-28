import copy
import string
import random
import datetime

from account.query_managers import AccountQueryManager
from advertiser.query_managers import AdGroupQueryManager
from reporting.query_managers import StatsModelQueryManager

#
## TODO: make imports explicit
from registration.models import *
from advertiser.models import *
from publisher.models import *
from account.models import *
from budget.models import *
from reporting.models import *

#
## Imports to generate networks page data
from common.constants import REPORTING_NETWORKS, \
        NETWORKS_WITHOUT_REPORTING, \
        NETWORKS, \
        NETWORK_ADGROUP_TRANSLATION

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkStats, \
     AdNetworkScrapeStats, \
     AdNetworkNetworkStats, \
     AdNetworkAppStats

from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager

####
#Configuration Parameters for data generation
####

USERNAME = "test@mopub.com"
PASSWORD = "test"

NUM_ACCOUNTS = 1
NUM_APPS = 2 #ONLY SUPPORT ONE ACCOUNT FOR NOW
NUM_CAMPAIGNS_PER_APP = 1#3
NUM_CREATIVES_PER_ADGROUP = 1
NUM_ADUNITS_PER_APP = 2#3

NETWORKS_TO_USE = ['admob', 'iad']
APP_STATS_SINCE = datetime.datetime.now() - datetime.timedelta(days=14)

### End configuration parameters


####
#Constants
####

APP_INDEX = 0
ADUNIT_INDEX = 0
CAMPAIGN_INDEX = 0
CREATIVE_INDEX = 0
ADGROUP_INDEX= 0
APP_TYPES = ['iphone','android','ipad','mweb']
COLOR_ALPH = string.digits + "ABCDEF"
CAMPAIGN_TYPES = ['gtee', 'gtee_high', 'gtee_low', 'promo', 'network','backfill_promo', 'marketplace', 'backfill_marketplace']
NETWORK_TYPES = ["adsense", "iAd", "admob","millennial","ejam","chartboost","appnexus","inmobi","mobfox","jumptap","brightroll","greystripe", "custom", "custom_native", "admob_native", "millennial_native"]
BID_STRATEGIES = ['cpc','cpm','cpa']

NETWORK_TYPE_TO_PUB_ID_ATTR = {'dummy':'',
                               'adsense':'adsense_pub_id',
                               'iAd':'',
                               'admob':'admob_pub_id',
                               'millenial':'millenial_pub_id',
                               'ejam':'ejam_pub_id',
                               'chartboost':'chartboost_pub_id',
                               'appnexus':'appnexus_pub_id',
                               'inmobi':'inmobi_pub_id',
                               'jumptap':'jumptap_pub_id',
                               'brightroll':'brightroll_pub_id',
                               'greystripe':'greystripe_pub_id'}


####
#Helper Methods
####

def get_adgroup_name():
    global ADGROUP_INDEX
    ADGROUP_INDEX+=1
    return "adgroup%s" % ADGROUP_INDEX


def get_creative_name():
    global CREATIVE_INDEX
    CREATIVE_INDEX+=1
    return "creative%s" % CREATIVE_INDEX

def get_app_name():
    global APP_INDEX
    APP_INDEX+=1
    return "app%s" % APP_INDEX

def get_adunit_name():
    global ADUNIT_INDEX
    ADUNIT_INDEX+=1
    return "adunit%s" % ADUNIT_INDEX

def get_campaign_name():
    global CAMPAIGN_INDEX
    CAMPAIGN_INDEX+=1
    return "campaign%s" % CAMPAIGN_INDEX

def get_random_color():
    return "".join([select_rand(COLOR_ALPH) for i in range(5)])

def select_rand(array):
    return array[random.randint(0,len(array)-1)]

def select_rand_subset(array):
    num_elements = random.randint(1,len(array)-1)
    cloned = copy.copy(array)
    random.shuffle(cloned)
    return cloned[:num_elements]


def get_random_date():
    today = datetime.date.today()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return datetime.date(year,month,day)

def get_random_datetime():
    today = datetime.datetime.now()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return datetime.datetime(year,month,day)


####
#Generation methods
####


def generate_app(account):
    app = App(name=get_app_name(),
              app_type=select_rand(APP_TYPES),
              account = account)
    app.put()
    return app


def generate_adunit(app,account):
    adunit = AdUnit(app_key = app,
                    account = account,
                    name = get_adunit_name(),
                    color_border = get_random_color(),
                    color_bg = get_random_color(),
                    color_link = get_random_color(),
                    color_text = get_random_color(),
                    color_url = get_random_color())
    adunit.put()
    return adunit

def generate_budget():
    start_date = get_random_datetime()
    end_date = get_random_datetime()
    if start_date > end_date:
        temp = start_date
        start_date = end_date
        end_date = temp
    budget = Budget(start_datetime=start_date,
                    end_datetime = end_date,
                    static_total_budget = float(random.randint(100,1000)),
                    static_slice_budget = float(random.randint(100,1000)))

    budget.put()
    return budget


def generate_adgroup(site_keys,account,campaign=None,network=None):
    if campaign:
        if campaign.campaign_type=="network":
            if network:
                adgroup = AdGroupQueryManager.get_network_adgroup(campaign.key(), site_keys[0],
                         account.key(), network)
                adgroup.put()
                return adgroup
            else:
                network = select_rand(NETWORK_TYPES)

            #Need to update account's network configuration if we add a network adgroup
            if network in NETWORK_TYPE_TO_PUB_ID_ATTR.keys():
                network_config = account.network_config
                setattr(network_config,NETWORK_TYPE_TO_PUB_ID_ATTR[network],"fillerid")
                a = AccountQueryManager()
                a.update_config_and_put(account,network_config)

        adgroup = AdGroup(campaign=campaign,
                      network_type=network if campaign.campaign_type=="network" else None,
                      bid_strategy=select_rand(BID_STRATEGIES),
                      account=account,
                      site_keys=site_keys,
                      name=get_adgroup_name())

    else:
        adgroup = AdGroup(network_type=network,
                          bid_strategy='cpm',
                          account=account,
                          site_keys=site_keys,
                          name=get_adgroup_name())
    adgroup.put()

    return adgroup



def generate_campaign(account,budget,campaign_type=None):
    start_date = get_random_date()
    end_date = get_random_date()
    if start_date> end_date:
        temp = start_date
        start_date = end_date
        end_date = temp
    campaign = Campaign(name=get_campaign_name(),
                        budget_obj = budget,
                        campaign_type = campaign_type if campaign_type else select_rand(CAMPAIGN_TYPES),
                        account = account,
                        start_date = start_date,
                        end_date = end_date)
    campaign.put()
    return campaign



def generate_account(username=USERNAME,password=PASSWORD,email=USERNAME,marketplace_config=None,network_config=None):
    if not marketplace_config:
        marketplace_config = MarketPlaceConfig()
        marketplace_config.put()
    if not network_config:
        network_config = NetworkConfig()
        network_config.put()

    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False,username=username,password=password,email=email)
    manager.create_profile(user)

    account = AccountQueryManager().get_current_account(user=user)
    account.active = True
    account.marketplace_config = marketplace_config
    account.network_config = network_config

    account.put()
    return account

def generate_networkconfig():
    networkconfig = NetworkConfig()
    networkconfig.put()
    return networkconfig

def generate_marketplace_config():
    marketplace_config = MarketPlaceConfig()
    marketplace_config.put()
    return marketplace_config


def generate_stats_model(publisher,advertiser,account,date):
    #This logic is in place to make the stats more realistic
    request_count = random.randint(0,10000)
    impression_count = int(random.random()*request_count)
    click_count = int(random.random()*impression_count)
    conversion_count = int(random.random()*click_count)
    revenue = click_count*.5

    user_count = int(request_count*.75)
    request_user_count = user_count
    impression_user_count =int(request_user_count * random.random())
    click_user_count = int(impression_user_count * random.random())

    stats_model = StatsModel(publisher = publisher,
                             advertiser = advertiser,
                             account = account,
                             revenue = revenue,
                             date = date,
                             request_count = request_count,
                             impression_count = impression_count,
                             click_count = click_count,
                             conversion_count = conversion_count,
                             user_count = user_count,
                             request_user_count = request_user_count,
                             impression_user_count = impression_user_count,
                             click_user_count = click_user_count)

    return stats_model


def generate_creative(account,adgroup):
    creative_name = get_creative_name()

    #For now, test data generation will only create basic text creatives
    creative = TextCreative(active=True,
                            account = account,
                            ad_group = adgroup,
                            ad_type = "text",
                            headline = "%s %s" % (creative_name,"headline"),
                            line1 = "%s %s" % (creative_name,"line1"),
                            line2 = "%s %s" % (creative_name,"line2"),
                            name=creative_name)
    creative.put()
    return creative




#Example Method to generate data. See top configuration contants for customizing result
def main_():
    account = generate_account(USERNAME,PASSWORD,USERNAME)

    apps = []
    for i in range(NUM_APPS):
        apps.append(generate_app(account))

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,[]) for app in apps])
    creatives_per_campaign = {}

    for app in apps:
        for i in range(NUM_ADUNITS_PER_APP):
            adunits_per_app[app].append(generate_adunit(app,account))

        all_site_keys = [a.key() for a in AdUnit.all() if a._account == account.key()]

        for i in range(NUM_CAMPAIGNS_PER_APP):
            budget = generate_budget()

            if i==0:
                #create at least 1 network campaign
                campaign = generate_campaign(account,budget,"network")

            elif i==1:
                #create at least 1 marketplace campaign
                campaign = generate_campaign(account,budget,"marketplace")

            else:
                campaign = generate_campaign(account,budget)

            creatives_per_campaign[campaign] = []
            campaigns_per_app[app].append(campaign)
            adgroup = generate_adgroup(select_rand_subset(all_site_keys),
                                       account,
                                       campaign=campaign)
            for i in range(NUM_CREATIVES_PER_ADGROUP):
                creatives_per_campaign[campaign].append(generate_creative(account,adgroup))


    today = datetime.datetime.now()
    day = datetime.timedelta(days=1)

    s = StatsModelQueryManager(account=account)

    for app in apps:
        cur_date = APP_STATS_SINCE
        while cur_date<=today:
            for campaign in campaigns_per_app[app]:
                stats= [generate_stats_model(adunit,
                                             creative,
                                             account,
                                             cur_date)
                        for creative in creatives_per_campaign[campaign]
                        for adunit in adunits_per_app[app]]

                req_stats = [generate_stats_model(adunit,None,account,cur_date) for adunit in adunits_per_app[app]]
                for stat in req_stats:
                    stat.impression_count = stat.click_count = stat.conversion_count = 0

                s.put_stats(stats=stats+req_stats)

            cur_date+=day


def main():
    account = generate_account(USERNAME,PASSWORD,USERNAME)

    apps = []
    for i in range(NUM_APPS):
        apps.append(generate_app(account))

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,set()) for app in apps])

    reporting_networks = set(NETWORKS_TO_USE).intersection(set(
        REPORTING_NETWORKS.keys()))

    # Generate logins and initialize login_by_network dict
    login_by_network = {}
    for network in reporting_networks:
        login = AdNetworkLoginCredentials(account=account,
                           ad_network_name=network,
                           client_key=str(random.random()*10),
                           send_email=False)
        login_by_network[network] = login
        login.put()

    # Generate campaigns and the data structures required to quickly access them
    campaigns_by_network = {}
    creatives_per_campaign = {}
    campaigns = []
    for network in NETWORKS_TO_USE:
        campaign = Campaign(account=account,
                campaign_type='network',
                network_type=network,
                network_state=NetworkStates.DEFAULT_NETWORK_CAMPAIGN,
                name=REPORTING_NETWORKS.get(network, False) or \
                        NETWORKS_WITHOUT_REPORTING[network])
        campaign.put()

        creatives_per_campaign[campaign] = []
        campaigns_by_network[network] = campaign
        campaigns.append(campaign)

    # Generate adunits, adgroups, network_configs and mappers
    for app in apps:
        for i in range(NUM_ADUNITS_PER_APP):
            adunit = generate_adunit(app,account)
            adunits_per_app[app].append(adunit)
            for network in NETWORKS_TO_USE:
                campaign = campaigns_by_network[network]

                adgroup_network_type = network
                if network in NETWORK_ADGROUP_TRANSLATION:
                    adgroup_network_type = NETWORK_ADGROUP_TRANSLATION[network]
                adgroup = generate_adgroup([adunit.key()],
                                           account,
                                           campaign=campaign,
                                           network=adgroup_network_type)

                for i in range(NUM_CREATIVES_PER_ADGROUP):
                    creative = generate_creative(account,adgroup)
                    creatives_per_campaign[campaign].append(creative)

        all_site_keys = [a.key() for a in AdUnit.all() if a._account ==
                account.key()]

        network_config = generate_networkconfig()
        app.network_config = network_config
        app.put()

        # Create mappers and set network config pub_ids
        for network in reporting_networks:
            pub_id = str(random.random()*100)

            setattr(network_config, network + '_pub_id', pub_id)

            AdNetworkAppMapper(ad_network_name=network,
                    publisher_id=pub_id,
                    ad_network_login=login_by_network[network],
                    application=app).put()
        network_config.put()

    today = datetime.datetime.now()
    day = datetime.timedelta(days=1)

    stats_manager = StatsModelQueryManager(account=account)

    # Generate StatsModel stats
    for app in apps:
        cur_date = APP_STATS_SINCE
        while cur_date<=today:
            for campaign in campaigns:
                stats= [generate_stats_model(adunit,
                                             creative,
                                             account,
                                             cur_date)
                        for creative in creatives_per_campaign[campaign]
                        for adunit in adunits_per_app[app]]

                req_stats = [generate_stats_model(adunit,None,account,cur_date)
                        for adunit in adunits_per_app[app]]
                for stat in req_stats:
                    stat.impression_count = stat.click_count = \
                            stat.conversion_count = 0

                stats_manager.put_stats(stats=stats+req_stats)

            cur_date+=day

    # Generate reporting stats
    cur_date = APP_STATS_SINCE.date()
    while cur_date<=datetime.date.today():
        network_totals = {}
        app_totals = {}
        for mapper in AdNetworkMapperManager.get_mappers(account):
            revenue = random.random() * 10000
            attempts = random.randint(1, 100000)
            impressions = random.randint(1, attempts)
            clicks = random.randint(1, impressions)
            stats = AdNetworkScrapeStats(revenue=revenue,
                                         attempts=attempts,
                                         impressions=impressions,
                                         clicks=clicks,
                                         date=cur_date,
                                         ad_network_app_mapper=mapper)
            stats.put()
            if mapper.ad_network_name not in network_totals:
                network_totals[mapper.ad_network_name] = \
                        AdNetworkNetworkStats(account=account,
                                              ad_network_name=mapper. \
                                                      ad_network_name,
                                              date=cur_date)
            AdNetworkStatsManager.combined_stats(network_totals[
                mapper.ad_network_name], stats)
            if mapper.application.key_ not in app_totals:
                app_totals[mapper.application.key_] = \
                        AdNetworkAppStats(account=account,
                                          application=mapper.application,
                                          date=cur_date)
            AdNetworkStatsManager.combined_stats(app_totals[mapper. \
                    application.key_], stats)

        for stats in network_totals.itervalues():
            stats.put()

        for stats in app_totals.itervalues():
            stats.put()

        cur_date+=day

if __name__=="__main__":
    main()

