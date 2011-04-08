import cgi
import os 
import re
import sys
import traceback
import urlparse

COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
    + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
    + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
    + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
    + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')


# Handler types:
# 56370:64.233.172.18 - - [15/Mar/2011:15:38:00 -0700] "GET /m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYwLQgDA&udid=mopubcanary&q=keywords HTTP/1.1" 200 1095 - "AppEngine-Google; (+http://code.google.com/appengine; appid: mopub-canary),gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_PARAMS = ['udid', 'id']
# 
# 52798:76.173.252.144 - - [15/Mar/2011:15:00:06 -0700] "GET /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUYucAcDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGKm8IAw HTTP/1.1" 200 126 - "facebookhdLite/3.4.2 CFNetwork/485.13.8 Darwin/10.6.0,gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_IMP_PARAMS = ['udid', 'id', 'cid']   # id = adunit_id, cid = creative_id
# 
# 54556:76.173.252.144 - - [15/Mar/2011:15:16:26 -0700] "GET /m/aclk?id=agltb3B1Yi1pbmNyDAsSBFNpdGUYucAcDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGKm8IAw&req=0efcbd3bfde383e1687bf8a85d8e671e HTTP/1.1" 200 126 - "facebookhdLite/3.4.2 CFNetwork/485.13.8 Darwin/10.6.0,gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_CLICK_PARAMS = ['udid', 'appid', 'id', 'cid']    # appid = mobile_appid, id = adunit_id, cid = creative_id
# 
# /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA
# APP_OPEN_PARAMS = ['udid', 'id']    # id = mobile_appid
# 
# AD_REQ_PARAMS = ['udid', 'id', 'cid'] # id = adunit_id
AD = '/m/ad'
IMP = '/m/imp'
CLK = '/m/aclk'
OPEN = '/m/open'
REQ = '/m/req'


# takes a log line and parses it, detecting UserAgent, query parameters, origin IP and other information
#
# {'origin': '166.205.139.160', 'status': '200', 'tz': '-0700', 'referrer': '-', 'bytes': '761', 'auth': '-', 'identd': '-', 
# 'client': '"nearby-iphone/1.4 CFNetwork/459 Darwin/10.0.0d3,gzip(gfe),gzip(gfe)"', 'time': '16:08:09', 'date': '08/Sep/2010', 
# 'protocol': 'HTTP/1.1', 
# 'path': "/m/ad", 
# 'qs': "?v=1&f=320x50&udid=4bddad15bd08cbbfb2c804f4561828212d34acc2&ll=19.610787,-155.978178&q=Restaurants:%20Jameson's%20By%20the%20Sea%20&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRjpyQMM",
# 'params': {"v": ['1'] ... }
# 'method': 'GET'}
def parse_logline(logline):
    m = COMBINED_LOGLINE_PAT.match(logline)
    if m:
        d = m.groupdict()

        # also decode the path into a query dict
        d['path'] = urlparse.urlsplit(d.get('url'))[2]
        d['qs'] = urlparse.urlsplit(d.get('url'))[3]
        d['params'] = dict(cgi.parse_qsl(d['qs']))
        
        # do not double-count if 'exclude' parameter is present and its value is not empty
        if not ('exclude' in d['params'] and len(d['params']['exclude']) > 0):
            return d
    return None