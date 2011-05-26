from google.appengine.api import memcache
import datetime
from advertiser.models import ( Campaign,
                                AdGroup,
                                )
import logging

from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog
                           )

"""
A service that determines if a campaign can be shown based upon the defined 
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well. 
"""

test_timeslice = 0
test_daily_budget = 0


def has_budget(campaign, cost):
    """ Returns True if the cost is less than the budget in the current timeslice """
    
    if not campaign.budget:
        return True
    
    memcache_daily_budget = remaining_daily_budget(campaign)
    
    if memcache_daily_budget < cost:
        return False
    
    if campaign.budget_strategy == "evenly":
        memcache_ts_budget = remaining_ts_budget(campaign)
    
        if memcache_ts_budget < cost:
            return False
            
    # All budgets are met:
    return True
    
    
def apply_expense(campaign, cost):
    """ Applies an expense to our memcache """
    if campaign is not None:
        ts_key = _make_campaign_ts_budget_key(campaign)
        daily_key = _make_campaign_daily_budget_key(campaign)
    
        memcache.decr(ts_key, _to_memcache_int(cost), namespace="budget")
        memcache.decr(daily_key, _to_memcache_int(cost), namespace="budget")

def timeslice_advance(campaign):
    """ Adds a new timeslice's worth of budget and pulls the budget
    expenditures into the database. Executed once per timeslice."""
    if not campaign.budget:
        return
        
    _backup_budgets(campaign)
    
    budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    # Update timeslice budget in memory
    key = _make_campaign_ts_budget_key(campaign)
    memcache.incr(key, _to_memcache_int(budget_slicer.timeslice_budget), namespace="budget")
            
def daily_advance(campaign, date=None):
    """ Adds a new timeslice's worth of daily budget, Executed once daily at midnight."""
    if not campaign.budget:
        return
        
    key = _make_campaign_daily_budget_key(campaign)
    
    budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)
    
    # Since we execute at midnight, 2 hours ago should get the right day
    date = date or (datetime.datetime.now() - datetime.timedelta(hours=2)).date()
    daily_log = BudgetDailyLog(budget_slicer=budget_slicer,
                      remaining_daily_budget=rem_daily_budget,
                      end_datetime=datetime.datetime.now(),
                      date=date,
                      )
    daily_log.put()
        
    if campaign.finite:
        summed_budget = rem_daily_budget + campaign.budget
        memcache.set(key, _to_memcache_int(summed_budget), namespace="budget")
    else:
        memcache.set(key, _to_memcache_int(campaign.budget), namespace="budget")
    
    # We backup immediately in order to set a new daily snapshot
    _backup_budgets(campaign)
    
        
def last_log(campaign):
    """Returns the most recently recorded log"""
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    return slicer.timeslice_logs.order("-end_date").get()
    
def log_generator(campaign):
    """Returns a generator function for the list of most recent logs"""
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    return slicer.timeslice_logs.order("-end_date")
     
    
def percent_delivered(campaign):
    """ Gives the percent of the budget that has been delivered.
    Gives the percent of the daily budget that has been delivered so far today """
    if not (campaign.budget and campaign.finite):
        return None
        
    # The number of days in the campaign, inclusive
    num_days = (campaign.end_date - campaign.start_date).days + 1
    logging.warning(num_days)
    total_budget = campaign.budget * num_days
        
    logging.error("total: %s" % total_budget)
    logging.error("remaining: %s" % remaining_daily_budget(campaign))
    
    total_spending = total_budget - remaining_daily_budget(campaign)
    
    return (total_spending / total_budget) * 100

    
def remaining_daily_budget(campaign):
    """ Gets or inserts the remaining daily budget.
    This budget can increase past campaign.budget only
    if this is a finite campaign """
    key = _make_campaign_daily_budget_key(campaign)

    memcache_budget = memcache.get(key, namespace="budget")

    if memcache_budget is None:
        logging.error("cache miss for campaign with key: %s" % key)
        # If there is a cache miss, we fall back to the previous snapshot
        budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
        campaign_daily_budget = campaign.budget

        key = _make_campaign_daily_budget_key(campaign)    

        daily_init_budget = budget_slicer.daily_snapshot

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
        budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
        campaign_daily_budget = campaign.budget

        key = _make_campaign_ts_budget_key(campaign)    

        
        ts_init_budget = budget_slicer.timeslice_snapshot

        if ts_init_budget is None:
            # If no timeslice has been initialized, start with a full batch
            ts_init_budget = campaign.timeslice_budget

        memcache_budget = _to_memcache_int(ts_init_budget)
        memcache.add(key, memcache_budget, namespace="budget")

    return _from_memcache_int(memcache_budget)        
    
    
def get_spending_for_date_range(campaign, start_date, end_date):
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    
    # daily_logs = slicer.daily_logs
    # for log in daily_logs:
    #     logging.error("log date: %s spending: %s" % ( log.date, log.spending))
    
    daily_logs = slicer.daily_logs.filter("date >=", start_date).filter("date <=", end_date)
    
    for log in daily_logs:
        logging.error("log spending: " + str(log.spending))
    
    return sum([log.spending for log in daily_logs])
    
################ HELPER FUNCTIONS ###################

def _make_campaign_ts_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'timeslice_budget:%s'%(campaign.key())

def _make_campaign_daily_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'daily_budget:%s'%(campaign.key())
  
def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def _from_memcache_int(value):
    value = float(value)
    return value/100000
    
def _set_memcache(campaign, val):
    key = _make_campaign_ts_budget_key(campaign)
    memcache.set(key, _to_memcache_int(val), namespace="budget")

def _backup_budgets(campaign):
    budget_slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)

    mem_budget = remaining_ts_budget(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)

    # Make BudgetSliceLog
    initial_memcache_budget = budget_slicer.timeslice_snapshot
    final_memcache_budget = mem_budget

    log = BudgetSliceLog(budget_slicer=budget_slicer,
                      initial_memcache_budget=initial_memcache_budget,
                      final_memcache_budget=final_memcache_budget,
                      remaining_daily_budget=rem_daily_budget,
                      end_date=datetime.datetime.now()
                      )
    log.put()
    
    # Back up slicer with snapshots in database.
    budget_slicer.timeslice_snapshot = mem_budget + budget_slicer.timeslice_budget
    budget_slicer.daily_snapshot = rem_daily_budget
    budget_slicer.put()

def _recent_daily_logs(campaign, max_days=14):
    """ Returns a list of recent daily logs sorted by date"""
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    return slicer.daily_logs.order("-end_datetime").fetch(max_days)
################ TESTING FUNCTIONS ###################

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
    
    for log in budget_slicer.timeslice_logs:
        log.delete()

    for log in budget_slicer.daily_logs:
         log.delete()
    
    budget_slicer.delete()

def _flush_all():
    campaigns = Campaign.all()
    # We use campaigns as an iterator
    for camp in campaigns:
        if camp.budget is not None:
            logging.error("flushing: %s" % camp.name)
            _flush_cache_and_slicer(camp)

def _delete_memcache(campaign):
    """ To simulate cache failure on both campaign and daily """
    key = _make_campaign_ts_budget_key(campaign)
    memcache.delete(key, namespace="budget")

    key = _make_campaign_daily_budget_key(campaign)
    memcache.delete(key, namespace="budget")

def _advance_all():
    campaigns = Campaign.all()
    # We use campaigns as an iterator
    for camp in campaigns:
        if camp.budget is not None:
            timeslice_advance(camp)