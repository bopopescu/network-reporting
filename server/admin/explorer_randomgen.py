import copy
import string
import random
import datetime
import uuid

from common.utils import date_magic
import simplejson
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
NUM_ADUNITS = 10
NUM_CAMPAIGNS = 10
NUM_CAMPAIGNS_PER_APP = 2
NUM_CREATIVES_PER_ADGROUP = 20
NUM_ADUNITS_PER_APP = 20
NUM_ADGROUPS_PER_CAMPAIGN = 2

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

def get_adgroup_name():
    adgroup_index = str(uuid.uuid1()).split('-')[0]
    return "Wow! Line item %s" % adgroup_index


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
    return "Super Order %s" % campaign_index

def get_random_color():
    return "".join([select_rand(COLOR_ALPH) for i in xrange(5)])

def select_rand(array):
    return array[random.randint(0,len(array)-1)]

def select_rand_subset(array):
    num_elements = random.randint(1,len(array)-1)
    cloned = copy.copy(array)
    random.shuffle(cloned)
    return cloned[:num_elements]

def get_random_datetime():
    today = datetime.datetime.now()
    year = 2012
    month = random.randint(1,today.month)
    day = random.randint(1,28 if today.month!= month else random.randint(1,month))
    return datetime.datetime(year,month,day)

def get_random_datetime_pair():
    """
    Generates a pair of datetimes, returned in order of time.
    Good for generating start and end dates, because start
    will always be before end.
    e.g.:
        start, end = get_random_datetime_pair()
    """
    start, end = get_random_datetime(), get_random_datetime()
    if start > end:
        start, end = end, start
    return start, end


####
#Generation methods
####

def generate_app(account, id=None):
    app = App(key =_get_key(App, id),
              name=get_app_name(),
              app_type=select_rand(APP_TYPES),
              account=account)
    app.put()
    return app


