from google.appengine.api import memcache

import logging
from budget.models import BudgetSlicer

def remaining_daily_budget(campaign):
    """ Gets or inserts the remaining daily budget.
    This budget can increase past campaign.budget only
    if this is a finite campaign """
    key = _make_campaign_daily_budget_key(campaign)

    memcache_budget = memcache.get(key, namespace="budget")

    if memcache_budget is None:
        logging.error("Budget cache miss campaign with key: %s" % key)
        # If there is a cache miss, we fall back to the previous snapshot
        budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)

        key = _make_campaign_daily_budget_key(campaign)    

        daily_init_budget = campaign.budget-spent_today(campaign)

        memcache_budget = _to_memcache_int(daily_init_budget)
        memcache.add(key, memcache_budget, namespace="budget")
        
    return _from_memcache_int(memcache_budget)

def remaining_ts_budget(campaign):
    """ Gets or inserts the remaining timeslice budget """
    key = _make_campaign_ts_budget_key(campaign)

    memcache_budget = memcache.get(key, namespace="budget")

    if memcache_budget is None:
        logging.error("cache miss for campaign with key: %s" % key)
        # If there is a cache miss, we fall back to the previous snapshot
        budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
        
        key = _make_campaign_ts_budget_key(campaign) 
        
        spent_in_timeslice = spent_today(campaign)-budget_obj.spent_today
        remaining_timeslice = budget_obj.timeslice_budget-spent_in_timeslice
        
        memcache_budget = _to_memcache_int(remaining_timeslice)
        memcache.add(key, memcache_budget, namespace="budget")

    return _from_memcache_int(memcache_budget)        
    
def spent_today(campaign):
    """ Gets or inserts budget spent today"""
    key = _make_campaign_spent_today_key(campaign)
    memcache_spent = memcache.get(key, namespace="budget")
    if memcache_spent is None:
        logging.error("spending cache miss for campaign with key: %s" % key)
        budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
        spent = budget_obj.spent_today
        
        key = _make_campaign_spent_today_key(campaign)
        
        memcache_spent =_to_memcache_int(spent)
        memcache.add(key,memcache_spent, namespace="budget")
    
    return _from_memcache_int(memcache_spent)
    
def _from_memcache_int(value):
    value = float(value)
    return value/100000
    
def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(max(value,0)*100000)
    
def _make_campaign_ts_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'timeslice_budget:%s'%(campaign.key())

def _make_campaign_daily_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'daily_budget:%s'%(campaign.key())

def _make_campaign_spent_today_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'spent_today:%s'%(campaign.key())