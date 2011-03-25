from google.appengine.api import memcache
import datetime
from advertiser.models import ( Campaign,
                                AdGroup,
                                )
import logging

from budget.models import (BudgetSlicer,
                           TimesliceLog,
                           )
                        
"""
A service that determines if a campaign can be shown based upon the defined 
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well. 
"""

test_timeslice = 0
test_daily_budget = 0


def has_budget(campaign, cost):
    """ Returns True if the cost is less than the budget in the current slice """
    memcache_budget = _get_memcache(campaign)
    
    if memcache_budget is None:
        # If there is a cache miss, we fall back to the previous snapshot
        budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
        campaign_daily_budget = campaign.budget
    
        key = _make_campaign_ts_budget_key(campaign)    
        
        ts_init_budget = budget_slicer.previous_budget_snapshot
        if ts_init_budget is None:
            ts_init_budget = budget_slicer.timeslice_budget
            logging.warning("calculated: %s" % ts_init_budget)
        # Add the budget every time, only is actually added the first
        memcache.add(key, _to_memcache_int(ts_init_budget),namespace="budget")
        memcache_budget = _get_memcache(campaign)
    
    if memcache_budget >= cost:
        return True
    return False
    
def apply_expense(campaign, cost):
    """ Applies an expense to our memcache """
    key = _make_campaign_ts_budget_key(campaign)
    return memcache.decr(key, _to_memcache_int(cost), namespace="budget")
    # TODO: Check for rollunder in devappserver
    

def advance_timeslice(campaign):
    """ Adds a new timeslice's worth of budget and pulls the budget
    expenditures into the database. Executed once per timeslice."""
    budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
     
    # If cache miss, assume that no budget has been spent
    mem_budget = _get_budget(campaign)
    if mem_budget is None:
        # Use the snapshot from the beginning of this timeslice
        mem_budget = budget_slicer.previous_budget_snapshot 

    # Log budget as long as this is not the first time
    if budget_slicer.previous_budget_snapshot is not None:
        initial_memcache_budget = budget_slicer.previous_budget_snapshot
        final_memcache_budget = mem_budget
        log = TimesliceLog(budget_slicer=budget_slicer,
                           initial_memcache_budget=initial_memcache_budget,
                           final_memcache_budget=final_memcache_budget,
                           end_date=datetime.datetime.now()
                           )
        log.put()
    
    # Back up slicer in database.
    budget_slicer.previous_budget_snapshot = mem_budget + budget_slicer.timeslice_budget
    budget_slicer.put()
    
    # Update in memory
    key = _make_campaign_ts_budget_key(campaign)
    memcache.incr(key, _to_memcache_int(budget_slicer.timeslice_budget), namespace="budget")
    
        
def advance_all():
    campaigns = Campaign.all()
    # We use campaigns as an iterator
    for camp in campaigns:
        if camp.budget is not None:
            advance_timeslice(camp)   
            
def last_log(campaign):
    """Returns the most recently recorded log"""
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    return slicer.timeslice_logs.order("-end_date").get()
    
def log_generator_from_key(campaign_key):
    return log_generator(Campaign.get_by_key_name(campaign_key))
    
def log_generator(campaign):
    """Returns a generator function for the list of most recent logs"""
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    return slicer.timeslice_logs.order("-end_date")
            
            
################ HELPER FUNCTIONS ###################

def _make_campaign_ts_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'budget:%s'%(campaign.key())
  
def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def _from_memcache_int(value):
    value = float(value)
    return value/100000

def _get_memcache(campaign):
    """ Does a raw get from memcache """
    key = _make_campaign_ts_budget_key(campaign)
    return memcache.get(key, namespace="budget")
   
def _set_memcache(campaign, val):
    key = _make_campaign_ts_budget_key(campaign)
    memcache.set(key, _to_memcache_int(val), namespace="budget")


def _delete_memcache(campaign):
    key = _make_campaign_ts_budget_key(campaign)
    memcache.delete(key, namespace="budget")
  

def _get_budget(campaign):
    key = _make_campaign_ts_budget_key(campaign)
    # logging.warning( "key: %s" % key )
    value = memcache.get(key, namespace="budget")
    if value is None:
        return None
    else:
        return _from_memcache_int(value)

################ TESTING FUNCTIONS ###################

def _get_budget_from_key(campaign_key):
    campaign = Campaign.get(campaign_key)
    return _get_budget(campaign)

def _apply_if_able(campaign, cost):
    """ For testing purposes """
    success = has_budget(campaign, cost)
    if success:
        apply_expense(campaign, cost)
    return success


def _flush_cache_and_slicer(campaign):
    """ For testing. Deletes the slicer and all logs"""
    _delete_memcache(campaign)

    budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    # budget_slicer.previous_budget_snapshot = None
    
    for log in budget_slicer.timeslice_logs:
        log.delete()
    
    budget_slicer.delete()

def _flush_all():
    campaigns = Campaign.all()
    # We use campaigns as an iterator
    for camp in campaigns:
        if camp.budget is not None:
            logging.error("flushing: %s" % camp.name)
            _flush_cache_and_slicer(camp)