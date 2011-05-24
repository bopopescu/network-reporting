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
from parse_utils import parse_logline
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import Site as AdUnit, App
from reporting.models import StatsModel, Pacific_tzinfo


STATUS_STEP = 100000

# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:
# {app_str: [account_str],
#  adunit_str: [app_str, account_str],
#  campaign_str: [account_str],
#  adgroup_str: [campaign_str, account_str],
#  creative_str: [adgroup_str, campaign_str, account_str]} 

DEREF_CACHE_PICKLE_FILE = 'deref_cache.pkl' 
try:
    with open(DEREF_CACHE_PICKLE_FILE, 'rb') as pickle_file:
        DEREF_CACHE = pickle.load(pickle_file)
        print '\nloading deref cache from %s ...\n' %DEREF_CACHE_PICKLE_FILE
except:
    print '\ninitializing empty deref cache...\n'
    DEREF_CACHE = {}


# returns [account_str]
def deref_app(app_str):
    if app_str in DEREF_CACHE:
        return DEREF_CACHE[app_str]

    try:
        app_key = db.Key(app_str)
        app = App.get(app_key)
        account_str = str(app._account)
        DEREF_CACHE[app_str] = [account_str]
        return [account_str]
    except BadKeyError, e:
        print 'EXCEPTION on app %s: %s' %(app_str, e)
        return None
    except Exception, e:
        # traceback.print_exc() 
        return None


# returns [app_str, account_str]
def deref_adunit(adunit_str):
    if adunit_str in DEREF_CACHE:
        return DEREF_CACHE[adunit_str]

    try:
        adunit_key = db.Key(adunit_str)
        adunit = AdUnit.get(adunit_key)
        app_str = str(adunit._app_key)
        account_str = str(adunit._account)
        DEREF_CACHE[adunit_str] = [app_str, account_str]
        return [app_str, account_str]
    except BadKeyError, e:
        print 'EXCEPTION on adunit %s: %s' %(adunit_str, e)
        return None
    except Exception, e:
        # print 'ADUNIT_STR:', adunit_str
        # traceback.print_exc()
        return None


# returns [account_str]
def deref_campaign(campaign_str):
    if campaign_str in DEREF_CACHE:
        return DEREF_CACHE[campaign_str]

    try:
        campaign_key = db.Key(campaign_str)
        campaign = Campaign.get(campaign_key)
        account_str = str(campaign._account)
        DEREF_CACHE[campaign_str] = [account_str]
        return [account_str]
    except BadKeyError, e:
        print 'EXCEPTION on campaign %s: %s' %(campaign_str, e)
        return None
    except Exception, e:
        # traceback.print_exc()
        return None


# returns [campaign_str, account_str]
def deref_adgroup(adgroup_str):
    if adgroup_str in DEREF_CACHE:
        return DEREF_CACHE[adgroup_str]

    try:
        adgroup_key = db.Key(adgroup_str)
        adgroup = AdGroup.get(adgroup_key)
        campaign_str = str(adgroup._campaign)
        account_str = str(adgroup._account)
        DEREF_CACHE[adgroup_str] = [campaign_str, account_str]
        return [campaign_str, account_str]
    except BadKeyError, e:
        print 'EXCEPTION on adgroup %s: %s' %(adgroup_str, e)
        return None
    except Exception, e:
        # traceback.print_exc()
        return None


# returns [adgroup_str, campaign_str, account_str]
def deref_creative(creative_str):
    if creative_str in DEREF_CACHE:
        return DEREF_CACHE[creative_str]

    try:
        creative_key = db.Key(creative_str)
        creative = Creative.get(creative_key)
        adgroup_str = str(creative._ad_group)        
        adgroup_deref_results = deref_adgroup(adgroup_str)
        if adgroup_deref_results:
            [campaign_str, account_str] = adgroup_deref_results
            DEREF_CACHE[creative_str] = [adgroup_str, campaign_str, account_str]
            return [adgroup_str, campaign_str, account_str]
    except BadKeyError, e:
        print 'EXCEPTION on creative %s: %s' %(creative_str, e)
        return None
    except Exception, e:
        # print 'CREATIVE_STR:', creative_str
        # traceback.print_exc()
        return None


def deref_models(handler, param_dict): 
    # params: 'udid', 'id', 'cid'    # id = adunit, cid = creative  TODO: udid currently not passed in to logs     
    if handler == utils.REQ:
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            deref_adunit(adunit_str)
            deref_creative(creative_str)

    
    # params: 'udid', 'id'  # id = adunit
    elif handler == utils.AD:
        adunit_str = param_dict.get('id', None)
        if adunit_str:
            deref_adunit(adunit_str)

    
    # params: 'udid', 'id', 'cid'   # id = adunit, cid = creative
    elif handler == utils.IMP:
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            deref_adunit(adunit_str)
            deref_creative(creative_str)

    
    # params: 'udid', 'appid', 'id', 'cid'  # appid = destination app, id = adunit, cid = creative
    elif handler == utils.CLK:
        dest_app_str = param_dict.get('appid', None)
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            deref_adunit(adunit_str)
            deref_creative(creative_str)
                
    
def deref_logline(logline):
    logline_dict = parse_logline(logline, parse_ua=False)

    if logline_dict:
        handler = logline_dict.get('path', None)
        param_dict = logline_dict.get('params', None)

        # ex: 14/Mar/2011:15:04:09 -0700
        log_date = logline_dict.get('date', None)
        log_time = logline_dict.get('time', None)
        
        if handler and param_dict and log_date and log_time:
            if 'udid' in param_dict:    # unique user count requires udid 
                deref_models(handler, param_dict)
                return True
    return False


def preprocess_logs(input_file):
    with open(input_file, 'r') as in_stream:
        count = 0
        for line in in_stream:
            derefed = deref_logline(line)
            if derefed:
                count += 1
                if count % STATUS_STEP == 0:
                    print '%ix %ik lines pre-processed successfully' %(count/STATUS_STEP, STATUS_STEP/1000)
            
       
def main():
    start = time.time()
    
    parser = OptionParser()
    parser.add_option('-f', '--input_file', dest='input_file')
    (options, args) = parser.parse_args()
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', utils.auth_func, host)
    
    preprocess_logs(options.input_file)

    # pickle deref cache 
    with open(DEREF_CACHE_PICKLE_FILE, 'wb') as pickle_file:
        pickle.dump(DEREF_CACHE, pickle_file)

    elapsed = time.time() - start
    print 'building deref cache took %i minutes and %i seconds' % (elapsed/60, elapsed%60)
    

if __name__ == '__main__':
    main()
