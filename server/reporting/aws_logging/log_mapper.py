#!/usr/bin/python
import cgi 
import re
import sys
from datetime import datetime
import urlparse


COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
    + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
    + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
    + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
    + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')


# handler types
AD = '/m/ad'
IMP = '/m/imp'
CLK = '/m/aclk'
OPEN = '/m/open'
REQ = '/m/req'

 
# # 56370:64.233.172.18 - - [15/Mar/2011:15:38:00 -0700] "GET /m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYwLQgDA&udid=mopubcanary&q=keywords HTTP/1.1" 200 1095 - "AppEngine-Google; (+http://code.google.com/appengine; appid: mopub-canary),gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_PARAMS = ['udid', 'id']
# 
# # 52798:76.173.252.144 - - [15/Mar/2011:15:00:06 -0700] "GET /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUYucAcDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGKm8IAw HTTP/1.1" 200 126 - "facebookhdLite/3.4.2 CFNetwork/485.13.8 Darwin/10.6.0,gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_IMP_PARAMS = ['udid', 'id', 'cid']   # id = adunit_id, cid = creative_id
# 
# # 54556:76.173.252.144 - - [15/Mar/2011:15:16:26 -0700] "GET /m/aclk?id=agltb3B1Yi1pbmNyDAsSBFNpdGUYucAcDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGKm8IAw&req=0efcbd3bfde383e1687bf8a85d8e671e HTTP/1.1" 200 126 - "facebookhdLite/3.4.2 CFNetwork/485.13.8 Darwin/10.6.0,gzip(gfe),gzip(gfe),gzip(gfe)"
# AD_CLICK_PARAMS = ['udid', 'appid', 'id', 'cid']    # appid = mobile_appid, id = adunit_id, cid = creative_id
# 
# # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA
# APP_OPEN_PARAMS = ['udid', 'id']    # id = mobile_appid
# 
# 
# AD_REQ_PARAMS = ['udid', 'id', 'cid'] # id = adunit_id



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


def format_kv_pair(handler, param_dict, date_hour):
    # return format:
    # k:adunit_id:creative_id:time, [req_count, imp_count, clk_count, conv_count, user_count]
    
    if handler == AD:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), '', date_hour), '[1, 0, 0, 0]'         
    if handler == IMP:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[0, 1, 0, 0]'         
    if handler == CLK:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[0, 0, 1, 0]'
    #if handler == CONV:
    if handler == REQ:
        return 'k:%s:%s:%s' % (param_dict.get('id', None), param_dict.get('cid', None), date_hour), '[1, 0, 0, 0]'
    return None, None
        
    
# abstract out core logic on parsing on handler params; this function is used for both mrjob (local testing) and boto (remote EMR job)
def generate_kv_pairs(line):
    logline_dict = parse_logline(line)
    if logline_dict:
        handler = logline_dict.get('path', None)
        param_dict = logline_dict.get('params', None)

        # ex: 14/Mar/2011:15:04:09 -0700
        log_date = logline_dict.get('date', None)
        log_time = logline_dict.get('time', None)
        # log_tz = logline_dict.get('tz', None)

        if handler and param_dict and log_date and log_time:# and log_tz:      
            # construct datetime object           
            date_hour = datetime.strptime(log_date + ':' + log_time, '%d/%b/%Y:%H:%M:%S')

            # resolution is hour
            hour_k, hour_v = format_kv_pair(handler, param_dict, date_hour.strftime('%y%m%d%H'))
            # resolution is day
            date_k, date_v = format_kv_pair(handler, param_dict, date_hour.strftime('%y%m%d'))

            if hour_k and 'None' not in hour_k and date_k and 'None' not in date_k:
                return hour_k, hour_v, date_k, date_v
    return None, None, None, None
                


def main():
    try:
        for line in sys.stdin:
            hour_k, hour_v, date_k, date_v = generate_kv_pairs(line)
            if hour_k and hour_v and date_k and date_v:
                print "%s\t%s" % (hour_k, hour_v)
                print "%s\t%s" % (date_k, date_v)
    except:
        pass


if __name__ == '__main__':
    main()
