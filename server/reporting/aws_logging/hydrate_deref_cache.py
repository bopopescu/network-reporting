import cgi
import os 
import pickle
import re
import sys
import time
import traceback
import urlparse

from optparse import OptionParser


# add mopub root to path
sys.path.append(os.getcwd()+'/../../')


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

import utils
from advertiser.models import Creative, AdGroup, Campaign
from publisher.models import Site as AdUnit, App


LIMIT = 100


# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:
# {app_str: [account_str],
#  adunit_str: [app_str, account_str],
#  campaign_str: [account_str],
#  adgroup_str: [campaign_str, account_str],
#  creative_str: [adgroup_str, campaign_str, account_str]} 

DEREF_CACHE_PICKLE_FILE = 'deref_cache.pkl' 
try:
    print '\nloading deref cache from %s ...' %DEREF_CACHE_PICKLE_FILE
    with open(DEREF_CACHE_PICKLE_FILE, 'rb') as pickle_file:
        DEREF_CACHE = pickle.load(pickle_file)
    print 'loaded %i records\n' % (len(DEREF_CACHE))
except:
    traceback.print_exc()
    print '\ninitializing empty deref cache...\n'
    DEREF_CACHE = {}


def auth_func():
    return "olp@mopub.com", "N47935N47935"
  

def deref_adgroup(adgroup_str):
    if adgroup_str in DEREF_CACHE:
        return DEREF_CACHE[adgroup_str]
    try:
        adgroup_key = db.Key(adgroup_str)
        adgroup = AdGroup.get(adgroup_key)
        campaign_str = str(adgroup._campaign)
        account_str = str(adgroup._account)
        DEREF_CACHE[adgroup_str] = [campaign_str, account_str]
        DEREF_CACHE[campaign_str] = [account_str]
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
            if creative_str in DEREF_CACHE:
                continue
            adgroup_str = str(creative._ad_group)
            adgroup_deref_results = deref_adgroup(adgroup_str)
            if adgroup_deref_results:
                [campaign_str, account_str] = adgroup_deref_results
                DEREF_CACHE[creative_str] = [adgroup_str, campaign_str, account_str]
        except BadKeyError, e:
            print 'EXCEPTION on creative %s: %s' %(creative_str, e)
        except Exception, e:
            print 'EXCEPTION on creative %s: %s' %(creative_str, e)


def process_adunits(adunits):
    for adunit in adunits:
        try:
            adunit_str = str(adunit.key())
            if adunit_str in DEREF_CACHE: 
                continue
            app_str = str(adunit._app_key)
            account_str = str(adunit._account)
            DEREF_CACHE[adunit_str] = [app_str, account_str]
            DEREF_CACHE[app_str] = [account_str]
        except BadKeyError, e:
            print '\tEXCEPTION on adunit %s: %s' %(adunit_str, e)
        except Exception, e:
            print '\tEXCEPTION on adunit %s: %s' %(adunit_str, e)        


def pickle_deref_cache():
    print '\npickling to %s ...' % (DEREF_CACHE_PICKLE_FILE)
    with open(DEREF_CACHE_PICKLE_FILE, 'wb') as pickle_file:
        pickle.dump(DEREF_CACHE, pickle_file)
    print '%i entries loaded' % (len(DEREF_CACHE))


                                
def main():
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

    start = time.time()

    print 'processing adunits...'
    
    # process all adunits
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

    print '\nprocessing creatives...'
    
    # process all creatives
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

    pickle_deref_cache()

    elapsed = time.time() - start
    print 'building deref cache took %i minutes and %i seconds' % (elapsed/60, elapsed%60)


if __name__ == '__main__':
    main()

