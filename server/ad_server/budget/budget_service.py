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

test_timeslice = 0
test_daily_budget = 0

def timeslice_campaign_key(campaign_id,timeslice):
    """Returns a key based upon the campaign_id and the current time"""
    return 'timeslice:%s:%s'%(campaign_id,timeslice)
  
def to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def from_memcache_int(value):
    value = float(value)
    return value/100000

def previous_timeslice():
    return current_timeslice() - 1;

def current_timeslice():
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

def current_timeslice_initial_budget(campaign_id):
    rollover_key = timeslice_campaign_key(campaign_id,previous_timeslice())
    rollover_val = memcache.get(rollover_key, namespace="budget") or 0.0
    rollover_budget = from_memcache_int(rollover_val)
    
    initial_budget = daily_budget(campaign_id) / TIMESLICES
    
    budget = rollover_budget + initial_budget
    return budget
    

def daily_budget(campaign_id):
    if not TEST_MODE:
        "look up in db with fudge factor"
    else:
        return test_daily_budget

def has_budget(key, bid):
    if from_memcache_int(memcache.get(key, namespace="budget")) >= bid:
        return True
    return False
    
def get_timeslice_budget(campaign_id):
    key = timeslice_campaign_key(campaign_id,current_timeslice())
    return from_memcache_int(memcache.get(key, namespace="budget"))
 
    
def process(campaign_id, bid):
    """ Return true if the campaign's current timeslice budget has
    enough money for a creative's bid """
    key = timeslice_campaign_key(campaign_id,current_timeslice())
    
    # Add the budget every time, only is added the first
    ts_budget = current_timeslice_initial_budget(campaign_id)
    memcache.add(key, to_memcache_int(ts_budget),namespace="budget")
    
    can_show = has_budget(key, bid)
    if can_show:
        memcache.decr(key, to_memcache_int(bid), namespace="budget")
    return can_show
        
        