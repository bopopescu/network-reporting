import logging
import re       
import hashlib  

import reporting.models as reporting_models

def get_country_code(headers, default=reporting_models.DEFAULT_COUNTRY):
    return headers.get('X-AppEngine-country', default)
    
def get_user_agent(request):
    return request.get('ua') or request.headers['User-Agent']    
    
def get_client_ip(request):
    return request.get('ip') or request.remote_addr
    
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def make_mopub_id(raw_udid):
    """
    Converts a raw_udid into a mopub_id
    udid from the device comes as 
    udid=md5:asdflkjbaljsadflkjsdf (new clients) or
    udid=pqesdlsdfoqeld (old clients)
    For the newer clients we can just pass over the hashed string
    after "md5:"

    For older clients we must md5 hash the udid with salt 
    "mopub-" prepended.

    returns hashed_udid
    """                      
    raw_udid_parts = raw_udid.split('md5:')

    # if has md5: then just pull out value
    if len(raw_udid_parts) == 2:
        # get the part after 'md5:'
        hashed_udid = raw_udid_parts[-1]
    # else salt the udid and hash it    
    else:
        m = hashlib.md5()
        m.update('mopub-')
        m.update(raw_udid_parts[0])
        hashed_udid = m.hexdigest().upper() 
        
    # We call this hashed UDID the mopub_id
    return hashed_udid

    
def campaign_stats(stat, type):
    if type == 'network':
        return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
    elif 'gtee' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, stat.revenue]
    elif 'promo' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, int(stat.conversion_count), stat.conv_rate]


def app_stats(stat):
    return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
