from google.appengine.api import memcache
import datetime

"""
A service that determines if a campaign can be shown based upon the defined 
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well. 
"""

TIMESLICES = 1440 #we use a default timeslice of one minute
TEST_MODE = False
SECONDS_PER_DAY = 86400
FUDGE_FACTOR = 0.1

test_timeslice = 0
test_daily_budget = 0

def make_timeslice_campaign_key(campaign_id,timeslice):
    """Returns a key based upon the campaign_id and the current time"""
    return 'timeslice:%s:%s'%(campaign_id,timeslice)
  
def to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def from_memcache_int(value):
    value = float(value)
    return value/100000

def get_previous_timeslice():
    return get_current_timeslice() - 1;

def get_current_timeslice():
    """Returns the current timeslice, has test mode"""
    if not TEST_MODE:
        origin = datetime.datetime.combine(datetime.date.today(),
                                           datetime.time.min)
        now = datetime.datetime.now()
        seconds_elapsed = (now-origin).seconds
        # return seconds_elapsed/seconds_per_day*timeslices
        return int(seconds_elapsed*TIMESLICES/SECONDS_PER_DAY)
    else:
        return test_timeslice

def get_current_timeslice_initial_budget(campaign_id, campaign_daily_budget):
    rollover_key = make_timeslice_campaign_key(campaign_id,get_previous_timeslice())
    rollover_val = memcache.get(rollover_key, namespace="budget") or 0.0
    rollover_budget = from_memcache_int(rollover_val)
    
    initial_budget = campaign_daily_budget * (1 + FUDGE_FACTOR) / TIMESLICES
    
    budget = rollover_budget + initial_budget
    return budget
    
def has_budget(key, bid):
    if from_memcache_int(memcache.get(key, namespace="budget")) >= bid:
        return True
    return False
    
def get_timeslice_budget(campaign_id):
    key = make_timeslice_campaign_key(campaign_id,get_current_timeslice())
    return from_memcache_int(memcache.get(key, namespace="budget"))
 
    
def process(campaign_id, bid, campaign_daily_budget):
    """ Return true if the campaign's current timeslice budget has
    enough money for a creative's bid """
    key = make_timeslice_campaign_key(campaign_id,get_current_timeslice())
    
    # Add the budget every time, only is added the first
    ts_budget = get_current_timeslice_initial_budget(campaign_id, campaign_daily_budget)
    memcache.add(key, to_memcache_int(ts_budget),namespace="budget")
    
    can_show = has_budget(key, bid)
    if can_show:
        memcache.decr(key, to_memcache_int(bid), namespace="budget")
    return can_show
        
        