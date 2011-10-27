import sys
import traceback


# for ubuntu EC2
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')


from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.ext import db
from google.appengine.ext.remote_api import remote_api_stub

from account.models import Account
from advertiser.models import *
from advertiser.query_managers import CreativeQueryManager, AdGroupQueryManager, CampaignQueryManager
from publisher.models import *
# from publisher.query_managers import *
AdUnit = Site

LIMIT = 100
# APP_ID = 'mopub-inc'
APP_ID = 'mopub-experimental'
HOST = '38.%s.appspot.com' % APP_ID

def auth_func():
  return 'olp@mopub.com', 'N47935'

DEREF_CACHE = {}

ALL_ACCOUNTS = []
ALL_ADUNITS = []
ALL_ADGROUPS = []

CAMPAIGNS_TO_PUT = []
ADGROUPS_TO_PUT = []
CREATIVES_TO_PUT = []


def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


def fetch_all_accounts():
    print '\nretrieving accounts...'
    try:
        total = 0
        accounts = Account.all().fetch(LIMIT)
        ALL_ACCOUNTS.extend(accounts)

        while len(accounts) == LIMIT:
            total += LIMIT
            print 'fetched %i accounts so far' % (total)
            last_key = accounts[-1].key()
            accounts = Account.all().filter('__key__ >', last_key).fetch(LIMIT)
            ALL_ACCOUNTS.extend(accounts)

        print 'fetched %i accounts total' % (len(ALL_ACCOUNTS))
    except:
        traceback.print_exc()
        sys.exit()


def fetch_all_adunits():
    print '\nretrieving adunits...'
    try:
        total = 0
        adunits = AdUnit.all().fetch(LIMIT)
        ALL_ADUNITS.extend(adunits)

        while len(adunits) == LIMIT:
            total += LIMIT
            print 'fetched %i adunits so far' % (total)
            last_key = adunits[-1].key()
            adunits = AdUnit.all().filter('__key__ >', last_key).fetch(LIMIT)
            ALL_ADUNITS.extend(adunits)

        print 'fetched %i adunits total' % (len(ALL_ADUNITS))
    except:
        traceback.print_exc()
        sys.exit()


def fetch_all_adgroups():
    print '\nretrieving adgroups...'
    try:
        total = 0
        adgroups = AdGroup.all().fetch(LIMIT)
        ALL_ADGROUPS.extend(adgroups)

        while len(adgroups) == LIMIT:
            total += LIMIT
            print 'fetched %i adgroups so far' % (total)
            last_key = adgroups[-1].key()
            adgroups = AdGroup.all().filter('__key__ >', last_key).fetch(LIMIT)
            ALL_ADGROUPS.extend(adgroups)

        print 'fetched %i adgroups total' % (len(ALL_ADGROUPS))
    except:
        traceback.print_exc()
        sys.exit()


def migrate_campaigns():
    '''
    CAMPAIGN MIGRATION
    Every account should have one marketplace campaign defaulted to `active=False`
    For the accounts that already have one or more marketplace campaign:
        -- the old campaign(s) should be marked `deleted = True`
        -- the new campaign should be marked `active = True`
    '''

    print '\nmigrating campaigns...\n'

    processed_so_far = 0
    for account in ALL_ACCOUNTS:
        DEREF_CACHE[account.key()] = account

        # create new mpx campaign
        new_mpx_camapign = CampaignQueryManager.get_marketplace(account)
        new_mpx_camapign.active = False

        # archive old existing mpx campaigns, if any
        existing_mpx_campaigns = Campaign.all().filter('account =', account) \
                                               .filter('campaign_type IN', ['marketplace', 'backfill_marketplace'])
        for c in existing_mpx_campaigns:
            print 'found old mpx campaign', c
            DEREF_CACHE[c.key()] = c    # put old mpx campaign deref cache, used for migrating adgroups
            if not c.key().name():
                c.deleted = True
            CAMPAIGNS_TO_PUT.append(c)
            new_mpx_camapign.active = True

        CAMPAIGNS_TO_PUT.append(new_mpx_camapign)

        processed_so_far += 1
        if processed_so_far % LIMIT == 0:
            print 'processed %i accounts so far' % processed_so_far

    print 'to put %i campaigns\n' % len(CAMPAIGNS_TO_PUT)


