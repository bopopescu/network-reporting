from google.appengine.api import memcache
import datetime
from advertiser.models import ( Campaign,
                                )
import logging

from budget.models import (Budget,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           NoSpendingForIncompleteLogError,
                           )
                           
from budget.query_managers import BudgetSliceLogQueryManager
from budget.tzinfo import Pacific

"""
A service that determines if a campaign can be shown based upon the defined 
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well. 
"""

test_timeslice = 0
test_daily_budget = 0

def pac_today():
    return datetime.datetime.now(tz=Pacific).date()
    
def pac_dt():
    return datetime.datetime.now(tz=Pacific)
    
def has_budget(campaign, cost, today=pac_today()):
    """ Returns True if the cost is less than the budget in the current timeslice.
        Campaigns that have not yet begun always return false"""
    
    if not campaign.budget:
        return True
    
    if campaign.start_date and today < campaign.start_date:
        return False
    
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
        spent_today(campaign) #Assures memcache spent today will not be None
        
        ts_key = _make_campaign_ts_budget_key(campaign)
        daily_key = _make_campaign_daily_budget_key(campaign)
        spent_key = _make_campaign_spent_today_key(campaign)
        
        memcache.decr(ts_key, _to_memcache_int(cost), namespace="budget")
        memcache.decr(daily_key, _to_memcache_int(cost), namespace="budget")
        memcache.incr(spent_key, _to_memcache_int(cost), namespace="budget")


def timeslice_advance(campaign):
    """ Adds a new timeslice's worth of budget and pulls the budget
    expenditures into the database. Executed once per timeslice."""
    if not campaign.budget:
        return
        
    budget_slicer = Budget.get_or_insert_for_campaign(campaign)
    # Update timeslice budget in memory
    key = _make_campaign_ts_budget_key(campaign)
    budget_slicer.advance_timeslice()

    spent_this_timeslice = spent_today(campaign)-budget_slicer.spent_today
    budget_slicer.spent_today = spent_today(campaign)

    budget_slicer.put()
    
    _backup_budgets(campaign, spent_this_timeslice=spent_this_timeslice)
    
    memcache.set(key, _to_memcache_int(budget_slicer.timeslice_budget), namespace="budget")
            
def daily_advance(campaign, new_date=pac_today()):
    """ Adds a new timeslice's worth of daily budget, logs the daily spending and initializes a new log
    Executed once daily just after midnight. Will not increment a campaign that is not active.
    """
    today = new_date
    if not campaign.budget:
        return
    
    budget_slicer = Budget.get_or_insert_for_campaign(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)
    daily_spending = spent_today(campaign)
    
    yesterday = today - datetime.timedelta(days=1)
    
    # Attach the remaining_daily_budget to yesterday if it was initialized
    try:
        yesterday_log = budget_slicer.daily_logs.filter("date =", yesterday).get()
        yesterday_log.remaining_daily_budget = rem_daily_budget
        yesterday_log.spending = daily_spending
        yesterday_log.put()
    except AttributeError:
        # If the log was not initialized, then this is a new campaign and
        # we build a new one.
        yesterday_log = BudgetDailyLog(budget_slicer=budget_slicer,
                          initial_daily_budget=campaign.budget,
                          remaining_daily_budget = rem_daily_budget,
                          spending = daily_spending,
                          date=yesterday,
                          )
        yesterday_log.put()
    
        
    budget_slicer.spent_in_campaign += daily_spending
    budget_slicer.put()
    
    spent_key = _make_campaign_spent_today_key(campaign)    
    memcache.set(spent_key, _to_memcache_int(0), namespace="budget")
    
    if campaign.budget_type == "full_campaign":
        campaign.budget = _redistribute_budget(campaign,new_date)
        budget_slicer.campaign=campaign
    
    new_initial_budget = campaign.budget
    
    daily_budget_key = _make_campaign_daily_budget_key(campaign)
    memcache.set(daily_budget_key, _to_memcache_int(new_initial_budget), namespace="budget")
    
    daily_log = BudgetDailyLog(budget_slicer=budget_slicer,
                      initial_daily_budget=new_initial_budget,
                      date=today,
                      )
    daily_log.put()
    
    spent_this_timeslice = budget_slicer.spent_today-daily_spending
    # We reset the timeslice snapshot to 0.0
    
    budget_slicer.timeslice_snapshot = 0.0
    
    budget_slicer.spent_today = 0.
    
    ts_budget_key = _make_campaign_ts_budget_key(campaign)
    memcache.set(ts_budget_key, _to_memcache_int(0), namespace="budget")
    
    budget_slicer.put()
    campaign.put()
    
    # We backup immediately in order to set a new daily snapshot
    _backup_budgets(campaign, spent_this_timeslice=spent_this_timeslice)
    
  
