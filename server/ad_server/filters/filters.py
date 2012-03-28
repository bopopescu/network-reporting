import datetime
import logging, random
from ad_server.debug_console import trace_logging


from math import (atan2,
                   cos,
                   sin,
                   sqrt,
                   pow,
                   pi
                  )
from budget import budget_service
from reporting.models import StatsModel
from ad_server.parser.useragent_parser import get_os

from common.utils.decorators import deprecated

from common.constants import (VALID_FULL_FORMATS,
                              VALID_TABLET_FULL_FORMATS,
                              MIN_IOS_VERSION,
                              MAX_IOS_VERSION,
                              MIN_ANDROID_VERSION,
                              MAX_ANDROID_VERSION
                             )
###############################
# BASIC INCLUSION FILTERS
#
# --- Each filter function is a function which takes some arguments (or none) necessary
#       for the filter to work its magic. log_mesg is the message that will be logged
#       for the associated objects that eval'd to false.
# --- ALL FILTER GENERATOR FUNCTIONS MUST RETURN (filter_function, log_mesg, [])
# --- The empty list is the list that will contain all elt's for which the
# --- Filters should return TRUE if the element being tested should be kept
#
###############################

def budget_filter():
    log_mesg = "Removed due to being over budget: %s"
    def real_filter(a):
        # Check if we need smoothing, if so, use budgeting
        a.bid = a.bid or 0.0
        # The amount of budget doesn't really matter. As long as a budget
        # has.  This is technically incorrect for CPC/CPA ads, but because
        # of what was mentioned before, it doesn't really matter.


        # Turning off all budgeted campaigns because budgets are now going 
        # to be running live on the new adserver
        if a.campaign.budget_obj:
            return False
            #return (budget_service.has_budget(a.campaign.budget_obj, a.bid/1000))
        else:
            return True
    return (real_filter, log_mesg, [])

def active_filter():
    log_mesg = "Removed due to inactivity: %s"
    def real_filter(a):
        if not a.campaign.active or not a.active: return False
        if a.campaign.start_date and not (a.campaign.start_date <= StatsModel.today()): return False
        if a.campaign.end_date and not (StatsModel.today() <= a.campaign.end_date): return False
        if a.campaign.start_datetime and not(a.campaign.start_datetime <= datetime.datetime.now()): return False
        if a.campaign.end_datetime and not(datetime.datetime.now() <= a.campaign.end_datetime): return False
        return True
    return (real_filter, log_mesg, [])

def kw_filter(keywords):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter(adgroup):
        # if there are no keywords then we don't need to exclude
        if not adgroup.keywords:
            return True

        keyword_match = False
        # lists of tuples:
        # m_age:19 AND m_gender:m
        # m_age:20 AND m_gender:f
        # is transformed to
        # [(m_age:19,m_gender:m),(m_age:20,m_gender:f)]
        anded_keywords = [k.split(' AND ') for k in adgroup.keywords]
        trace_logging.info("KEYWORDS: %s == %s"%(keywords,anded_keywords))
        for anded_keyword in anded_keywords:
            anded_keyword = (kw.lower() for kw in anded_keyword)
            if set(anded_keyword) <= set(keywords):
                keyword_match = True
                break
        return keyword_match # return False if there is a match and vice versa
    return (real_filter, log_mesg, [])



def geo_filter(acceptable_geo_preds_list):
    log_mesg = "Removed due to geo mismatch: %s"
    def real_filter(a):
        # If this adgroup is LL targeted, then ignore this filter
        if a.cities and len(a.cities) > 0:
            return True
        return (set(acceptable_geo_preds_list).intersection(a.geographic_predicates) > set())
    return (real_filter, log_mesg, [])