def generate_adunit(app, account, id=None):
    adunit = AdUnit(key = _get_key(AdUnit, id),
                    app_key = app,
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


def generate_adgroup(campaign,
                     site_keys,
                     account,
                     network_type=None,
                     bid_strategy=None,
                     id=None,
                     key=None):


    rand_network_type = select_rand(NETWORK_TYPES)

    start, end = get_random_datetime_pair()

    adgroup = AdGroup(key=_get_key(AdGroup, id),
                      campaign=campaign,
                      network_type=network_type,
                      bid_strategy=bid_strategy,
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
       and adgroup.campaign.campaign_type=="network":
        network_config = account.network_config
        setattr(network_config,
                NETWORK_TYPE_TO_PUB_ID_ATTR[rand_network_type],
                "fillerid")
        a = AccountQueryManager()
        a.update_config_and_put(account,network_config)

    return adgroup


def generate_campaign(account,
                      campaign_type = None,
                      id=None,
                      key=None):

    campaign = Campaign(key=_get_key(Campaign, id),
                        name=get_campaign_name(),
                        account = account,
                        campaign_type = campaign_type,
                        advertiser = "John's Hat Co, Inc.",
                        is_order=True)
    campaign.put()
    return campaign


def generate_marketplace_campaign(account, id=None):
    campaign = Campaign(key_name = 'id:%s' % id if id else None,
                        name=get_campaign_name(),
                        account = account,
                        advertiser = "marketplace",
                        is_order=False)
    campaign.put()
    return campaign


def generate_account(username=USERNAME,
                     password=PASSWORD,
                     email=USERNAME,
                     marketplace_config=None,
                     network_config=None,
                     id=None):

    if not marketplace_config:
        marketplace_config = MarketPlaceConfig()
        marketplace_config.put()
    if not network_config:
        network_config = NetworkConfig(account=account)
        network_config.put()

    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False,
                                      username=username,
                                      password=password,
                                      email=email)
    manager.create_profile(user)

    db.delete(Account.all().fetch(1000))

    account_key = _get_key(Account, id)
    account = Account(mpuser=user, all_mpusers = [user.key()], key=account_key)
    account.active = True
    account.marketplace_config = marketplace_config
    account.network_config = network_config

    account.put()
    return account

def _get_key(cls, id):
    return db.Key.from_path(cls.kind(), id + 1)

def _get_correct_key(key):
    if key:
        if isinstance(key, str):
            key = db.Key(key)
        key = db.Key.from_path(key.kind(), key.id_or_name()) # overwrite the _app property
    return key


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


def generate_creative(account, adgroup, id):
    creative_name = get_creative_name()

    #For now, test data generation will only create basic text creatives
    creative = HtmlCreative(key=_get_key(Creative, id),
                            active=True,
                            account = account,
                            ad_group = adgroup,
                            ad_type = "html",
                            headline = "%s %s" % (creative_name,"headline"),
                            line1 = "%s %s" % (creative_name,"line1"),
                            line2 = "%s %s" % (creative_name,"line2"),
                            name=creative_name)
    creative.put()
    return creative



#Example Method to generate data. See top configuration contants for customizing result
def main():

    # these were copied from the generate_fixtures function in
    # mopub-stats-service/stats_service/fixtures.py
    flatten = lambda l: [item for sublist in l for item in sublist]

    account_id = 1
    account = generate_account(username='test@mopub.com', password='test', id=account_id)

    apps = [generate_app(account, id=id) for id in xrange(NUM_APPS)]

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,[]) for app in apps])
    creatives_per_adgroup = {}

    for i, app in enumerate(apps):
        adunits = [generate_adunit(app, account, id) for id in xrange(NUM_ADUNITS_PER_APP/(i+1))]



    # for app in apps:
    #     for adunit_key in publisher_keys[str(app.external_key())]:
    #         adunits_per_app[app].append(generate_adunit(app, account, key=adunit_key))

    adunit_dict = dict([(a.key(), a) for a in AdUnit.all() if a._account == account.key()])
    all_adunit_keys = adunit_dict.keys()

    campaigns = []
    for i, campaign_type in enumerate(['gtee', 'gtee_high', 'gtee_low', 'promo', 'network', 'backfill_promo', 'marketplace']):
        campaigns += [generate_campaign(account, campaign_type, id) for id in xrange(NUM_CAMPAIGNS/(i+1))]

    adgroups = []
    for i, campaign in enumerate(campaigns):
        adgroups += [generate_adgroup(campaign,
                         [adunit_key for j, adunit_key in enumerate(all_adunit_keys) if j % (i+1) == 0],
                         account,
                         network_type=NETWORK_TYPES[i % len(NETWORK_TYPES)] if campaign.campaign_type == 'network' else None,
                         id=i)]

    for i, adgroup in enumerate(adgroups):
        [generate_creative(account, adgroup, (i*100 + id)) for id in xrange(NUM_CREATIVES_PER_ADGROUP/(i+1))]

    start = datetime .datetime.now() - datetime.timedelta(100)
    days = date_magic.gen_days(start, datetime.datetime.now())
    datapoints = []
    for day in days:
        for i, adgroup in enumerate(adgroups):
            for j, adunit_key in enumerate(adgroup.site_keys):
                i += 1
                j += 1
                adunit = adunit_dict.get(adunit_key)
                datapoints += [dict(
                    date         = day.strftime("%Y-%m-%d-00"),
                    datehour     = day.strftime("%Y-%m-%d-%H"),
                    account      = str(adunit.account.key()),
                    campaign     = str(adgroup.campaign.key()),
                    adgroup      = str(adgroup.key()),
                    app          = str(adunit.app.key()),
                    adunit       = str(adunit.key()),
                    source       = _get_source(adgroup),
                    source_type  = _get_source_type(adgroup),

                    rev          = get_stats(day)*10.0*random.random(),
                    req          = int(get_stats(day)*1000*random.random()),
                    imp          = int(get_stats(day)*900*random.random()),
                    clk          = int(get_stats(day)*40*random.random()),
                    conv         = int(get_stats(day)*random.random()),
                    attempts     = int(get_stats(day)*1000*random.random()),

                    mpx_rev      = 0,
                    mpx_req      = 0,
                    mpx_imp      = 0,
                    mpx_clk      = 0,
                    mpx_conv     = 0,
                    mpx_attempts = 0,

                    net_rev      = 0,
                    net_req      = 0,
                    net_imp      = 0,
                    net_clk      = 0,
                    net_conv     = 0,
                    net_attempts = 0,
                )]


    open('datapoints.json','w').write(simplejson.dumps(datapoints))

    # for campaign_key in advertiser_keys.keys():
    #     budget = generate_budget()

    #     campaign = generate_campaign(account,
    #                                  budget,
    #                                  adgroup_type = adgroup_types[campaign_key],
    #                                  key=campaign_key)


    #     campaigns_per_app[app].append(campaign)

    #     for i, adgroup_key in enumerate(advertiser_keys[campaign_key]):
    #         adgroup = generate_adgroup(campaign,
    #                                    select_rand_subset(all_site_keys),
    #                                    account,
    #                                    key=adgroup_key)
    #         creatives_per_adgroup[str(adgroup)] = []
    #         for i in xrange(NUM_CREATIVES_PER_ADGROUP):
    #             creatives_per_adgroup[str(adgroup)].append()

def _get_source(adgroup):
    campaign_type = adgroup.campaign_type
    if 'gtee' in campaign_type or 'promo' in campaign_type:
        return 'direct'
    if 'network' in campaign_type:
        return 'network'
    if 'marketplace' in campaign_type:
        return 'mpx'

def _get_source_type(adgroup):
    source = _get_source(adgroup)
    if source == 'network':
        return adgroup.network_type.replace('_native', '').lower()
    if source == 'mpx':
        return 'mpx'
    if source == 'direct':
        campaign_type = adgroup.campaign_type
        if 'gtee' in campaign_type:
            return 'gtee'
        if 'backfill_promo' in campaign_type:
            return 'bfill'
        if 'promo' in campaign_type:
            return 'promo'

import math
def get_stats(day):
    return int(day.day + math.sin(day.day)/3*day.day)

if __name__=="__main__":
    main()
