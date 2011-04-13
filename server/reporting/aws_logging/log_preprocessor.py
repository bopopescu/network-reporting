import cgi
import os 
import pickle
import re
import sys
import time
import traceback
import urlparse

from optparse import OptionParser

# for ubuntu EC2
sys.path.append("/home/ubuntu/mopub/server")
sys.path.append("/home/ubuntu/mopub/server/reporting")
sys.path.append("/home/ubuntu/google_appengine")
sys.path.append("/home/ubuntu/google_appengine/lib/django")
sys.path.append("/home/ubuntu/google_appengine/lib/webob")
sys.path.append("/home/ubuntu/google_appengine/lib/yaml/lib")
sys.path.append("/home/ubuntu/google_appengine/lib/fancy_urllib")

from google.appengine.ext import db
from google.appengine.ext.db import BadKeyError
from google.appengine.ext.remote_api import remote_api_stub

# for run_jobflow.sh
sys.path.append(os.getcwd()+'/../../')

from log_parser import parse_logline, AD, IMP, CLK, OPEN, REQ
from advertiser.models import Campaign, AdGroup, Creative
from publisher.models import Site as AdUnit, App
from reporting.models import StatsModel, Pacific_tzinfo

import utils


# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:
# {app_str: [account_str],
#  adunit_str: [app_str, account_str],
#  campaign_str: [account_str],
#  adgroup_str: [campaign_str, account_str],
#  creative_str: [adgroup_str, campaign_str, account_str]} 

DEREF_CACHE_PICKLE_FILE = 'deref_cache.pkl' 
if os.path.isfile(DEREF_CACHE_PICKLE_FILE):
    with open(DEREF_CACHE_PICKLE_FILE, 'rb') as pickle_file:
        DEREF_CACHE = pickle.load(pickle_file)
        print '\nloading deref cache from %s ...\n' %DEREF_CACHE_PICKLE_FILE
else:
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
        print "EXCEPTION on app %s: %s" %(app_str, e)
        return None
    except Exception, e:
        #traceback.print_exc() # comment out for now; too many ill-formated keys that flood the output logs
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
        print "EXCEPTION on adunit %s: %s" %(adunit_str, e)
        return None
    except Exception, e:
        #traceback.print_exc()
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
        print "EXCEPTION on campaign %s: %s" %(campaign_str, e)
        return None
    except Exception, e:
        #traceback.print_exc()
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
        print "EXCEPTION on adgroup %s: %s" %(adgroup_str, e)
        return None
    except Exception, e:
        #traceback.print_exc()
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
        print "EXCEPTION on creative %s: %s" %(creative_str, e)
        return None
    except Exception, e:
        #traceback.print_exc()
        return None


def deref_models(logline_dict): 
    handler = logline_dict.get('path', None)
    param_dict = logline_dict.get('params', None)
    
    if handler and param_dict:

        # params: 'udid', 'id', 'cid'    # id = adunit, cid = creative  TODO: udid currently not passed in to logs     
        if handler == REQ:
            adunit_str = param_dict.get('id', None)
            creative_str = param_dict.get('cid', None)

            if adunit_str and creative_str:
                pub_models = deref_adunit(adunit_str)
                adv_models = deref_creative(creative_str)
                if pub_models and adv_models:
                    # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                    [adgroup_str, campaign_str, account_str] = adv_models
                    [app_str, account_str] = pub_models
                    return "&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s" % ('adunit', adunit_str, 'app', app_str, \
                                                                     'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                     'account', account_str)
        
        # params: 'udid', 'id'  # id = adunit
        if handler == AD:
            adunit_str = param_dict.get('id', None)
            if adunit_str:
                pub_models = deref_adunit(adunit_str)
                if pub_models:
                    [app_str, account_str] = pub_models
                    return "&%s=%s&%s=%s&%s=%s" % ('adunit', adunit_str, 'app', app_str, 'account', account_str)
        
        # params: 'udid', 'id', 'cid'   # id = adunit, cid = creative
        if handler == IMP:
            adunit_str = param_dict.get('id', None)
            creative_str = param_dict.get('cid', None)

            if adunit_str and creative_str:
                pub_models = deref_adunit(adunit_str)
                adv_models = deref_creative(creative_str)
                if pub_models and adv_models:
                    # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                    [adgroup_str, campaign_str, account_str] = adv_models
                    [app_str, account_str] = pub_models
                    return "&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s" % ('adunit', adunit_str, 'app', app_str, \
                                                                     'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                     'account', account_str)
        
        # params: 'udid', 'appid', 'id', 'cid'  # appid = destination app, id = adunit, cid = creative
        if handler == CLK:
            dest_app_str = param_dict.get('appid', None)
            adunit_str = param_dict.get('id', None)
            creative_str = param_dict.get('cid', None)

            if adunit_str and creative_str:
                pub_models = deref_adunit(adunit_str)
                adv_models = deref_creative(creative_str)
                if pub_models and adv_models:
                    # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                    [adgroup_str, campaign_str, account_str] = adv_models
                    [app_str, account_str] = pub_models
                    return "&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s&%s=%s" % ('dest_app', dest_app_str, \
                                                                           'adunit', adunit_str, 'app', app_str, \
                                                                           'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                           'account', account_str)
            
        # params: 'udid', 'id'   # id = mobile_appid
        if handler == OPEN:
            dest_app_str = param_dict.get('id', None)
            if dest_app_str:
                return "&%s=%s" % ('dest_app', dest_app_str)
                   
    return None

    
def preprocess_logline(logline):
    logline_dict = parse_logline(logline)
    if logline_dict:
        param_dict = logline_dict.get('params', None)
        if 'udid' in param_dict:# and 'account' in param_dict:    # unique user count requires udid and account
            new_params = deref_models(logline_dict)
            if new_params:
                old_qs = logline_dict['qs']
                new_logline = logline.replace(old_qs, old_qs + new_params)            
                return new_logline
    return None


def preprocess_logs(input_file):
    output_file = input_file + ".pp"  # .pp for preprocessed
    with open(input_file, 'r') as in_stream:
        with open(output_file, 'w') as out_stream:
            for line in in_stream:
                pp_line = preprocess_logline(line)
                if pp_line:
                    out_stream.write(pp_line)
            
       
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
    print 'preprocessing logs took %i minutes and %i seconds' % (elapsed/60, elapsed%60)
    print 'preprocessed logs written to %s.pp'%options.input_file
    

if __name__ == '__main__':
    main()
