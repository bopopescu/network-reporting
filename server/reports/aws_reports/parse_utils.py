from datetime import datetime, date, timedelta
import time
import sys
import logging

sys.path.append('.')

MR1_KEY = '%s'
MR2_KEY = '%s:%s'
MR3_KEY = '%s:%s:%s'

APP = 'app'
AU = 'adunit'
CAMP = 'campaign'
CRTV = 'creative'
P = 'priority'
MO = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'
CO = 'country'
MAR = 'marketing'
BRND = 'brand'
OS = 'os'
OS_VER = 'os_ver'
KEY = 'kw'

AWS_ACCESS_KEY = 'AKIAJKOJXDCZA3VYXP3Q'
AWS_SECRET_KEY = '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'

JOBFLOW_NAME = 'generating report job'

NO_REQUESTS = (CAMP, CRTV, P)

DELIM = '|'

REPORT_NAME = '%s-%s-%s__%s-%s__%s.rep'

DATE_FMT = '%y%m%d'
DATE_FMT_HR = '%y%m%d%H'

DATE_HR_LEN = 8
DATE_LEN = 6

def gen_days(start, end):
    dt = timedelta(days=1)
    temp = start
    days = [temp]
    while temp < end:
        temp = temp + dt
        days.append(temp)
    return days

def get_key(line_dict, dim):
    """ Returns the key for a dim

    Args:
        line_dict: parsed log line
        dim: dimension that a key is needed for
    """
    #worry about resolving these when rendering the report, need for speed RIGHT NAO
    if APP == dim:
        return line_dict['adunit']
    elif AU == dim:
        return line_dict['adunit']
    elif CAMP == dim:
        return line_dict['creative']
    elif CRTV == dim:
        return line_dict['creative']
    elif P == dim:
        return line_dict['creative']
    elif MO == dim:
        return line_dict['time'].strftime('%y%m')
    elif WEEK == dim: 
        return line_dict['time'].strftime('%y%W')
    elif DAY == dim:
        return line_dict['time'].strftime('%y%m%d')
    elif HOUR == dim:
        return line_dict['time'].strftime('%H')
    elif CO == dim:
        #TODO somehow get the full country name from the 2 letter country code
        return line_dict['country']
    elif MAR == dim: 
        return line_dict['marketing_name']
    elif BRND == dim:
        return line_dict['brand_name']
    elif OS == dim:
        return line_dict['os']
    #iPhone:2.2 and Android:2.2 would both yield the same thing, this is wrong
    elif OS_VER == dim:
        return line_dict['os'] + '_'+ line_dict['os_ver']


# k = k:adunit_id:creative_id:country_code:brand_name:marketing_name:device_os:device_os_version:time
# v = [req_count, imp_count, clk_count, conv_count,]# user_count]
def parse_line(line):
    """ Takes a line from the stats Blobfile and turns it into a dictionary where values are
    of the correct type (ie not strings)

    Args:
        line: the line to be parsed
    """
    #get the key and value away from each other
    key, value = line.split('\t', 1)
    vals = eval(value)
    #ph = k, needed a placeholder 
    ph, adunit_id, creative_id, country, brand, marketing, os, os_ver, log_time = key.split(':')

    if len(log_time) == DATE_LEN:
        log_time = datetime.strptime(log_time, DATE_FMT)
    elif len(log_time) == DATE_HR_LEN:
        log_time = datetime.strptime(log_time, DATE_FMT_HR)

    au = adunit_id
    crtv = creative_id

    #Huzzah
    return dict(adunit = au,
                creative = crtv,
                country = country,
                brand_name = brand,
                marketing_name = marketing,
                os = os,
                os_ver = os_ver,
                time = log_time,
                vals = vals,
                )

def build_keys(line_dict, dim1, dim2, dim3):
    #if we're on a line w/ no creative it's a request line, return what we have
    if line_dict['creative'] == '' and dim1 in NO_REQUESTS:
        return []
    dim1_key = get_key(line_dict, dim1)   
    keys = [MR1_KEY % dim1_key]
    if dim2:
        if line_dict['creative'] == '' and dim2 in NO_REQUESTS:
            return keys
        dim2_key = get_key(line_dict, dim2)
        keys.append(MR2_KEY % (dim1_key, dim2_key))
    if dim3:
        if line_dict['creative'] == '' and dim3 in NO_REQUESTS:
            return keys 
        dim3_key = get_key(line_dict, dim3)
        keys.append(MR3_KEY % (dim1_key, dim2_key, dim3_key))
    return keys


def gen_report_fname(dim1, dim2, dim3, start, end):
    fname = REPORT_NAME % (dim1, dim2, dim3, start.strftime('%y%m%d'), end.strftime('%y%m%d'), int(time.time()))
    return fname


def parse_msg(msg):
    data = str(msg.get_body())
    try:
        dim1, dim2, dim3, start, end, rep_key, acct_key, timestamp = data.split(DELIM)
    except Exception:
        dim1, dim2, dim3, start, end, rep_key, acct_key = data.split(DELIM)
        timestamp = time.time()
    if dim2 == 'None':
        dim2 = None
    if dim3 == 'None':
        dim3 = None
    start = datetime.strptime(start, '%y%m%d')
    end = datetime.strptime(end, '%y%m%d')
    return (dim1, dim2, dim3, start, end, rep_key, acct_key, timestamp)

