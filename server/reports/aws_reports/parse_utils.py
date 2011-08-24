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

def gen_days(start, end, hours=False):
    dt = timedelta(days=1)
    temp = start
    days = [temp]
    while temp != end:
        temp = temp + dt
        days.append(temp)
    if hours:
        return reduce(lambda x,y: x+y, get_hours(days))
    else:
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
    if AU == dim:
        return line_dict['adunit']
    if CAMP == dim:
        return line_dict['creative']
    if CRTV == dim:
        return line_dict['creative']
    if P == dim:
        return line_dict['creative']
    if MO == dim:
        return line_dict['time'].strftime('%y%m')
    if WEEK == dim: 
        return line_dict['time'].strftime('%y%m%W')
    if DAY == dim:
        return line_dict['time'].strftime('%y%m%d')
    if HOUR == dim:
        return line_dict['time'].strftime('%y%m%d%H')
    if CO == dim:
        #TODO somehow get the full country name from the 2 letter country code
        return line_dict['country']
    if MAR == dim: 
        return line_dict['marketing_name']
    if BRND == dim:
        return line_dict['brand_name']
    if OS == dim:
        return line_dict['os']
    #iPhone:2.2 and Android:2.2 would both yield the same thing, this is wrong
    if OS_VER == dim:
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
    ph, adunit_id, creative_id, country, brand, marketing, os, os_ver, time = key.split(':')

    if len(time) == DATE_LEN:
        time = datetime.strptime(time, DATE_FMT)
    elif len(time) == DATE_HR_LEN:
        time = datetime.strptime(time, DATE_FMT_HR)

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
                time = time,
                vals = vals,
                )

def build_keys(line_dict, d1, d2, d3):
    #if we're on a line w/ no creative it's a request line, return what we have
    if line_dict['creative'] == '' and d1 in NO_REQUESTS:
        return []
    d1_key = get_key(line_dict, d1)   
    keys = [MR1_KEY % d1_key]
    if d2:
        if line_dict['creative'] == '' and d2 in NO_REQUESTS:
            return keys
        d2_key = get_key(line_dict, d2)
        keys.append(MR2_KEY % (d1_key, d2_key))
    if d3:
        if line_dict['creative'] == '' and d3 in NO_REQUESTS:
            return keys 
        d3_key = get_key(line_dict, d3)
        keys.append(MR3_KEY % (d1_key, d2_key, d3_key))
    return keys


def gen_report_fname(d1, d2, d3, start, end):
    fname = REPORT_NAME % (d1, d2, d3, start.strftime('%y%m%d'), end.strftime('%y%m%d'), int(time.time()))
    return fname


def parse_msg(msg):
    data = str(msg.get_body())
    d1, d2, d3, start, end, rep_key, acct_key = data.split(DELIM)
    if d2 == 'None':
        d2 = None
    if d3 == 'None':
        d3 = None
    start = datetime.strptime(start, '%y%m%d')
    end = datetime.strptime(end, '%y%m%d')
    return (d1, d2, d3, start, end, rep_key, acct_key)


def get_waiting_jobflow(conn):
    waiting_jobflows = conn.describe_jobflows([u'WAITING'])
    for jobflow in waiting_jobflows:
        if jobflow.name != JOBFLOW_NAME:
            continue
        jid = jobflow.jobflowid
        num_steps = len(jobflow.steps)
        print 'found waitingjobflow %s with %i steps completed' % (jid, num_steps)
        if num_steps > 250:
            print 'num of steps near limit of 256: terminating jobflow %s ...' % (jobid)
            conn.terminate_jobflow(jid)
        else:
            return jid, num_steps
    return None, 0


