import re

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


def auth_func():
    return "olp@mopub.com", "N47935"
