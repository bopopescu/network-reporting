import logging
import re
import reporting.models as reporting_models

# matches sequence: space, 2 char, - or _, 2 char, 0 or more ;, followed by char that's not a char, number, - or _


def get_country_code(headers):
    logging.info(headers.get('X-AppEngine-country'), reporting_models.DEFAULT_COUNTRY))
    return headers.get('X-AppEngine-country'), reporting_models.DEFAULT_COUNTRY)
    
def get_user_agent(request):
    return request.get('ua') or request.headers['User-Agent']    
    
def get_ip(request):
    return request.get('ip') or request.remote_addr
    
def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]
    
def campaign_stats(stat, type):
    if type == 'network':
        return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
    elif 'gtee' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, stat.revenue]
    elif 'promo' in type:
        return [int(stat.impression_count), int(stat.click_count), stat.ctr, int(stat.conversion_count), stat.conv_rate]


def app_stats(stat):
    return [int(stat.request_count), int(stat.impression_count), stat.fill_rate, int(stat.click_count), stat.ctr]
