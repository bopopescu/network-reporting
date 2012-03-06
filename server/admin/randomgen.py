import copy
import string
import random
import datetime
import uuid

from account.query_managers import AccountQueryManager
from reporting.query_managers import StatsModelQueryManager


from registration.models import *
from advertiser.models import *
from publisher.models import *
from account.models import *
from budget.models import *
from reporting.models import *


ceiling = lambda x, y: x if x < y else y

####
#Configuration Parameters for data generation
####

USERNAME = "test@mopub.com"
PASSWORD = "test"

NUM_ACCOUNTS = 1
NUM_APPS = 2
NUM_CAMPAIGNS_PER_APP = 3
NUM_CREATIVES_PER_ADGROUP = 1
NUM_ADUNITS_PER_APP = 5

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
CAMPAIGN_TYPES = ['gtee',
                  'gtee_high',
                  'gtee_low',
                  'promo',
                  'network',
                  'backfill_promo',
                  'marketplace',
                  'backfill_marketplace']
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
    adgroup_index = str(uuid.uuid1()).split('-')[0]
    return "AdGroup %s" % adgroup_index


def get_creative_name():
    creative_index = str(uuid.uuid1()).split('-')[0]
    return "Creative %s" % creative_index

def get_app_name():
    app_index = str(uuid.uuid1()).split('-')[0]
    return "Your Great App %s" % app_index

def get_adunit_name():
    adunit_index = str(uuid.uuid1()).split('-')[0]
    return "Your Well Performing AdUnit %s" % adunit_index

def get_campaign_name():
    campaign_index = str(uuid.uuid1()).split('-')[0]
    return "Super Campaign %s" % campaign_index

def get_random_color():
    return "".join([select_rand(COLOR_ALPH) for i in xrange(5)])

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

def get_random_datetime_pair():
    start, end = get_random_datetime(), get_random_datetime()
    if start > end:
        start, end = end, start

    return start, end


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
    start_date, end_date = get_random_datetime_pair()
    budget = Budget(start_datetime=start_date,
                    end_datetime = end_date,
                    static_total_budget = float(random.randint(100,1000)),
                    static_slice_budget = float(random.randint(100,1000)))

    budget.put()
    return budget


def generate_adgroup(campaign, site_keys, account, adgroup_type):
    if adgroup_type=="network":
        rand_network_type = select_rand(NETWORK_TYPES)
    else:
        rand_network_type = None

    start, end = get_random_datetime_pair()

    adgroup = AdGroup(campaign=campaign,
                      adgroup_type = adgroup_type,
                      network_type=rand_network_type,
                      bid_strategy=select_rand(BID_STRATEGIES),
                      account=account,
                      site_keys=site_keys,
                      name=get_adgroup_name(),
                      start_datetime=start,
                      end_datetime=end)
    adgroup.put()


    # If we've added a network adgroup, then we need to make sure to
    # update the account's NetworkConfig object as well, so that ad
    # network configuration is set properly.
    if rand_network_type in NETWORK_TYPE_TO_PUB_ID_ATTR.keys() \
       and adgroup.adgroup_type=="network":
        network_config = account.network_config
        setattr(network_config,
                NETWORK_TYPE_TO_PUB_ID_ATTR[rand_network_type],
                "fillerid")
        a = AccountQueryManager()
        a.update_config_and_put(account,network_config)

    return adgroup



def generate_campaign(account, budget):
    campaign = Campaign(name=get_campaign_name(),
                        account = account,
                        advertiser = "John's Hat Co, Inc.")
    campaign.put()
    return campaign

def generate_marketplace_campaign(account, budget):
    campaign = Campaign(name=get_campaign_name(),
                        account = account,
                        advertiser = "marketplace")
    campaign.put()
    return campaign



def generate_account(username=USERNAME,
                     password=PASSWORD,
                     email=USERNAME,
                     marketplace_config=None,
                     network_config=None):
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
    # This logic is in place to make the stats more realistic
    request_count = random.randint(0,10000)
    impression_count = int(random.random()*request_count)
    click_count = int(random.random() *.1* impression_count)
    conversion_count = int(random.random() *.1* click_count)
    revenue = click_count*.5

    user_count = int(request_count*.75)
    request_user_count = user_count
    impression_user_count =int(request_user_count*random.random())
    click_user_count = int(impression_user_count *random.random())

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
def main():
    account = generate_account()

    apps = [generate_app(account) for app in xrange(NUM_APPS)]

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,[]) for app in apps])
    creatives_per_campaign = {}

    for app in apps:
        for i in xrange(NUM_ADUNITS_PER_APP):
            adunits_per_app[app].append(generate_adunit(app,account))

        all_site_keys = [a.key() for a in AdUnit.all() if a._account == account.key()]

        for i in xrange(NUM_CAMPAIGNS_PER_APP):
            budget = generate_budget()
            adgroup_type = 'gtee_high'

            if i == 1:
                adgroup_type = 'network'
            elif i == 2:
                adgroup_type = 'marketplace'
            elif i == 3:
                adgroup_type = 'promo'

            if adgroup_type == 'marketplace':
                campaign = generate_marketplace_campaign(account, budget)
            else:
                campaign = generate_campaign(account, budget)

            creatives_per_campaign[campaign] = []
            campaigns_per_app[app].append(campaign)
            adgroup = generate_adgroup(campaign,
                                       select_rand_subset(all_site_keys),
                                       account,
                                       adgroup_type)
            for i in xrange(NUM_CREATIVES_PER_ADGROUP):
                creatives_per_campaign[campaign].append(generate_creative(account,adgroup))


    cur_date = APP_STATS_SINCE
    today = datetime.datetime.now()
    day = datetime.timedelta(days=1)

    s = StatsModelQueryManager(account=account)

    for app in apps:
        cur_date = APP_STATS_SINCE
        while cur_date <= today:
            for campaign in campaigns_per_app[app]:
                stats= [generate_stats_model(adunit,
                                             creative,
                                             account,
                                             cur_date)
                        for creative in creatives_per_campaign[campaign]
                        for adunit in adunits_per_app[app]]

                req_stats = [generate_stats_model(adunit, None, account, cur_date) \
                             for adunit in adunits_per_app[app]]
                for stat in req_stats:
                    stat.impression_count = 0
                    stat.click_count = 0
                    stat.conversion_count = 0

                s.put_stats(stats=stats+req_stats)

            cur_date+=day


if __name__=="__main__":
    main()