def os_filter(user_agent):
    log_mesg = "Removed due to OS restrictions: %s"
    def real_filter(a):

        # Do not do device targeting if it is turned off
        if not a.device_targeting:
            return True

        user_os_name, user_model, user_os_version = get_os(user_agent)

        # If we don't know the user agent
        if user_os_name is None:
            if a.target_other:
                return True
            else:
                return False

        # We do know the OS but we don't know what the os_version is
        if user_os_version is None:
            if user_os_name == 'iOS':
                if a.target_iphone and a.target_ipod and a.target_ipad and a.ios_version_min == MIN_IOS_VERSION and a.ios_version_max == MAX_IOS_VERSION:
                    return True
                else:
                    return False
            elif user_os_name == 'android':
                if a.target_android and a.android_version_min == MIN_ANDROID_VERSION and a.android_version_max == MAX_ANDROID_VERSION:
                    return True
                else:
                    return False

        def in_range(user_nums, max_nums, min_nums):
            # Make all lists same length to make comparison easier
            max_len = max(len(user_nums), len(max_nums), len(min_nums))
            while len(user_nums) < max_len:
                user_nums.append('0')
            while len(max_nums) < max_len:
                max_nums.append('0')
            while len(min_nums) < max_len:
                min_nums.append('0')

            # Do comparison
            is_less = False
            is_more = False
            for i, num in enumerate(user_nums):
                if not is_less:
                    if int(num) > int(max_nums[i]):
                        return False
                    elif int(num) < int(max_nums[i]):
                        is_less = True
                if not is_more:
                    if int(num) < int(min_nums[i]):
                        return False
                    elif int(num) > int(min_nums[i]):
                        is_more = True

            # Comparison succeeded
            return True

        # We know the OS and the os_version
        user_nums = user_os_version.split('.')
        if user_os_name == "iOS":
            if user_model:
                if user_model == "iPhone" and not a.target_iphone:
                    return False
                elif user_model == "iPad" and not a.target_ipad:
                    return False
                elif user_model == "iPod" and not a.target_ipod:
                    return False
                else:
                    max_nums = a.ios_version_max.split('.')
                    min_nums = a.ios_version_min.split('.')
                    return in_range(user_nums, max_nums, min_nums)
        elif user_os_name == "android":
            if not a.target_android:
                return False
            else:
                max_nums = a.android_version_max.split('.')
                min_nums = a.android_version_min.split('.')
                return in_range(user_nums, max_nums, min_nums)

    return (real_filter, log_mesg, [])

def mega_filter(*filters):
    def actual_filter(a):
        for (f, msg, lst) in filters:
            if not f(a):
                lst.append(a)
                return False
        return True
    return actual_filter



######################################
#
# Creative filters
#
######################################

def format_filter(adunit):
    adunit_format = None if adunit.resizable else adunit.format
    log_mesg = "Removed due to format mismatch, expected " + str(adunit_format) + ": %s"
    def real_filter(creative):
        if not adunit_format or not creative.format:
            return True
        if creative.multi_format:
            if adunit_format in creative.multi_format:
                return True
        if adunit_format == 'full' or adunit_format == 'full_landscape':
            if creative.multi_format:
                return set(creative.multi_format).intersection(set(VALID_FULL_FORMATS)) > set()
            else:
                # if the creative is a full screen one, make sure its the correct orientation
                if creative.format in ['full','full_landscape']:
                    return creative.landscape == adunit.landscape
                else:
                    return creative.format in VALID_FULL_FORMATS
        if adunit_format == 'full_tablet' or adunit_format == 'full_tablet_landscape':
            if creative.multi_format:
                return set(creative.multi_format).intersection(set(VALID_TABLET_FULL_FORMATS)) > set()
            else:
                # if the creative is a full screen one, make sure its the correct orientation
                if creative.format in ['full_tablet', 'full_tablet']:
                    return creative.landscape == adunit.landscape
                else:
                    return creative.format in VALID_TABLET_FULL_FORMATS
        if adunit_format == 'custom' and creative.format == 'custom':
            return adunit.custom_width == creative.custom_width and adunit.custom_height == creative.custom_height
        return creative.format == adunit_format
    return (real_filter, log_mesg, [])

def exclude_filter(excluded_adgroup_keys):
    """ We exclude certain adgroups that we have already tried or wish
    to skip for other reasons """
    log_mesg = "Removed due to exclusion parameters: %s"
    def real_filter(adgroup):
        return not str(adgroup.key()) in excluded_adgroup_keys
    return (real_filter, log_mesg, [])

