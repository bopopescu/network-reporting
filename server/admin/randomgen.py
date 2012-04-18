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
NUM_CAMPAIGNS_PER_APP = 2
NUM_CREATIVES_PER_ADGROUP = 2
NUM_ADUNITS_PER_APP = 3
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

def generate_app(account, id=None, key=None):
    app = App(key = _get_correct_key(key),
              name=get_app_name(),
              app_type=select_rand(APP_TYPES),
              account = account)
    app.put()
    return app


def generate_adunit(app,account, id=None, key=None):
    adunit = AdUnit(key = _get_correct_key(key),
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
                     #adgroup_type,
                     id=None,
                     key=None):
    

    rand_network_type = select_rand(NETWORK_TYPES)

    start, end = get_random_datetime_pair()

    adgroup = AdGroup(key = _get_correct_key(key),
                      campaign=campaign,
                      #adgroup_type = adgroup_type,
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
       and adgroup.campaign.campaign_type=="network":
        network_config = account.network_config
        setattr(network_config,
                NETWORK_TYPE_TO_PUB_ID_ATTR[rand_network_type],
                "fillerid")
        a = AccountQueryManager()
        a.update_config_and_put(account,network_config)

    return adgroup


def generate_campaign(account,
                      budget,
                      adgroup_type = None,
                      id=None,
                      key=None):
    
    campaign = Campaign(key = _get_correct_key(key),
                        name=get_campaign_name(),
                        account = account,
                        campaign_type = adgroup_type,
                        advertiser = "John's Hat Co, Inc.",
                        is_order=True)
    campaign.put()
    return campaign


def generate_marketplace_campaign(account, budget, id=None):
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
                     key=None):
    if not marketplace_config:
        marketplace_config = MarketPlaceConfig()
        marketplace_config.put()
    if not network_config:
        network_config = NetworkConfig()
        network_config.put()

    manager = RegistrationManager()
    user = manager.create_active_user(send_email=False,
                                      username=username,
                                      password=password,
                                      email=email)
    manager.create_profile(user)

    # account = AccountQueryManager().get_current_account(user=user)
    account_key = _get_correct_key(key)
    account = Account(mpuser=user, all_mpusers = [user.key()], key=account_key)
    account.active = True
    account.marketplace_config = marketplace_config
    account.network_config = network_config

    account.put()
    return account

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


def generate_creative(account,adgroup):
    creative_name = get_creative_name()

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


