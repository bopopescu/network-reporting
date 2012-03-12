import os
import pickle
import sys
import traceback

# add mopub root to path
sys.path.append(os.getcwd()+'/../')


# for ubuntu EC2
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/mopub/server/reporting')
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
from google.appengine.ext.db import BadKeyError
from google.appengine.ext.remote_api import remote_api_stub

from advertiser.models import Creative, AdGroup, Campaign
from publisher.models import Site as AdUnit, App


LIMIT = 100


# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:

#  {adunit_str: [app_str, account_str]}
ADUNIT_DEREF_CACHE = {}
#  {creative_str: [adgroup_str, campaign_str, account_str]}
CREATIVE_DEREF_CACHE = {}
# {adgroup_str: [campaign_str, account_str]}
ADGROUP_DEREF_CACHE = {}


def deref_adgroup(adgroup_str):
    if adgroup_str in ADGROUP_DEREF_CACHE:
        return ADGROUP_DEREF_CACHE[adgroup_str]
    try:
        adgroup_key = db.Key(adgroup_str)
        adgroup = AdGroup.get(adgroup_key)
        campaign_str = str(adgroup._campaign)
        account_str = str(adgroup._account)
        ADGROUP_DEREF_CACHE[adgroup_str] = [campaign_str, account_str]
        return [campaign_str, account_str]
    except BadKeyError, e:
        print 'EXCEPTION on adgroup %s: %s' %(adgroup_str, e)
        return None
    except Exception, e:
        print 'EXCEPTION on adgroup %s: %s' %(adgroup_str, e)
        return None


def process_creatives(creatives):
    for creative in creatives:
        try:
            creative_str = str(creative.key())
            if creative_str in CREATIVE_DEREF_CACHE:
                continue
            adgroup_str = str(creative._ad_group)
            adgroup_deref_results = deref_adgroup(adgroup_str)
            if adgroup_deref_results:
                [campaign_str, account_str] = adgroup_deref_results
                CREATIVE_DEREF_CACHE[creative_str] = [adgroup_str, campaign_str, account_str]
        except BadKeyError, e:
            print 'EXCEPTION on creative %s: %s' %(creative_str, e)
        except Exception, e:
            print 'EXCEPTION on creative %s: %s' %(creative_str, e)


def process_adunits(adunits):
    for adunit in adunits:
        try:
            adunit_str = str(adunit.key())
            if adunit_str in ADUNIT_DEREF_CACHE:
                continue
            app_str = str(adunit._app_key)
            account_str = str(adunit._account)
            ADUNIT_DEREF_CACHE[adunit_str] = [app_str, account_str]
        except BadKeyError, e:
            print '\tEXCEPTION on adunit %s: %s' %(adunit_str, e)
        except Exception, e:
            print '\tEXCEPTION on adunit %s: %s' %(adunit_str, e)


def pickle_to_file(pkl_obj, pkl_file):
    print '\npickling to %s ...' % (pkl_file)
    with open(pkl_file, 'w') as pf:
        pickle.dump(pkl_obj, pf)
    print '%i entries pickled' % (len(pkl_obj))


def auth_func():
    return "olp@mopub.com", "N47935N47935"


def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub

    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)


def main():
    # setup remote connection to datastore
    setup_remote_api()

    # process all adunits
    print 'processing adunits...'
    try:
        total = 0
        adunits = AdUnit.all().fetch(LIMIT)
        while len(adunits) == LIMIT:
            process_adunits(adunits)
            total += LIMIT
            print 'fetched %i adunits so far' % (total)
            last_key = adunits[-1].key()
            adunits = AdUnit.all().filter('__key__ >', last_key).fetch(LIMIT)

        # process last batch < LIMIT
        process_adunits(adunits)
        total += len(adunits)
        print 'fetched %i adunits total' % (total)
    except:
        traceback.print_exc()

    # pickle adunit hierarchy
    pickle_to_file(ADUNIT_DEREF_CACHE, 'adunit_hierarchy.pkl')


    # process all creatives
    print '\nprocessing creatives...'
    try:
        total = 0
        creatives = Creative.all().fetch(LIMIT)
        while len(creatives) == LIMIT:
            process_creatives(creatives)
            total += LIMIT
            print 'fetched %i creatives so far' % (total)
            last_key = creatives[-1].key()
            creatives = Creative.all().filter('__key__ >', last_key).fetch(LIMIT)

        # process last batch < LIMIT
        process_creatives(creatives)
        total += len(creatives)
        print 'fetched %i creatives total' % (total)
    except:
        traceback.print_exc()

    # pickle creative hierarchy
    pickle_to_file(CREATIVE_DEREF_CACHE, 'creative_hierarchy.pkl')



if __name__ == '__main__':
    main()