def ecpm_filter(winning_ecpm, creative_ecpm_dict):
    log_mesg = "Removed due to low eCPM: %s"
    def real_filter(creative):
        return creative_ecpm_dict[creative] >= winning_ecpm
    return (real_filter, log_mesg, [])

##############################################
#
#   FREQUENCY FILTERS
#
##############################################


def freq_filter(type, key_func, udid, now, frq_dict):
    """Function for constructing a frequency filter
    Super generic, made this way since all frequencies are just
     -verify frequency cap, if yes make sure we're not over it, otherwise carry on
    so I just made a way to generate them"""

    log_mesg = "Removed due to " + type + " frequency cap: %s"
    def real_filter(a):
        a_key = key_func(udid, now, a.key())
        #This is why all frequency cap attributes must follow the same naming convention, otherwise this
        #trick doesn't work
        try:
            frq_cap = getattr(a, '%s_frequency_cap' % type)
        except:
            frq_cap = 0

        if frq_cap and (a_key in frq_dict):
            imp_cnt = int(frq_dict[ a_key ])
        else:
            imp_cnt = 0
        #Log the current counts and cap
        trace_logging.warning("key: %s type: %s imps: %s, freq cap: %s" % (a_key, type.title(), imp_cnt, frq_cap))
        return (not frq_cap or imp_cnt < frq_cap)
    return (real_filter, log_mesg, [])

def alloc_filter(test_value=None):

    log_mesg = "Removed due to allocation cap: %s"
    def real_filter(a):
        d100f = test_value or random.random() * 100
        if a.allocation_percentage:
            if (d100f < a.allocation_percentage):
                return True
            else:
                return False
    return (real_filter, log_mesg, [])


#this is identical to mega_filter except it logs the adgroup
def all_freq_filter(*filters):
    def actual_filter(a):
        #print the adgroup title so the counts/cap printing in the acutal filter don't confuse things
        trace_logging.warning("Adgroup: %s" % a)
        for f, msg, lst in filters:
            if not f(a):
                lst.append(a)
                return False
        return True
    return actual_filter


#Technically this should be set by the user//adgroup, but right now we're just being static about things
CAPTURE_DIST = 50
EARTH_RADIUS = 3958.75587

def to_rad(x):
    return (pi*x)/180

def ll_dist(p1, p2):
    lat1, lng1 = (to_rad(x) for x in p1)
    lat2, lng2 = (to_rad(x) for x in p2)
    d_lat = lat2 - lat1
    d_lng = lng2 - lng1
    a = pow(sin(d_lat/2),2) + (cos(lat1) * cos(lat2) * pow(sin(d_lng/2),2))
    c = 2*atan2(sqrt(a), sqrt(1-a))
    return EARTH_RADIUS * c


def lat_lon_filter(ll=None):
    ll_p = None
    #ll should be input as a string, turn it into a list of floats
    if ll:
        ll_p = parse_lat_long(ll)#[float(val) for val in ll.split(',')]
    log_mesg = "Removed due to being outside target lat/long radii: %s"
    def real_filter(a):
        #If ll_p is none or adgroup has no city targets, dont' exclude
        if not ll_p or not a.cities or len(a.cities) == 0:
            return True
        #City format is ll:ste:city:ccode, split on ':', take the first entry, 'lat,lon', split that on ',' to get ('lat','lon')
        # for every city.  Apply map to this split list to get (float('lat'), float('lon'))
        latlons = ((float(k) for k in t.split(',')) for t in (city.split(':')[0] for city in a.cities))
        for lat, lon in latlons:
            #Check all lat, lon pairs.  If any one of them is too far, return True
            # since all filters are exclusion filters (True means don't keep it)
            if ll_dist((lat,lon),ll_p) < CAPTURE_DIST:
                return True
        return False
    return (real_filter, log_mesg, [])

def parse_lat_long(ll_str):
    # Try basic way first
    latlon = ll_str.split(",")
    if len(latlon) == 2:
        return [float(val) for val in latlon]
    elif len(latlon) == 4:
        lat = float('.'.join(latlon[:2]))
        lon = float('.'.join(latlon[2:]))
        return [lat, lon]
    else:
        return None

###############
# End filters
###############
