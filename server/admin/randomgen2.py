#from appengine_django import InstallAppengineHelperForDjango
#InstallAppengineHelperForDjango()

import copy
import string
import random
import datetime as dt

from account.query_managers import AccountQueryManager
from reporting.query_managers import StatsModelQueryManager

from registration.models import *
from advertiser.models import *
from publisher.models import *
from account.models import *
from budget.models import *
from reporting.models import *


APP_INDEX = 0
ADUNIT_INDEX = 0
CAMPAIGN_INDEX = 0
ADGROUP_INDEX= 0
APP_TYPES = ['iphone','android','ipad','mweb']
COLOR_ALPH = string.digits + "ABCDEF"
CAMPAIGN_TYPES = ['gtee', 'gtee_high', 'gtee_low', 'promo', 'network','backfill_promo', 'marketplace', 'backfill_marketplace']
NETWORK_TYPES = ["dummy","adsense", "iAd", "admob","millennial","ejam","chartboost","appnexus","inmobi","mobfox","jumptap","brightroll","greystripe", "custom", "custom_native", "admob_native", "millennial_native"]
BID_STRATEGIES = ['cpc','cpm','cpa']


def get_adgroup_name():
    global ADGROUP_INDEX
    ADGROUP_INDEX+=1
    return "adgroup%s" % ADGROUP_INDEX

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
    today = dt.date.today()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return dt.date(year,month,day)

def get_random_datetime():
    today = dt.datetime.now()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return dt.datetime(year,month,day)


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
                  

def generate_adgroup(campaign,site_keys,account):
    adgroup = AdGroup(campaign=campaign,network_type=select_rand(NETWORK_TYPES),bid_strategy=select_rand(BID_STRATEGIES),
                      account=account,site_keys=site_keys,name=get_adgroup_name())
    adgroup.put()
    return adgroup
    

'''creates a budget, campaign, and adgroup'''
def generate_campaign(account,budget):
    start_date = get_random_date()
    end_date = get_random_date()
    if start_date> end_date:
        temp = start_date
        start_date = end_date
        end_date = temp    
    campaign = Campaign(name=get_campaign_name(),
                        budget_obj = budget,
                        campaign_type = select_rand(CAMPAIGN_TYPES),
                        account = account,
                        start_date = start_date,
                        end_date = end_date)
    campaign.put()
    return campaign

'''generates user and account'''
def generate_account(username="rob@mopub.com",password="test",email="rob@mopub.com",marketplace_config=None,networkconfig=None):
    if not marketplace_config:
        marketplace_config = MarketPlaceConfig()
        marketplace_config.put()
    if not networkconfig:
        networkconfig = NetworkConfig()
        networkconfig.put()

    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False,username=username,password=password,email=email)
    manager.create_profile(user)
    
    account = AccountQueryManager().get_current_account(user=user)
    account.marketplace_config = marketplace_config
    account.networkconfig = networkconfig

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
    request_count = random.randint(0,10000)
    impression_count = int(random.random()*request_count)
    click_count = int(random.random()*impression_count)
    conversion_count = int(random.random()*click_count)

    user_count = int(request_count*.75)
    request_user_count = user_count
    impression_user_count =int(request_user_count*random.random())
    click_user_count = int(impression_user_count *random.random())

    stats_model = StatsModel(publisher = publisher,
                             advertiser = advertiser,
                             account = account,
                             date = date,
                             request_count  =request_count,
                             impression_count = impression_count,
                             click_count = click_count,
                             conversion_count = conversion_count,
                             user_count = user_count,
                             request_user_count = request_user_count,
                             impression_user_count = impression_user_count,
                             click_user_count = click_user_count)
                             
    return stats_model
    

def main():
    NUM_ACCOUNTS = 1
    NUM_APPS = 2 #ONLY SUPPORT ONE ACCOUNT FOR NOW
    NUM_CAMPAIGNS_PER_APP = 2
    NUM_ADUNITS_PER_APP = 2

    APP_STATS_SINCE = datetime.datetime(2012,1,10)
    

    account = generate_account("rob@mopub.com","test","rob@mopub.com")

    apps = []
    for i in range(NUM_APPS):
        apps.append(generate_app(account))

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,[]) for app in apps])
    for app in apps:
        for i in range(NUM_ADUNITS_PER_APP):
            adunits_per_app[app].append(generate_adunit(app,account))

        all_site_keys = [a.key() for a in AdUnit.all()]

        for i in range(NUM_CAMPAIGNS_PER_APP):
            budget = generate_budget()
            campaign = generate_campaign(account,budget)
            campaigns_per_app[app].append(campaign)
            adgroup = generate_adgroup(campaign,
                                       select_rand_subset(all_site_keys),
                                       account)
                                          

    cur_date = APP_STATS_SINCE
    today = dt.datetime.now()
    day = dt.timedelta(days=1)

    s = StatsModelQueryManager(account=account)

    for app in apps:
        cur_date = APP_STATS_SINCE
        while cur_date<today:
            stats= [generate_stats_model(app,
                                  campaign,
                                  account,
                                  cur_date)                    
             for campaign in campaigns_per_app[app]]
            s.put_stats(stats=stats)
            
            cur_date+=day
        
            
if __name__=="__main__":
    main()
