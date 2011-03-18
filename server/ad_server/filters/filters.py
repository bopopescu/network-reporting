from math import ( atan2,
                   cos,
                   sin,
                   sqrt,
                   pow,
                   pi
                   )
import logging
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
            return False
        #City format is ll:ste:city:ccode, split on ':', take the first entry, 'lat,lon', split that on ',' to get ('lat','lon') 
        # for every city.  Apply map to this split list to get (float('lat'), float('lon'))
        latlons = ((float(k) for k in t.split(',')) for t in (city.split(':')[0] for city in a.cities))
        for lat, lon in latlons:
            #Check all lat, lon pairs.  If any one of them is too far, return True
            # since all filters are exclusion filters (True means don't keep it)
            if ll_dist((lat,lon),ll_p) < CAPTURE_DIST:
                return False 
        return True 
    return (real_filter, log_mesg, [])

def kw_filter( keywords ):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter( adgroup ):
        # if there are no keywords then we don't need to exclude
        if not adgroup.keywords:
            return False 
        
        keyword_match = False
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
                keyword_match = True
                break
        return not keyword_match # return False if there is a match and vice versa        
    return ( real_filter, log_mesg, [] )