def percent_delivered(campaign, today=pac_today()):
    """ Gives the percent of the budget that has been delivered.
    Gives the percent of the daily budget that has been delivered so far today """
    if not (campaign.budget and campaign.finite) and not campaign.budget_type == "full_campaign":
        return None
        
    if campaign.budget_type == "daily":
        # The number of days in the campaign, inclusive
        num_days = (campaign.end_date - campaign.start_date).days + 1
        total_budget = campaign.budget * num_days
    else:
        total_budget = campaign.full_budget
     
    # logging.error("percent del date: %s" % today)
    # logging.error("total: %s" % total_budget)
    # logging.error("remaining: %s" % remaining_daily_budget(campaign))
    
    budget_slicer = Budget.get_or_insert_for_campaign(campaign)
    
    return ((budget_slicer.spent_in_campaign+spent_today(campaign)) / total_budget) * 100

def remaining_daily_budget(campaign):
    """ Gets or inserts the remaining daily budget.
    This budget can increase past campaign.budget only
    if this is a finite campaign """
    key = _make_campaign_daily_budget_key(campaign)

    memcache_budget = memcache.get(key, namespace="budget")

    if memcache_budget is None:
        logging.error("Budget cache miss campaign with key: %s" % key)
        # If there is a cache miss, we fall back to the previous snapshot
        budget_slicer = Budget.get_or_insert_for_campaign(campaign)

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
        budget_slicer = Budget.get_or_insert_for_campaign(campaign)
        campaign_daily_budget = campaign.budget

        key = _make_campaign_ts_budget_key(campaign)    

        
        ts_init_budget = budget_slicer.timeslice_snapshot

        if ts_init_budget is None:
            # If no timeslice has been initialized, start with a full batch
            ts_init_budget = campaign.timeslice_budget

        memcache_budget = _to_memcache_int(ts_init_budget)
        memcache.add(key, memcache_budget, namespace="budget")

    return _from_memcache_int(memcache_budget)        
    
def spent_today(campaign):
    """ Gets or inserts budget spent today"""
    key = _make_campaign_spent_today_key(campaign)
    memcache_spent = memcache.get(key, namespace="budget")
    if memcache_spent is None:
        logging.error("spending cache miss for campaign with key: %s" % key)
        budget_slicer = Budget.get_or_insert_for_campaign(campaign)
        spent = budget_slicer.spent_today
        
        key = _make_campaign_spent_today_key(campaign)
        
        memcache_spent =_to_memcache_int(spent)
        memcache.add(key,memcache_spent, namespace="budget")
    
    return _from_memcache_int(memcache_spent)
    
def get_spending_for_date_range(campaign, start_date, end_date, today=pac_today()):
    """ Gets the spending for a date range (inclusive). Uses realtime budget information for
        campaigns that are currently in progress. """
    daily_logs = _get_daily_logs_for_date_range(campaign, start_date, end_date, today=today)
    
    # logging.warning("dlogs: %s" % daily_logs.get())
    # logging.warning("today: %s" % today)
    # logging.warning("sdate: %s" % campaign.start_date)
    # If there are no results, check if today is the start date
    if not daily_logs.get():
        if today == campaign.start_date:
            return spent_today(campaign)
    
    total_spending = 0.0
    for log in daily_logs:
        if log.spending is not None:
            total_spending += log.spending
        else:
            total_spending += spent_today(campaign)
        # try:
        #     total_spending += log.spending
        # except NoSpendingForIncompleteLogError:
        #     # If there is a log that is incomplete, we assume that it is today's log
        #     log_spending = log.initial_daily_budget - remaining_daily_budget(campaign)
        #     total_spending += log_spending
    
    return total_spending

def update_budget(campaign, dt = pac_dt(), save_campaign=True):
    if campaign.budget_type:
        budget_slicer = Budget.get_or_insert_for_campaign(campaign)
        if campaign.budget_type == "full_campaign":
            campaign.budget = _redistribute_budget(campaign, dt.date())
            budget_slicer.campaign = campaign
            
        if campaign.is_active_for_date(dt) and (campaign.budget_type == "full_campaign" or campaign.budget):
            spent = spent_today(campaign)
            daily_budget_key = _make_campaign_daily_budget_key(campaign)
            ts_key = _make_campaign_ts_budget_key(campaign)
            
            budget_slicer.daily_snapshot = campaign.budget-spent
            
            if campaign.budget-spent < 0:
                memcache.set(daily_budget_key, _to_memcache_int(0), namespace="budget")
            else:
                memcache.set(daily_budget_key, _to_memcache_int(budget_slicer.daily_snapshot), namespace="budget")

            if campaign.budget_strategy == "evenly":
                budget_slicer.set_timeslice(dt.hour*60*60+dt.minute*60+dt.second)
                budget_slicer.timeslice_snapshot = budget_slicer.timeslice_budget
                spent_in_timeslice = spent_today(campaign)-budget_slicer.spent_today
                remaining_timeslice = budget_slicer.timeslice_budget-spent_in_timeslice
                if remaining_timeslice < 0:
                    memcache.set(ts_key, _to_memcache_int(0), namespace="budget")
                else:
                    memcache.set(ts_key, _to_memcache_int(remaining_timeslice), namespace="budget")
        budget_slicer.put()
        if save_campaign:
            campaign.put()
                    
