from google.appengine.api import memcache

from datetime import datetime

"""
A service that determines if a campaign can be shown based upon the defined 
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well. 
"""


def timeslice_memcache_minute_key(adgroup_id,datetime):
    return 'timeslice:%s:%s'%(adgroup_id,datetime.strftime('%y%m%d%H%M'))
  
  
def to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def from_memcache_int(value):
    return float(value/100000)


def init_adgroup(adgroup_id, daily_dollar_budget, cost_per_event):
    self.adgroup_id = adgroup_id
    self.remaining_daily_budget = daily_dollar_budget/cost_per_event*(1 + fudge_factor)
    self.remaining_timeslices = timeslices
    self.counter = 0
    
    self._set_next_timeslice()


def _next_timeslice_budget(self):
        return (self.remaining_daily_budget / self.remaining_timeslices)
        
def _set_next_timeslice(self):
    rollover_budget = self._get_timeslice_budget()
    
    #set new timeslice name
    self.timeslice_name = str(self.adgroup_id) + ":" + str(self.counter)
    self.counter += 1
    
    budget = rollover_budget + self._next_timeslice_budget()
    memcache.add(self.timeslice_name, int(budget))
    
def _has_budget(self):
    if self._get_timeslice_budget() > 0:
        return True
    return False
    
def _get_timeslice_budget(self):
    try:
        return memcache.get(self.timeslice_name)
    except AttributeError:
        return 0
        

    
def process(campaign_id, bid):
    """ Return true if the adgroup's current timeslice has enough budget for a creative's bid """
    has_budget = has_budget()
    if has_budget:
        memcache.decr(timeslice_adgroup_key(campaign), to_memcache_int(bid))
    return has_budget
        
        