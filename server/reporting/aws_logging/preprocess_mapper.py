#!/usr/bin/python
import logging
import pickle
import sys
import traceback


# for EMR so log_parser and deref_cache.pkl can be found within each task
sys.path.append('.')

from log_parser import parse_logline, AD, IMP, CLK, OPEN, REQ


# DEREF_CACHE description:
# global dict containing str(key) mappings among publisher and advertiser models:
# {app_str: [account_str],
#  adunit_str: [app_str, account_str],
#  campaign_str: [account_str],
#  adgroup_str: [campaign_str, account_str],
#  creative_str: [adgroup_str, campaign_str, account_str]} 

DEREF_CACHE_PICKLE_FILE = 'deref_cache.pkl' 
try:
    pickle_file = open(DEREF_CACHE_PICKLE_FILE, 'rb')
    DEREF_CACHE = pickle.load(pickle_file)
    pickle_file.close()
    logging.warning('\nloading deref cache from %s ...\n' %DEREF_CACHE_PICKLE_FILE)
except:
    logging.warning('\ninitializing empty deref cache...\n')
    DEREF_CACHE = {}



def deref_models(handler, param_dict): 
    # params: 'udid', 'id', 'cid'    # id = adunit, cid = creative  TODO: udid currently not passed in to logs     
    if handler == REQ:
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            pub_models = DEREF_CACHE.get(adunit_str, None)
            adv_models = DEREF_CACHE.get(creative_str, None)
            if pub_models and adv_models:
                # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                [adgroup_str, campaign_str, account_str] = adv_models
                [app_str, account_str] = pub_models
                return "%s=%s,%s=%s,%s=%s,%s=%s,%s=%s,%s=%s" % ('adunit', adunit_str, 'app', app_str, \
                                                                 'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                 'account', account_str)
    
    # params: 'udid', 'id'  # id = adunit
    elif handler == AD:
        adunit_str = param_dict.get('id', None)
        if adunit_str:
            pub_models = DEREF_CACHE.get(adunit_str, None)
            if pub_models:
                [app_str, account_str] = pub_models
                return "%s=%s,%s=%s,%s=%s" % ('adunit', adunit_str, 'app', app_str, 'account', account_str)
    
    # params: 'udid', 'id', 'cid'   # id = adunit, cid = creative
    elif handler == IMP:
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            pub_models = DEREF_CACHE.get(adunit_str, None)
            adv_models = DEREF_CACHE.get(creative_str, None)
            if pub_models and adv_models:
                # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                [adgroup_str, campaign_str, account_str] = adv_models
                [app_str, account_str] = pub_models
                return "%s=%s,%s=%s,%s=%s,%s=%s,%s=%s,%s=%s" % ('adunit', adunit_str, 'app', app_str, \
                                                                 'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                 'account', account_str)
    
    # params: 'udid', 'appid', 'id', 'cid'  # appid = destination app, id = adunit, cid = creative
    elif handler == CLK:
        dest_app_str = param_dict.get('appid', None)
        adunit_str = param_dict.get('id', None)
        creative_str = param_dict.get('cid', None)

        if adunit_str and creative_str:
            pub_models = DEREF_CACHE.get(adunit_str, None)
            adv_models = DEREF_CACHE.get(creative_str, None)
            if pub_models and adv_models:
                # NOTE: put adv_models before put_models since there's a bug where account_str is NOT guaranteed to get retrieved from adv_models
                [adgroup_str, campaign_str, account_str] = adv_models
                [app_str, account_str] = pub_models
                return "%s=%s,%s=%s,%s=%s,%s=%s,%s=%s,%s=%s,%s=%s" % ('dest_app', dest_app_str, \
                                                                       'adunit', adunit_str, 'app', app_str, \
                                                                       'creative', creative_str, 'adgroup', adgroup_str, 'campaign', campaign_str, \
                                                                       'account', account_str)
        
    # params: 'udid', 'id'   # id = mobile_appid
    elif handler == OPEN:
        dest_app_str = param_dict.get('id', None)
        if dest_app_str:
            return "%s=%s" % ('dest_app', dest_app_str)
                   
    return None

    
def preprocess_logline(logline):
    logline_dict = parse_logline(logline)
    if logline_dict:
        handler = logline_dict.get('path', None)
        param_dict = logline_dict.get('params', None)

        # ex: 14/Mar/2011:15:04:09 -0700
        log_date = logline_dict.get('date', None)
        log_time = logline_dict.get('time', None)
        
        if handler and param_dict and log_date and log_time:
            if 'udid' in param_dict:    # unique user count requires udid 
                new_params = deref_models(handler, param_dict)
                if new_params:
                    new_logline = 'udid=%s,handler=%s,date=%s,time=%s,%s' \
                                    %(param_dict['udid'], handler, log_date, log_time, new_params)
                    return new_logline
    return None



def main():
    try:
        # read in output from dedup stage; key is original log line, value is frequency count (ignored)
        for line in sys.stdin:  
            parts = line.split('\t')
            if len(parts) != 2: continue
            
            line = parts[0] 
            pp_line = preprocess_logline(line)
            if pp_line:
                print "LongValueSum:%s\t%i" % (pp_line, 1)
    except:
        pass


if __name__ == '__main__':
    main()                        
            
       