def get_osi(campaign):
    """ Returns True if the most recent completed timeslice spent within 95% of the 
        desired total. """  
    last_budgetslice = BudgetSliceLogQueryManager().get_most_recent(campaign)
    successful_delivery = .95
    
    try:
        return last_budgetslice.actual_spending >= last_budgetslice.desired_spending*successful_delivery 
    except AttributeError:
        # If there is no log built yet, we return True
        return True
                
################ HELPER FUNCTIONS ###################


def _get_daily_logs_for_date_range(campaign, start_date, end_date, today=pac_today()):
    slicer = Budget.get_or_insert_for_campaign(campaign)
    daily_logs = slicer.daily_logs.filter("date >=", start_date).filter("date <=", end_date)
    return daily_logs
    
def _get_ts_logs_for_date(campaign, date):
    slicer = Budget.get_or_insert_for_campaign(campaign)
    min_dt = datetime.datetime.combine(date,datetime.time.min)
    max_dt = datetime.datetime.combine(date,datetime.time.max)
    ts_logs = slicer.timeslice_logs.filter("end_date >=", min_dt).filter("end_date <=", max_dt)
    return ts_logs

def _make_campaign_ts_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'timeslice_budget:%s'%(campaign.key())

def _make_campaign_daily_budget_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'daily_budget:%s'%(campaign.key())
    
def _make_campaign_spent_today_key(campaign):
    """Returns a unique budget key based upon campaign.key """
    return 'spent_today:%s'%(campaign.key())

def _redistribute_budget(campaign,new_date):
    #Recalculate daily budget for full campaigns in response to changes in end_date or full_budget
    budget_slicer = Budget.get_or_insert_for_campaign(campaign)
    if (new_date-datetime.timedelta(days=1) - campaign.start_date).days >= 0:
        new_budget = (campaign.full_budget-budget_slicer.spent_in_campaign)/((campaign.end_date-new_date).days+1)
        if new_budget < 0:
            return 0.
        else:
            return new_budget
    else:
        return campaign.full_budget/((campaign.end_date-campaign.start_date).days+1)
        

def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value*100000)
    
def _from_memcache_int(value):
    value = float(value)
    return value/100000
    
def _set_memcache(campaign, val):
    key = _make_campaign_ts_budget_key(campaign)
    memcache.set(key, _to_memcache_int(val), namespace="budget")

def _backup_budgets(campaign, spent_this_timeslice = None):
    """ Makes a timeslice budget summary, also includes the remaining daily budget"""
    budget_slicer = Budget.get_or_insert_for_campaign(campaign)

    mem_budget = remaining_ts_budget(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)

    # Make BudgetSliceLog
    initial_memcache_budget = budget_slicer.timeslice_snapshot
    final_memcache_budget = mem_budget
    
    log = BudgetSliceLog(budget_slicer=budget_slicer,
                      initial_memcache_budget=initial_memcache_budget,
                      final_memcache_budget=final_memcache_budget,
                      remaining_daily_budget=rem_daily_budget,
                      end_date=datetime.datetime.now(),
                      desired_spending=budget_slicer.timeslice_budget,
                      actual_spending=spent_this_timeslice
                      )
    log.put()
    
    # Back up slicer with snapshots in database.

    budget_slicer.timeslice_snapshot = budget_slicer.timeslice_budget
    budget_slicer.daily_snapshot = rem_daily_budget
    budget_slicer.put()


################ TESTING FUNCTIONS ###################

def _get_log_for_date(campaign, date):
    
    slicer = Budget.get_or_insert_for_campaign(campaign)
    daily_log = slicer.daily_logs.filter("date =", date).get()
    
    return daily_log

def _fudge_spending_for_date(campaign, date, spending):
    """ Fudges the amount that was spent, for testing or fixing bugs """
    slicer = Budget.get_or_insert_for_campaign(campaign)
    daily_log = _get_log_for_date(campaign, date)
    if not daily_log:
        daily_log = BudgetDailyLog(budget_slicer=slicer,
                          initial_daily_budget=float(spending),
                          remaining_daily_budget = 0.0,
                          date=date)
    daily_log.put()


def _get_spending_for_date(campaign, date):
    
    slicer = Budget.get_or_insert_for_campaign(campaign)
    daily_log = slicer.daily_logs.filter("date =", date).get()
    
    return daily_log.spending


def _apply_if_able(campaign, cost, today=pac_today()):
    """ For testing purposes """
    success = has_budget(campaign, cost, today=today)
    if success:
        apply_expense(campaign, cost)
    return success


def _flush_cache_and_slicer(campaign):
    """ For testing. Deletes the slicer and all logs"""
    _delete_memcache(campaign)

    budget_slicer = Budget.get_or_insert_for_campaign(campaign)
    
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