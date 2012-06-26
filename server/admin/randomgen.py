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
from advertiser.query_managers import CampaignQueryManager

from ad_network_reports.models import AdNetworkLoginCredentials, \
     AdNetworkAppMapper, \
     AdNetworkStats, \
     AdNetworkScrapeStats, \
     AdNetworkNetworkStats, \
     AdNetworkAppStats, \
     LoginStates

from ad_network_reports.query_managers import AdNetworkMapperManager, \
        AdNetworkStatsManager

from common.utils import date_magic

####
#Configuration Parameters for data generation
####

USERNAME = "test@mopub.com"
PASSWORD = "test"

NUM_ACCOUNTS = 1 #ONLY SUPPORT ONE ACCOUNT FOR NOW
NUM_APPS = 2
NUM_CAMPAIGNS_PER_APP = 1
NUM_CREATIVES_PER_ADGROUP = 1
NUM_ADUNITS_PER_APP = 2

NETWORKS_TO_USE = ['admob', 'admob', 'millennial']
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

CAMPAIGN_TYPES = ['order', 'marketplace', 'network']

ADGROUP_TYPES = ['gtee',
                 'gtee_high',
                 'gtee_low',
                 'promo',
                 'network',
                 'backfill_promo',
                 'marketplace',]
                 
NETWORK_TYPES = ["adsense",
                 "iAd",
                 "admob",
                 "millennial",
                 "ejam",
                 "chartboost",
                 "appnexus",
                 "inmobi",
                 "mobfox",
                 "jumptap",
                 "brightroll",
                 "greystripe",
                 "custom",
                 "custom_native",
                 "admob_native",
                 "millennial_native"]
BID_STRATEGIES = ['cpc','cpm','cpa']

NETWORK_TYPE_TO_PUB_ID_ATTR = {'dummy':'',
                               'adsense':'adsense_pub_id',
                               'iAd':'',
                               'admob':'admob_pub_id',
                               'millennial':'millennial_pub_id',
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

def get_random_name():
    return 'Object ' + str(uuid.uuid4())

def get_random_color():
    return "".join([select_rand(COLOR_ALPH) for i in range(5)])

def get_keys(objs, as_str=False):
    keys = [obj.key() for obj in objs]
    if as_str:
        return [str(k) for k in keys]
    return keys



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


def generate_adunit(app, account):
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


def generate_order(account, budget=None):

    name = get_random_name()
    order = Campaign(name=name,
                        budget_obj = budget,
                        campaign_type = 'order',
                        account = account,
                        start_date = start_date,
                        end_date = end_date)
    campaign.put()
    return order


def generate_line_item(account, order, site_keys,
                       start_date=None, end_date=None, budget=None):
    
    if not start_date:
        start_date = get_random_date()
        
    if not end_date:
        end_date = get_random_date()

    if start_date> end_date:
        temp = start_date
        start_date = end_date
        end_date = temp

    line_item = AdGroup(campaign=order,
                        name = get_random_name(),
                        site_keys = site_keys,
                        account = account)
    line_item.put()
    return line_item
                        
    
def generate_adgroup(site_keys,account,campaign=None,network=None):
    if campaign:
        if campaign.campaign_type=="network":
            if network:
                adgroup = AdGroupQueryManager.get_network_adgroup(campaign,
                        site_keys[0], account.key())
                adgroup.put()
                return adgroup
            else:
                network = select_rand(NETWORK_TYPES)

            # Need to update account's network configuration if we add
            # a network adgroup
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



def generate_campaign(account, budget=None, campaign_type=None):

    if not campaign_type:
        campaign_type = 'order'
        
    if campaign_type == 'marketplace':
        campaign_name = 'Marketplace'
        campaign = CampaignQueryManager.get_marketplace(account)
        
    else:
        start_date = get_random_date()
        end_date = get_random_date()
        name = get_campaign_name()
        if start_date> end_date:
            temp = start_date
            start_date = end_date
            end_date = temp
        campaign = Campaign(name=campaign_name,
                            budget_obj = budget,
                            campaign_type = campaign_type,
                            account = account,
                            start_date = start_date,
                            end_date = end_date)
    campaign.put()
    return campaign



def generate_account(username=USERNAME,
                     password=PASSWORD,
                     email=USERNAME,                     
                     marketplace_config=None,
                     network_config=None,
                     display_new_networks=False):

    # Create a marketplace config if it doesnt exist
    if not marketplace_config:
        marketplace_config = MarketPlaceConfig()
        marketplace_config.put()

    # Create a network config if it doesnt exist
    if not network_config:
        network_config = NetworkConfig()
        network_config.put()

    # Register a new user
    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False,username=username,
                                      password=password,email=email)
    manager.create_profile(user)

    # Create a new account object for the user
    account = AccountQueryManager().get_current_account(user=user)
    account.active = True
    account.marketplace_config = marketplace_config
    account.network_config = network_config
    account.display_new_networks = display_new_networks
    account.put()
    
    return account

def generate_network_config():
    networkconfig = NetworkConfig()
    networkconfig.put()
    return networkconfig

def generate_marketplace_config():
    marketplace_config = MarketPlaceConfig()
    marketplace_config.put()
    return marketplace_config


def generate_stats_model(publisher, advertiser, account, date):
    #This logic is in place to make the stats more realistic
    request_count = random.randint(0,10000)
    impression_count = int(random.random()*request_count)
    click_count = int(random.random()*impression_count)
    conversion_count = int(random.random()*click_count)
    revenue = click_count*.002

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


def generate_creative(account, adgroup):
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



        
def main():
    account = generate_account(USERNAME,
                               PASSWORD,
                               USERNAME,
                               display_new_networks=True)

    # generate inventory
    apps = [generate_app(account) for i in range(5)]
    adunits = [(generate_adunit(app, account), generate_adunit(app, account)) for app in apps]

    # generate advertiser models
    orders = [generate_order(account) for i in range(5)]    
    line_items = [generate_line_item(account, order, get_keys(site_keys)) \
                  for order, site_keys in zip(orders, adunits)]
    creatives = [generate_creative(account, line_item) for line_item in line_items]

    # Generate the date range
    today = datetime.datetime.now()
    month_ago = today - datetime.timedelta(30)
    days = date_magic.gen_days(today, month_ago)

    # Generate stats for each creative + adunit pair
    stats_manager = StatsModelQueryManager(account=account)
    for creative in creatives:
        for day in days:
            for site_key in creative.ad_group.site_keys:
                adunit = AdUnitQueryManager.get(site_key)
                stats = generate_stats_model(adunit, creative, account, day)

                # Generate some stats for requests that didn't fill
                req_stats = generate_stats_model(adunit,None,account,cur_date)
                req_stats.impression_count = req_stats.click_count = req_stats.conversion_count = 0
                
                stats_manager.put_stats(stats=stats+req_stats)            
        
if __name__=="__main__":
    main()