#Example Method to generate data. See top configuration contants for customizing result
def main():

    # these were copied from the generate_fixtures function in
    # mopub-stats-service/stats_service/fixtures.py
    flatten = lambda l: [item for sublist in l for item in sublist]

    account_key = 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'
    
    advertiser_keys = {'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOqInRIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY64idEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMHQwRIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYxNa_Egw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPqsqxIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYwtCnEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOjarhIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY64SuEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKufgQYM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrJ-BBgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGO7hqRIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0eOrEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPeivhIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYhfe8Egw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKu6yBMM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY-b3MEww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM2jrhEM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYzqOuEQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOydzw8M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYz8XPDww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPXZ_hAM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9tn-EAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI-RuwgM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYkJG7CAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP6ovRAM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_6i9EAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOqYsxEM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYscyvEQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIucgQoM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYqqiACgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL631hMM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0qzXEww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPGErhIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8dquEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPid5QQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYybflBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLm2kxIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYnNiNEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP7LtREM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_8u1EQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP-iyg0M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYueTODQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOrqphIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY6-qmEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKvmzBIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY1erIEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKHA_w8M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYzdqDEAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL-4uRMM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYwLi5Eww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL7EkRIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYq-iSEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPTS0gcM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY5uTLBww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL-t5hEM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrZvrEQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIC25AcM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYupTnBww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJ-Y1AQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY6PjgBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGND3txEM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0fe3EQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLqvshIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY7OCsEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLjD9Q4M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY7q_6Dgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM340BMM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_LDTEww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOGLsxAM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY4ouzEAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI_yqQYM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3-CoBgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOWJ_AUM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYhd2BBgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLHs_QoM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYsuz9Cgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGNjYrQQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYttaqBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPyb9wcM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8aruBww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIjszg0M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYiPDIDQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIPO7BEM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYspzpEQw'], 'agltb3B1Yi1pbmNyOQsSCENhbXBhaWduIitta3Q6YWdsdGIzQjFZaTFwYm1OeUVBc1NCMEZqWTI5MWJuUVk4ZDc3QXd3DA': ['agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMGVtQkJBdww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMXQydEVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMkw2T0Vndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZM3JfLUNRdww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNDV5ekVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNHFhNkV3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNTRxUEV3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNlpfVEJ3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZOUlpRUJBdww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZXzdfYkV3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaF9LVUVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaHA2bEVRdww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaXBhQUR3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZazdMR0Vndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZa05qVEV3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZa3VheUVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZbUllMUVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZb0kzQUVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZcXViTUVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZc2FidERndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdHBybEJ3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdjRuOUF3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdjZmUkV3dww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZd3FiQ0Vndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZeUpuakVndww', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZenNIR0Vndww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM7z4wQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8ejbBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKqblwYM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYq5uXBgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIj15QQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYifXlBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGK-RohIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYooWmEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJKxpxIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_cSjEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOOAng8M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrqieDww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJrH5wQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYm8fnBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLDi9AYM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3u7zBgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI28sxIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYk4OsEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMyR9xAM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYl9L-EAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIyFrwQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY2cCsBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOP1vxIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8cDBEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOf34AkM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_NzdCQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKfxtgQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYlca3BAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJLMnhIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYqcGfEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPODtwgM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYuo-2CAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP3hiw8M': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9rmJDww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLDb2QcM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY96HcBww'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMCJ_QMM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9peCBAw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGN26xgUM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3rrGBQw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOPSoRIM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYmMCiEgw'], 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMKU5gQM': ['agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw']}
    
    publisher_keys = {
    'agltb3B1Yi1pbmNyDAsSA0FwcBixtswTDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYv6fREww'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBi7yLwSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYoI3AEgw'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBjtre0ODA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYsabtDgw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUYipaADww'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBipgMcSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYk7LGEgw'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBiuvboTDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUY4qa6Eww'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBjp8rMSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYkuayEgw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUYmIe1Egw'], 
    'agltb3B1Yi1pbmNyDAsSA0FwcBj1l4IEDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYv4n9Aww', 'agltb3B1Yi1pbmNyDQsSBFNpdGUY0emBBAw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUY54qPEww'], 'agltb3B1Yi1pbmNyDAsSA0FwcBjrh5MSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUY2L6OEgw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUYh_KUEgw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBiLo_8DDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUY6Z_TBww', 'agltb3B1Yi1pbmNyDQsSBFNpdGUYtprlBww', 'agltb3B1Yi1pbmNyDQsSBFNpdGUYhp6lEQw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBi-_tsTDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYkNjTEww', 'agltb3B1Yi1pbmNyDQsSBFNpdGUY_7_bEww'], 'agltb3B1Yi1pbmNyDAsSA0FwcBjxl-ESDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYyJnjEgw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBixiYYKDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUY3r_-CQw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBjlj8cSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYqubMEgw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBjFuMkSDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYzsHGEgw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBiblcASDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUYwqbCEgw'], 'agltb3B1Yi1pbmNyDAsSA0FwcBjqq64SDA': ['agltb3B1Yi1pbmNyDQsSBFNpdGUY1t2tEgw', 'agltb3B1Yi1pbmNyDQsSBFNpdGUY45yzEgw']}
    
    adgroup_types = {'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOqInRIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMHQwRIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPqsqxIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOjarhIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKufgQYM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGO7hqRIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPeivhIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKu6yBMM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM2jrhEM': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOydzw8M': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPXZ_hAM': u'marketplace', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI-RuwgM': u'backfill_promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP6ovRAM': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOqYsxEM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIucgQoM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL631hMM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPGErhIM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPid5QQM': u'backfill_promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLm2kxIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP7LtREM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP-iyg0M': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOrqphIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKvmzBIM': u'promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKHA_w8M': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL-4uRMM': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL7EkRIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPTS0gcM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGL-t5hEM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIC25AcM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJ-Y1AQM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGND3txEM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLqvshIM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLjD9Q4M': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM340BMM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOGLsxAM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI_yqQYM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOWJ_AUM': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLHs_QoM': u'marketplace', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGNjYrQQM': u'promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPyb9wcM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIjszg0M': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIPO7BEM': u'gtee_high', 'agltb3B1Yi1pbmNyOQsSCENhbXBhaWduIitta3Q6YWdsdGIzQjFZaTFwYm1OeUVBc1NCMEZqWTI5MWJuUVk4ZDc3QXd3DA': u'marketplace', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGM7z4wQM': u'promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKqblwYM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIj15QQM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGK-RohIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJKxpxIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOOAng8M': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJrH5wQM': u'backfill_promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLDi9AYM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGI28sxIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMyR9xAM': u'marketplace', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGIyFrwQM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOP1vxIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOf34AkM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGKfxtgQM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGJLMnhIM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPODtwgM': u'gtee', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGP3hiw8M': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGLDb2QcM': u'promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMCJ_QMM': u'promo', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGN26xgUM': u'network', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGOPSoRIM': u'gtee_high', 'agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGMKU5gQM': u'network'}
    network_types = {'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZeUpuakVndww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZazdMR0Vndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_8u1EQw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYqqiACgw': u'admob_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYspzpEQw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYsuz9Cgw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNTRxUEV3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY5uTLBww': u'custom_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYkJG7CAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYzdqDEAw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZb0kzQUVndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYueTODQw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8ejbBAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrZvrEQw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYwtCnEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY6-qmEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8aruBww': u'custom_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_NzdCQw': u'chartboost', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZd3FiQ0Vndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY7q_6Dgw': u'iAd', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0qzXEww': u'admob_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYnNiNEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrqieDww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYq5uXBgw': u'inmobi', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8cDBEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3rrGBQw': u'jumptap', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYxNa_Egw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYrJ-BBgw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdjRuOUF3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYifXlBAw': u'custom_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9peCBAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_LDTEww': u'iAd', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZM3JfLUNRdww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZcXViTUVndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYlca3BAw': u'admob', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNHFhNkV3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY2cCsBAw': u'ejam', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY64SuEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY7OCsEgw': u'millennial_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY96HcBww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY4ouzEAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYhd2BBgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY8dquEgw': u'iAd', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaF9LVUVndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYqcGfEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYhfe8Egw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYl9L-EAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0eOrEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYscyvEQw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZbUllMUVndww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdHBybEJ3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYuo-2CAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYooWmEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9rmJDww': u'admob_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_6i9EAw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaXBhQUR3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY_cSjEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3u7zBgw': u'millennial', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZdjZmUkV3dww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZa3VheUVndww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMXQydEVndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYm8fnBAw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMkw2T0Vndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYybflBAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY6PjgBAw': u'admob_native', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY1erIEgw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNDV5ekVndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY0fe3EQw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYttaqBAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYq-iSEgw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZMGVtQkJBdww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYz8XPDww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY9tn-EAw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYzqOuEQw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZc2FidERndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY-b3MEww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY64idEgw': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYiPDIDQw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZa05qVEV3dww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw': u'iAd', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYwLi5Eww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYupTnBww': u'custom_native', 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZOUlpRUJBdww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZNlpfVEJ3dww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZaHA2bEVRdww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAY3-CoBgw': u'chartboost', 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYk4OsEgw': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZXzdfYkV3dww': None, 'agltb3B1Yi1pbmNyNAsSB0FkR3JvdXAiJ21rdDphZ2x0YjNCMVlpMXBibU55RFFzU0JGTnBkR1VZenNIR0Vndww': None, 'agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYmMCiEgw': None}
    
    account = generate_account(username='test@mopub.com', password='test', key=account_key)
        
    apps = [generate_app(account, key=app_key) for app_key in publisher_keys.keys()]

    adunits_per_app = dict([(app,[]) for app in apps])
    campaigns_per_app = dict([(app,[]) for app in apps])
    creatives_per_adgroup = {}

    for app in apps:
        for adunit_key in publisher_keys[str(app.external_key())]:
            adunits_per_app[app].append(generate_adunit(app, account, key=adunit_key))

        all_site_keys = [a.key() for a in AdUnit.all() if a._account == account.key()]

    for campaign_key in advertiser_keys.keys():
        budget = generate_budget()
        
        campaign = generate_campaign(account,
                                     budget,
                                     adgroup_type = adgroup_types[campaign_key],
                                     key=campaign_key)
                                     

        campaigns_per_app[app].append(campaign)
        
        for i, adgroup_key in enumerate(advertiser_keys[campaign_key]):
            adgroup = generate_adgroup(campaign,
                                       select_rand_subset(all_site_keys),
                                       account,
                                       key=adgroup_key)
            creatives_per_adgroup[str(adgroup)] = []
            for i in xrange(NUM_CREATIVES_PER_ADGROUP):
                creatives_per_adgroup[str(adgroup)].append(generate_creative(account, adgroup))

if __name__=="__main__":
    main()
