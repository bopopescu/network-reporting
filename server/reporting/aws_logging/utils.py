from __future__ import with_statement
import os
import pickle
import re
import sys
import traceback


# same as patterns defined in common.utils.heplers
# the reason we are re-defining them here is to minimize path issues for EMR and run_jobflow.sh as well as to reduce the number of cache files needed for EMR
# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _
COUNTRY_PAT = re.compile(r' [a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z]);*[^a-zA-Z0-9-_]')
LOCALE_PAT = re.compile(r'(?P<locale> [a-zA-Z][a-zA-Z][-_][a-zA-Z][a-zA-Z];*)[^a-zA-Z0-9-_]')


COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
    + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
    + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
    + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
    + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')


# Handler types:
# /m/ad?
# params = ['udid', 'id']
# 
# /m/imp?
# params = ['udid', 'id', 'cid']   # id = adunit_id, cid = creative_id
# 
# /m/aclk?
# params = ['udid', 'appid', 'id', 'cid']    # appid = mobile_appid, id = adunit_id, cid = creative_id
# 
# /m/open?
# params = ['udid', 'id']    # id = mobile_appid
# 
# /m/req?
# params = ['udid', 'id', 'cid'] # id = adunit_id
AD = '/m/ad'
IMP = '/m/imp'
CLK = '/m/aclk'
OPEN = '/m/open'
REQ = '/m/req'

# default country code, same as constant defined in reporting.models
# the reason we are re-defining it here is to minimize path issues for EMR and run_jobflow.sh as well as to reduce the number of cache files needed for EMR
DEFAULT_COUNTRY = 'XX'

# default value for brand_name, marketing_name, device_os, device_os_version since '' is interpreted as * in keyname
DEFAULT_VALUE = 'N/A'

# deref cache 
DEREF_CACHE_PICKLE_FILE = 'deref_cache.pkl' 

def load_deref_cache(pkl_file_name=DEREF_CACHE_PICKLE_FILE):
    try:
        print '\nloading deref cache from %s ...' % (pkl_file_name)
        with open(pkl_file_name, 'rb') as pickle_file:
            deref_cache = pickle.load(pickle_file)
        print 'loaded %i records\n' % (len(deref_cache))
        return deref_cache
    except:
        traceback.print_exc()
        print '\ninitializing empty deref cache...\n'
        return {}


def auth_func():
    return "olp@mopub.com", "N47935N47935"


def setup_remote_api():
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

    # from appengine_django import InstallAppengineHelperForDjango
    # InstallAppengineHelperForDjango()

    from google.appengine.ext.remote_api import remote_api_stub
    
    
    app_id = 'mopub-inc'
    host = '38-aws.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)
    
