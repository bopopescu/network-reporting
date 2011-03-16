from math import ( atan2,
                   cos,
                   sin,
                   sqrt,
                   pow,
                   pi
                   )
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
    if ll is not None:
        ll_p = [float(val) for val in ll.split(',')]
    log_mesg = "Removed due to being outside target lat/long radii: %s"
    def real_filter(a):
        if ll_p is None:
            return False
        temp = (city.split(':')[0] for city in a.cities) 
        latlons = (t.split(',') for t in temp)
        for lat, lon in latlons:
            #Check all lat, lon pairs.  If any one of them is too far, return True
            # since all filters are exclusion filters (True means don't keep it)
            if not ll_dist((float(lat),float(lon)),ll_p) < CAPTURE_DIST:
                return True
        return False
    return (real_filter, log_mesg, [])