def migrate_adgroups_and_creatives():
    '''
    ADGROUP MIGRATION
    Create a marketplace adgroup for every adunit
    with defaults `active=True` and `site_keys=[ adunit.key()]`
    '''

    print '\nmigrating adgroups and creatives...\n'

    new_mpx_adgroup_dict = {}

    processed_so_far = 0
    for adunit in ALL_ADUNITS:
        # create new mpx adgroup
        account = DEREF_CACHE[adunit._account]   # account model object on left, account key object on right
        adunit.account = account # set property, just in case
        new_mpx_adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit.key(), adunit._account)
        new_mpx_adgroup.active = True
        new_mpx_adgroup_dict[new_mpx_adgroup.key()] = new_mpx_adgroup

        # move price floor from account.network_config to adgroup's property `mktplace_price_floor`
        if account._network_config in DEREF_CACHE:
            new_mpx_adgroup.mktplace_price_floor = DEREF_CACHE[account._network_config].price_floor
        else:
            if account.network_config:  # network_config is not None
                DEREF_CACHE[account._network_config] = account.network_config
                new_mpx_adgroup.mktplace_price_floor = DEREF_CACHE[account._network_config].price_floor
            else:
                new_mpx_adgroup.mktplace_price_floor = .25

        # create default mpx creative
        default_mpx_creative = new_mpx_adgroup.default_creative(key_name=new_mpx_adgroup.key().name())
        default_mpx_creative.adgroup = new_mpx_adgroup
        default_mpx_creative.account = account
        CREATIVES_TO_PUT.append(default_mpx_creative)

        processed_so_far += 1
        if processed_so_far % LIMIT == 0:
            print 'processed %i adunits so far' % processed_so_far


    print 'to put %i creatives\n' % len(CREATIVES_TO_PUT)

    adunits_targeted_by_old_mpx_adgroups = set()

    # for each account, archive old existing mpx adgroups, if any
    processed_so_far = 0
    for account in ALL_ACCOUNTS:
        account_key = account.key()
        all_adunits_under_account = filter(lambda adunit: adunit._account == account_key, ALL_ADUNITS)
        all_adgroups_under_account = filter(lambda adgroup: adgroup._account == account_key, ALL_ADGROUPS)

        for ag in all_adgroups_under_account:
            if ag._campaign in DEREF_CACHE: # this adgroup is under an old mpx campaign
                print 'found old mpx adgroup', ag
                ADGROUPS_TO_PUT.append(ag)
                if not ag.key().name():
                    ag.deleted = True
                adunits_targeted_by_old_mpx_adgroups |= set(ag.site_keys)

        # for adunits not targeted by any old mpx adgroups, set their adgroups default to `active=False`
        adunits_not_targeted_by_old_mpx_adgroups = set(all_adunits_under_account) - adunits_targeted_by_old_mpx_adgroups
        for adunit in adunits_not_targeted_by_old_mpx_adgroups:
            new_mpx_adgroup = AdGroupQueryManager.get_marketplace_adgroup(adunit.key(), adunit._account)
            new_mpx_adgroup_dict[new_mpx_adgroup.key()].active = False

        processed_so_far += 1
        if processed_so_far % LIMIT == 0:
            print 'processed %i accounts so far' % processed_so_far

    ADGROUPS_TO_PUT.extend(new_mpx_adgroup_dict.values())
    print 'to put %i adgroups\n' % len(ADGROUPS_TO_PUT)



def main():
    # connect to GAE datastore
    remote_api_stub.ConfigureRemoteDatastore(APP_ID, '/remote_api', auth_func, HOST)

    # fetch models
    fetch_all_accounts()
    fetch_all_adunits()
    fetch_all_adgroups()

    # migrate models
    migrate_campaigns()
    migrate_adgroups_and_creatives()


    # batch put models
    total = 0
    for chunk in chunks(CAMPAIGNS_TO_PUT, LIMIT):
        CampaignQueryManager.put(chunk)
        total += len(chunk)
        print 'put in %i campaigns' % total

    total = 0
    for chunk in chunks(ADGROUPS_TO_PUT, LIMIT):
        AdGroupQueryManager.put(chunk)
        total += len(chunk)
        print 'put in %i adgroups' % total

    total = 0
    for chunk in chunks(CREATIVES_TO_PUT, LIMIT):
        CreativeQueryManager.put(chunk)
        total += len(chunk)
        print 'put in %i creatives' % total







if __name__ == '__main__':
    main()