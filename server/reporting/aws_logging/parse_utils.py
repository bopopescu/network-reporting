#!/usr/bin/python
import cgi
import os 
import re
import sys
import traceback
import urllib
import urlparse


# for EMR so imported modules can be found within each task
sys.path.append('.')

import utils
from wurfl import devices
from pywurfl.algorithms import TwoStepAnalysis

# search algo for WURFL
search_algo = TwoStepAnalysis(devices)


# takes a log line and parses it, detecting UserAgent, query parameters, origin IP and other information
#
# {'origin': '166.205.139.160', 'status': '200', 'tz': '-0700', 'referrer': '-', 'bytes': '761', 'auth': '-', 'identd': '-', 
# 'client': '"nearby-iphone/1.4 CFNetwork/459 Darwin/10.0.0d3,gzip(gfe),gzip(gfe)"', 'time': '16:08:09', 'date': '08/Sep/2010', 
# 'protocol': 'HTTP/1.1', 
# 'path': "/m/ad", 
# 'qs': "?v=1&f=320x50&udid=4bddad15bd08cbbfb2c804f4561828212d34acc2&ll=19.610787,-155.978178&q=Restaurants:%20Jameson's%20By%20the%20Sea%20&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRjpyQMM",
# 'params': {"v": ['1'] ... }
# 'method': 'GET'}
def parse_logline(logline, parse_ua=True):
    # some loglines have escaped double quotes in the user-agent string, which causes the logline regex 
    # to fail to match the user-agent string completely
    # example:
    # "Mozilla/5.0 (Linux; U; Android 2.3.1; de-de; \"HD2Droid-WP7\" Build/GRH78) AppleWebKit/533.1 (KHTML, like Gecko) Version/4.0 Mobile Safari/533.1,gzip(gfe),gzip(gfe),gzip(gfe)"
    logline = logline.replace(r'\"', '')
    
    m = utils.COMBINED_LOGLINE_PAT.match(logline)
    if m:
        d = m.groupdict()

        # also decode the path into a query dict
        d['path'] = urlparse.urlsplit(d['url'])[2]
        d['qs'] = urlparse.urlsplit(d['url'])[3]
        d['params'] = dict(cgi.parse_qsl(d['qs']))

        # parsing user-agent string can be computationally intensive (wurfl stuff), so only do it if specified
        if parse_ua:    
            if 'ua' in d['params']:
                # for 3rd party network requests, we encode the original user agent string as a query parameter
                original_ua = urllib.unquote(d['params']['ua'])
                d['country_code'] = get_country_code(original_ua)
                d['user_agent'] = get_user_agent_info(original_ua) 
            else:
                d['country_code'] = get_country_code(d['client'])
                d['user_agent'] = get_user_agent_info(d['client'])
        
        # do not double-count if 'exclude' parameter is present and its value is not empty
        if not ('exclude' in d['params'] and len(d['params']['exclude']) > 0):
            return d
    return None
    
    
# extracts uppercase two-letter country code from user_agent
def get_country_code(user_agent):
    m = utils.COUNTRY_PAT.search(user_agent)
    if m:
        country_code = m.group('ccode')
        return country_code.upper()
    return utils.DEFAULT_COUNTRY
        

# takes in the user_agent (client) section of the logline and returns a dict containing user_agent info
def get_user_agent_info(user_agent):        
    if not user_agent: 
        return {}   # return empty dict if user agent is not specified

    # strip away double quotes -- they screws up pywurfl search
    if user_agent.startswith('"') and user_agent.endswith('"'):
        user_agent = user_agent[1:-1]
    
    # remove locale, since it adds noise to pywurfl search
    user_agent = remove_locale(user_agent)
    
    # remove zip info at the end 
    user_agent = user_agent.replace(',gzip(gfe),gzip(gfe),gzip(gfe)', '')
    
    # if Apple mobile device, normalize user agent string
    ua_lower = user_agent.lower()
    if "iphone" in ua_lower or "ipod" in ua_lower or "ipad" in ua_lower:
        user_agent = normalize_apple_ua(user_agent)
        
    # pywurfl must take in user_agent as unicode string
    try:
        user_agent = unicode(user_agent)

        device = devices.select_ua(user_agent, search=search_algo)
        
        # retrieve relevant metadata, replace all spaces with _, and return them within dict
        # note that if a field is not available, empty string is returned
        info = {}
        info['brand_name'] = str(device.brand_name.replace(' ', '_') or utils.DEFAULT_VALUE)
        info['marketing_name'] = str((device.marketing_name or device.model_name).replace(' ', '_') or utils.DEFAULT_VALUE)
        info['device_os'] = str(device.device_os.replace(' ', '_') or utils.DEFAULT_VALUE)
        info['device_os_version'] = str(device.device_os_version.replace(' ', '_') or utils.DEFAULT_VALUE)

        # content inside (); for debugging purposes 
        blurb = re.search(r'\(.*?\)', user_agent)
        if blurb:
            info['blurb'] = str(blurb.group())
        else:
            info['blurb'] = str(user_agent)           

        return info
    except UnicodeDecodeError:
        sys.stderr.write('unicode decode error -> %s\n' %user_agent)
        # traceback.print_exc()
        return {}
    except:
        # traceback.print_exc()
        return {}


def remove_locale(user_agent):
    m = utils.LOCALE_PAT.search(user_agent)
    if m:
        locale = m.group('locale')
        user_agent = user_agent.replace(locale, '')
    return user_agent
        

def normalize_apple_ua(user_agent):    
    # replace periods in OS version number with underscores
    # input:
    # facebookhdLite/3.5.1  (iPad; U; CPU iPhone OS 4.3.1 like Mac OS X;)
    # output:
    # facebookhdLite/3_5_1  (iPad; U; CPU iPhone OS 4_3_1 like Mac OS X;)
    user_agent = user_agent.replace('.', '_')

    # replace first token with browser version Mozilla/5.0
    # input:
    # facebookhdLite/3_5_1  (iPad; U; CPU iPhone OS 4_3_1 like Mac OS X;)
    # output:
    # Mozilla/5.0 (iPad; U; CPU iPhone OS 4_3_1 like Mac OS X;)
    user_agent = r'Mozilla/5.0 ' + ' '.join(user_agent.split()[1:])
    
    return user_agent
