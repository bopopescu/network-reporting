import logging
import re       
import hashlib  


import datetime  
from common.constants import (KB, MB, GB)

from google.appengine.ext import blobstore
from google.appengine.ext import db

# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _
COUNTRY_PAT = re.compile(r' [a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z]);*[^a-zA-Z0-9-_]')

MB_PER_SHARD = 10
 

def to_uni(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj

def to_ascii(obj, encoding='utf-8'):  
    if isinstance(obj, unicode):  
        obj = obj.encode('utf-8')
    return obj
       
   
    
def get_country_code(headers, default='XX'):
    return headers.get('X-AppEngine-country', default)
    
def get_user_agent(request):
    return request.get('ua') or request.headers['User-Agent']    
    
def get_client_ip(request):
    return request.get('ip') or request.remote_addr

# dte:pub:adv:CC:BN:MN:OS:OSVER
STAT_KEY = "%s:%s:%s:%s:%s:%s:%s:%s"


def cust_sum(vals):
    tot = 0
    cur_type = None
    for val in vals:
        if cur_type is None:
            cur_type = type(val)
        elif not isinstance(val, cur_type):
            logging.warning(cur_type)
            logging.warning(val)
        if tot == 0 and isinstance(val, str):
            tot = val
        elif isinstance(val, int):
            tot += val
    return tot


def chunks(list, chunk_size):
    '''Generator function that creates chunk_size lists from list
    '''
    for idx in xrange(0, len(list), chunk_size):
        yield list[idx:idx+chunk_size]

# Must be len 8, must have format YYMMDDHH
# I'm not getting rid of this, but this is stupid, I should've jsut used strftime...duh....
def parse_time(time_str):
    if len(time_str) != 8:
        return None
    year = 2000 + int(time_str[:2])
    month = int(time_str[2:4])
    day = int(time_str[4:6])
    hour = int(time_str[6:])
    return datetime.datetime(year=year, month=month, day=day, hour=hour)

def clone_entity(ent, **extra_args):
    """Clones an entity ent, adding or overriding certain attributes
    as specified by extra_args

    Args:
        ent: entity to clone
        extra_args: constructor arguments to override/add to the entity being clone

    Returns:
        a cloned, possibly updated, version of ent
    """
    klass = ent.__class__
    #build old object property dict
    props = dict((k, v.__get__(ent, klass)) for k,v in klass.properties().iteritems())
    #update with new stuff
    props.update(extra_args)
    #create new object
    return klass(**props)

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


def build_key(template, template_dict):
    """ I got tired of not knowing what's what when building a key.
    This takes a dictionary and turns all db.Models into str(db.Model.key()), and all 
    db.Key()s into str(db.Key())s
    """
    new_vals = {}
    for k,v in template_dict.iteritems():
        if isinstance(v, db.Model):
            new_vals[k] = str(v.key())
        elif isinstance(v, db.Key):
            new_vals[k] = str(v)
    template_dict.update(new_vals)
    return template % template_dict


def campaign_stats(stat, type):
    if type == 'network':
        return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
    elif 'gtee' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, stat.revenue]
    elif 'promo' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, int(stat.conversion_count), stat.conv_rate]


def app_stats(stat):
    return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
