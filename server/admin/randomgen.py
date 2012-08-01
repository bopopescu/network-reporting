import copy
import string
import random
import datetime
import uuid

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


from advertiser.query_managers import CampaignQueryManager
from publisher.query_managers import AdUnitQueryManager

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
def select_rand(array):
    """
    Selects a random member of an array.
    """
    return array[random.randint(0,len(array)-1)]

def select_rand_subset(array):
    """
    Selects a random subset array from an array.
    """
    num_elements = random.randint(1,len(array)-1)
    cloned = copy.copy(array)
    random.shuffle(cloned)
    return cloned[:num_elements]

def get_random_name(kind=None):
    """
    Generates a random string for a name.
    """
    if not kind:
        kind = 'Object'
    iden = str(uuid.uuid4())[:4]
    return "%s%s" % (kind, iden)

def get_random_color():
    """
    Generates a random 6 digit hex color
    """
    color_alphas = string.digits + "ABCDEF"
    return "".join([select_rand(color_alphas) for i in range(5)])

def get_keys(objs, as_str=False):
    """
    Gets a list of keys for each object in a list of objects.
    """
    keys = [obj.key() for obj in objs]
    if as_str:
        return [str(k) for k in keys]
    return keys


def get_random_date():
    """
    Gets a random date between the start of the year and today.
    """
    today = datetime.date.today()
    year = today.year
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return datetime.date(year,month,day)

def get_random_datetime():
    """
    Gets a random datetime between the start of the year and today.
    """
    today = datetime.datetime.now()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return datetime.datetime(year,month,day)


####
#Generation methods
####


def generate_app(account):
    app = App(name=get_random_name(),
              app_type=select_rand(APP_TYPES),
              account = account)
    app.put()
    return app


def generate_adunit(app, account):
    adunit = AdUnit(app_key = app,
                    account = account,
                    name = get_random_name(),
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
                     account = account)
    order.put()
    return order


def generate_line_item(account, order, site_keys,
                       start_date=None, end_date=None,
                       budget=None):
    
    if not start_date:
        start_date = get_random_date()
        
    if not end_date:
        end_date = get_random_date()

    if start_date> end_date:
        temp = start_date
        start_date = end_date
        end_date = temp

    line_item = AdGroup(campaign=order,
                        adgroup_type='gtee',
                        name = get_random_name(),
                        site_keys = site_keys,
                        account = account)
    line_item.put()
    return line_item

    
def generate_marketplace(account):
    pass

    
def generate_network(account, network_type):
    pass

    
def generate_account(username, password):
    # Create a user and profile based on passed-in credentials.
    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False, username=username,
                                      password=password, email=username)
    manager.create_profile(user)

    # Create an account for this user. Mark it as active and as using new-style
    # networks.
    account = AccountQueryManager().get_current_account(user=user)
    account.active = True
    account.display_new_networks = True

    account.put()

    # Since this is a new account, it needs marketplace and network configs.
    marketplace_config = MarketPlaceConfig()
    marketplace_config.put()
    account.marketplace_config = marketplace_config

    network_config = NetworkConfig(account=account)
    network_config.put()
    account.network_config = network_config

    # This account also needs a default marketplace campaign.
    marketplace_campaign = CampaignQueryManager.get_marketplace(account)
    marketplace_campaign.put()

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
    click_count = int((random.random()/10.0)*impression_count)
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
    creative_name = get_random_name()

    #For now, test data generation will only create basic text creatives
    creative = HtmlCreative(active=True,
                            account = account,
                            ad_group = adgroup,
                            ad_type = "html",
                            headline = "%s %s" % (creative_name,"headline"),
                            line1 = "%s %s" % (creative_name,"line1"),
                            line2 = "%s %s" % (creative_name,"line2"),
                            name=creative_name)
    creative.put()
    return creative



        
def main():
    
    account = generate_account('test@mopub.com', 'test')
    account.put()

    # generate inventory
    apps = [generate_app(account) for i in range(5)]
    # generate two adunits per app and keep them grouped together for later
    adunits = [(generate_adunit(app, account),
                generate_adunit(app, account)) for app in apps]

    # generate advertiser models
    orders = [generate_order(account) for i in range(5)]
    line_items = [generate_line_item(account, order, get_keys(site_keys)) \
                  for order, site_keys in zip(orders, adunits)]
    creatives = [generate_creative(account, line_item) for line_item in line_items]
    
    # Generate the date range
    today = datetime.datetime.now()
    month_ago = today - datetime.timedelta(14)
    days = date_magic.gen_days(month_ago, today)
    
    # Generate stats for each creative + adunit pair
    stats_manager = StatsModelQueryManager(account=account)
    for creative in creatives:
        for day in days:
            for site_key in creative.ad_group.site_keys:                
                adunit = AdUnitQueryManager.get(site_key)                             
                stats = generate_stats_model(adunit, creative, account, day)
                stats_manager.put_stats(stats=stats)
        
if __name__=="__main__":
    main()

