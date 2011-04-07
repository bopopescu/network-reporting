import logging 
from math import ( atan2,
                   cos,
                   sin,
                   sqrt,
                   pow,
                   pi
                   )
from budget import budget_service
from reporting.models import StatsModel

from common.constants import VALID_FULL_FORMATS, VALID_TABLET_FULL_FORMATS
###############################
# BASIC INCLUSION FILTERS
#
# --- Each filter function is a function which takes some arguments (or none) necessary 
#       for the filter to work its magic. log_mesg is the message that will be logged 
#       for the associated objects that eval'd to false.
# --- ALL FILTER GENERATOR FUNCTIONS MUST RETURN ( filter_function, log_mesg, [] )
# --- The empty list is the list that will contain all elt's for which the 
# --- Filters should return TRUE if the element being tested should be kept
#       
###############################

def budget_filter():
    log_mesg = "Removed due to being over budget: %s"
    def real_filter( a ):
        # Check if we need smoothing, if so, use budgeting
        return (budget_service.has_budget(a.campaign, a.bid/1000))
    return ( real_filter, log_mesg, [] )

def active_filter():
    log_mesg = "Removed due to inactivity: %s"
    def real_filter( a ):
        return ( a.campaign.active and ( a.campaign.start_date  >= StatsModel.today() if a.campaign.start_date else True ) and ( StatsModel.today() <= a.campaign.end_date if a.campaign.end_date else True ) )
    return ( real_filter, log_mesg, [] )

def kw_filter( keywords ):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter( a ):
        return ( not a.keywords or set( keywords ).intersection( a.keywords ) > set() )
    return ( real_filter, log_mesg, [] )

def geo_filter( geo_preds ):
    log_mesg = "Removed due to geo mismatch: %s"
    def real_filter( a ):
        return ( set( geo_preds ).intersection( a.geographic_predicates ) > set() )
    return ( real_filter, log_mesg, [] )

def device_filter( dev_preds ):
    log_mesg = "Removed due to device mismatch: %s"
    def real_filter( a ):
        return ( set( dev_preds ).intersection( a.device_predicates ) > set() )
    return ( real_filter, log_mesg, [] )

def mega_filter( *filters ): 
    def actual_filter( a ):
        for ( f, msg, lst ) in filters:
            if not f( a ):
                lst.append( a )
                return False
        return True
    return actual_filter

######################################
#
# Creative filters
#
######################################

def format_filter( format ):
    log_mesg = "Removed due to format mismatch, expected " + str( format ) + ": %s"
    def real_filter( creative ):
        if not format or not creative.format:
            return True 
        if creative.multi_format:
            if format in creative.multi_format:
                return True
        if format == 'full' or format == 'full_landscape':
            if creative.multi_format:
                return set(creative.multi_format).intersection(set(VALID_FULL_FORMATS)) > set()
            else:
                return creative.format in VALID_FULL_FORMATS
        if format == 'full_tablet' or format == 'full_tablet_landscape':
            if creative.multi_format:
                return set(creative.multi_format).intersection(set(VALID_TABLET_FULL_FORMATS)) > set()
            else:
                return creative.format in VALID_TABLET_FULL_FORMATS
        return creative.format == format
    return ( real_filter, log_mesg, [] )

def exclude_filter( excl_params ):
    log_mesg = "Removed due to exclusion parameters: %s"
    # NOTE: we are excluding on ad type not the creative id
    def real_filter( creative ):
        return not creative.ad_type in excl_params 
    return ( real_filter, log_mesg, [] )

def ecpm_filter( winning_ecpm ):
    log_mesg = "Removed due to being a loser: %s"
    def real_filter( creative ):
        return creative.e_cpm() >= winning_ecpm
    return ( real_filter, log_mesg, [] )

##############################################
#
#   FREQUENCY FILTERS
#
##############################################


def freq_filter( type, key_func, udid, now, frq_dict ):
    """Function for constructing a frequency filter
    Super generic, made this way since all frequencies are just
     -verify frequency cap, if yes make sure we're not over it, otherwise carry on
    so I just made a way to generate them"""
    
    log_mesg = "Removed due to " + type + " frequency cap: %s"
    def real_filter( a ):
        a_key = key_func( udid, now, a.key() )
        #This is why all frequency cap attributes must follow the same naming convention, otherwise this
        #trick doesn't work
        try:
            frq_cap = getattr( a, '%s_frequency_cap' % type ) 
        except:
            frq_cap = 0

        if frq_cap and ( a_key in frq_dict ):
            imp_cnt = int( frq_dict[ a_key ] )
        else:
            imp_cnt = 0
        #Log the current counts and cap
        logging.warning( "%s imps: %s, freq cap: %d" % ( type.title(), imp_cnt, frq_cap ) )
        return ( not frq_cap or imp_cnt < frq_cap )
    return ( real_filter, log_mesg, [] )

#this is identical to mega_filter except it logs the adgroup 
def all_freq_filter( *filters ):
    def actual_filter( a ):
        #print the adgroup title so the counts/cap printing in the acutal filter don't confuse things
        logging.warning( "Adgroup: %s" % a )
        for f, msg, lst in filters:
            if not f( a ):
                lst.append( a )
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
    if ll is not None:
        ll_p = [float(val) for val in ll.split(',')]
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

def kw_filter( keywords ):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter( adgroup ):
        # if there are no keywords then we don't need to exclude
        if not adgroup.keywords:
            return True 
        
        keyword_match = True
        # lists of tuples:
        # m_age:19 AND m_gender:m
        # m_age:20 AND m_gender:f
        # is transformed to
        # [(m_age:19,m_gender:m),(m_age:20,m_gender:f)]
        anded_keywords = [k.split(' AND ') for k in adgroup.keywords] 
        logging.info("KEYWORDS: %s == %s"%(keywords,anded_keywords))
        for anded_keywords in anded_keywords:
            anded_keywords = (kw.lower() for kw in anded_keywords)
            if set(anded_keywords) <= set(keywords):
                keyword_match = False 
                break
        return keyword_match # return False if there is a match and vice versa        
    return ( real_filter, log_mesg, [] )

###############
# End filters
###############
