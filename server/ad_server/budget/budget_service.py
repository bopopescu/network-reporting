from google.appengine.api import memcache

from datetime import datetime


def timeslice_memcache_minute_key(adgroup_id,datetime):
  return 'timeslice:%s:%s'%(adgroup_id,datetime.strftime('%y%m%d%H%M'))

class BudgetService(object):
    """
    A service that determines if a campaign can be shown based upon the defined 
    budget for that campaign. If the budget_type is "evenly", a minute by minute
    timeslice-budget is kept as well. 
    """

    def __init__(self, adgroup_id, daily_dollar_budget, cost_per_event, timeslices=1440, fudge_factor=0.0, test_mode=False):
        self.adgroup_id = adgroup_id
        self.remaining_daily_slots = daily_dollar_budget/cost_per_event*(1 + fudge_factor)
        self.remaining_timeslices = timeslices
        self.counter = 0
        
        self._set_next_timeslice()

  
    def _next_timeslice_slots(self):
            return (self.remaining_daily_slots / self.remaining_timeslices)
            
    def _set_next_timeslice(self):
        rollover_slots = self._get_timeslice_slots()
        
        #set new timeslice name
        self.timeslice_name = str(self.adgroup_id) + ":" + str(self.counter)
        self.counter += 1
        
        slots = rollover_slots + self._next_timeslice_slots()
        memcache.add(self.timeslice_name, int(slots))
        
    def _has_slots(self):
        if self._get_timeslice_slots() > 0:
            return True
        return False
        
    def _get_timeslice_slots(self):
        try:
            return memcache.get(self.timeslice_name)
        except AttributeError:
            return 0
        
    def process(self):
        """ Return true if the current timeslice has a slot for a creative """
        has_slots = self._has_slots()
        if has_slots:
            memcache.decr(self.timeslice_name)
        return has_slots
            
        