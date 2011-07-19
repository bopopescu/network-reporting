from google.appengine.api import memcache
from ad_server.debug_console import trace_logging
import datetime
from advertiser.models import ( Campaign,
                                )
import logging
import random

from budget.models import (BudgetSlicer,
                           BudgetSliceLog,
                           BudgetDailyLog,
                           NoSpendingForIncompleteLogError,
                           )
                           
from budget.query_managers import BudgetSliceLogQueryManager
from budget.tzinfo import Pacific

from budget.memcache_budget import (spent_today,
                                    remaining_daily_budget,
                                    remaining_ts_budget
                                    )
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
    
    if campaign.budget is None:
        # TEMP: If past July 15th with no errors, remove this
        if campaign.full_budget:
            trace_logging.error("full_budget without budget in campaign: %s" % campaign.key())
         # TEMP: If past July 15th with no errors, remove this
         
        return True
    
    trace_logging.warning("active: %s"%campaign.is_active_for_date(today))
    if not campaign.is_active_for_date(today):
        return False

    
    
    # For now we comment this out, to get a sense of the fraction behavior
    
    # # Determine if we need to slow down to prevent race conditions
    # # Only let through things less than the braking fraction
    # if random.random() > braking_fraction(campaign):
    #     return False
    
    memcache_daily_budget = remaining_daily_budget(campaign)
    trace_logging.warning("memcache: %s"%memcache_daily_budget)
    
    if memcache_daily_budget < cost:
        return False
    
    if campaign.budget_strategy == "evenly":
        memcache_ts_budget = remaining_ts_budget(campaign)
        trace_logging.warning("memcache ts: %s"%memcache_ts_budget)
        if memcache_ts_budget < cost:
            return False
            
    # All budgets are met:
    return True
    
def apply_expense(campaign, cost, today=pac_today()):
    """ Applies an expense to our memcache """
    if campaign and campaign.budget and campaign.is_active_for_date(today):
        ts_key = _make_campaign_ts_budget_key(campaign)
        daily_key = _make_campaign_daily_budget_key(campaign)
        spent_key = _make_campaign_spent_today_key(campaign)
    
        memcache.decr(ts_key, _to_memcache_int(cost), namespace="budget")
        memcache.decr(daily_key, _to_memcache_int(cost), namespace="budget")
        memcache.incr(spent_key, _to_memcache_int(cost), namespace="budget", initial_value=spent_today(campaign))

def timeslice_advance(campaign, testing=False):
    """ Adds a new timeslice's worth of budget and pulls the budget
    expenditures into the database. Executed once per timeslice."""
    if not campaign.budget:
        return
    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
    # Update timeslice budget in memory
    key = _make_campaign_ts_budget_key(campaign)
    if testing:
        budget_obj.advance_timeslice()
    else:
        dt = pac_dt()
        budget_obj.set_timeslice(dt.hour*60*60+dt.minute*60+dt.second)

    spent_this_timeslice = spent_today(campaign)-budget_obj.spent_today
    budget_obj.spent_today = spent_today(campaign)

    budget_obj.put()
    
    _backup_budgets(campaign, spent_this_timeslice=spent_this_timeslice)

    memcache.set(key, _to_memcache_int(budget_obj.timeslice_budget), namespace="budget")
            
def daily_advance(campaign, new_date=pac_today()):
    """ Adds a new timeslice's worth of daily budget, logs the daily spending and initializes a new log
    Executed once daily just after midnight. Will not increment a campaign that is not active.
    """
    today = new_date
    if not campaign.budget:
        return
    
    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)
    daily_spending = spent_today(campaign)
    
    yesterday = today - datetime.timedelta(days=1)
    
    # Attach the remaining_daily_budget to yesterday if it was initialized
    try:
        yesterday_log = budget_obj.daily_logs.filter("date =", yesterday).get()
        yesterday_log.remaining_daily_budget = rem_daily_budget
        yesterday_log.actual_spending = daily_spending
        yesterday_log.put()
    except AttributeError:
        # If the log was not initialized, then this is a new campaign and
        # we build a new one.
        yesterday_log = BudgetDailyLog(budget_obj=budget_obj,
                          initial_daily_budget=campaign.budget,
                          remaining_daily_budget = rem_daily_budget,
                          actual_spending = daily_spending,
                          date=yesterday,
                          )
        yesterday_log.put()
    
        
    budget_obj.spent_in_campaign += daily_spending
    budget_obj.put()
    
    spent_key = _make_campaign_spent_today_key(campaign)    
    memcache.set(spent_key, _to_memcache_int(0), namespace="budget")
    
    if campaign.budget_type == "full_campaign":
        campaign.budget = _redistribute_budget(campaign,new_date)
        budget_obj.campaign=campaign
    
    new_initial_budget = campaign.budget
    
    daily_budget_key = _make_campaign_daily_budget_key(campaign)
    memcache.set(daily_budget_key, _to_memcache_int(new_initial_budget), namespace="budget")
    
    daily_log = BudgetDailyLog(budget_obj=budget_obj,
                      initial_daily_budget=new_initial_budget,
                      date=today,
                      )
    daily_log.put()
        
    budget_obj.spent_today = 0.
    
    ts_budget_key = _make_campaign_ts_budget_key(campaign)
    memcache.set(ts_budget_key, _to_memcache_int(0), namespace="budget")
    
    budget_obj.put()
    campaign.put() 
  
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
    
    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
    
    return ((budget_obj.spent_in_campaign+spent_today(campaign)) / total_budget) * 100
    
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
        try:
            total_spending += log.spending
        except NoSpendingForIncompleteLogError:
            total_spending += spent_today(campaign)
    
    return total_spending

def update_budget(campaign, dt = pac_dt(), save_campaign=True):
    """ Update budget is called whenever a campaign is created or saved. 
        It sets a new daily budget as well as fixing the outdated values
        in memcache. """
    
    if campaign.budget_type and (campaign.budget_type == "full_campaign" or campaign.budget):
        budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
        if campaign.budget_type == "full_campaign":
            campaign.budget = _redistribute_budget(campaign, dt.date())
            budget_obj.campaign = campaign
            
        if campaign.is_active_for_date(dt.date()):
            spent = spent_today(campaign)
            daily_budget_key = _make_campaign_daily_budget_key(campaign)
            ts_key = _make_campaign_ts_budget_key(campaign)
                        
            memcache.set(daily_budget_key, _to_memcache_int(campaign.budget-spent), namespace="budget")

            budget_obj.set_timeslice(dt.hour*60*60+dt.minute*60+dt.second)
            
            if campaign.budget_strategy == "evenly":
                spent_in_timeslice = spent_today(campaign)-budget_obj.spent_today
                remaining_timeslice = budget_obj.timeslice_budget-spent_in_timeslice
                memcache.set(ts_key, _to_memcache_int(remaining_timeslice), namespace="budget")
        budget_obj.put()
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
                
################ BUDGET BRAKING ###################                
                
def calc_braking_fraction(desired_spending, actual_spending, prev_fraction):
    """ Looks at the previous minute, if we overdelivered by 15 percent or more,
        we reduce the fraction by half. If we ever underdeliver, we double it """
    
    if actual_spending > desired_spending * 1.15:
        new_fraction = prev_fraction * 0.5
    
    elif actual_spending < desired_spending * 0.95:
        # Use more machines if underdelivering. Never go above 1.0
        new_fraction = min(prev_fraction * 2.0, 1.0)
    
    else:
        new_fraction = prev_fraction
        
    return new_fraction


def braking_fraction(campaign):
    """ Looks up the budget braking fraction in memcache. 
        1.00 means that we let through all traffic. 
        0.25 means we only let through one quearter. """
    key = _make_braking_fraction_key(campaign)
    return memcache.get(key, namespace="budget") or 1.0 # If nothing is in memcache try on 100%
            
def _make_braking_fraction_key(campaign):
    return 'braking_fraction:%s'%(campaign.key())    
                
################ HELPER FUNCTIONS ###################


def _get_daily_logs_for_date_range(campaign, start_date, end_date, today=pac_today()):
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    daily_logs = slicer.daily_logs.filter("date >=", start_date).filter("date <=", end_date)
    return daily_logs
    
def _get_ts_logs_for_date(campaign, date):
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
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
    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
    if (new_date-datetime.timedelta(days=1) - campaign.start_date).days >= 0:
        new_budget = (campaign.full_budget-budget_obj.spent_in_campaign)/((campaign.end_date-new_date).days+1)
        if new_budget < 0:
            return 0.
        else:
            return new_budget
    else:
        return campaign.full_budget/((campaign.end_date-campaign.start_date).days+1)
        

def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(max(value,0)*100000)
    
def _from_memcache_int(value):
    value = float(value)
    return value/100000
    
def _set_memcache(campaign, val):
    key = _make_campaign_ts_budget_key(campaign)
    memcache.set(key, _to_memcache_int(val), namespace="budget")

def _backup_budgets(campaign, spent_this_timeslice = None):
    """ Makes a timeslice budget summary, also includes the remaining daily budget"""
    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)

    mem_budget = remaining_ts_budget(campaign)
    rem_daily_budget = remaining_daily_budget(campaign)

    # Make BudgetSliceLog
    desired_spending = budget_obj.timeslice_budget
    
    last_log = budget_obj.timeslice_logs.order("-end_date").get()
    
    if last_log:
        last_log.remaining_daily_budget = rem_daily_budget
        last_log.actual_spending = spent_this_timeslice
        last_log.put()
        
        # If we had a previoius log, we can calculate the braking fraction too
        old_braking_fraction = braking_fraction(campaign)

        new_braking_fraction = calc_braking_fraction(last_log.desired_spending,
                                                     spent_this_timeslice,
                                                     old_braking_fraction)

        key = _make_braking_fraction_key(campaign)
        memcache.set(key, new_braking_fraction, namespace="budget")
    
    
    new_log = BudgetSliceLog(budget_obj=budget_obj,
                             desired_spending=desired_spending,
                             end_date=pac_dt())
    new_log.put()
    

    

################ TESTING FUNCTIONS ###################

def _get_log_for_date(campaign, date):
    
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    daily_log = slicer.daily_logs.filter("date =", date).get()
    
    return daily_log

def _fudge_spending_for_date(campaign, date, spending):
    """ Fudges the amount that was spent, for testing or fixing bugs """
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    daily_log = _get_log_for_date(campaign, date)
    if not daily_log:
        daily_log = BudgetDailyLog(budget_obj=slicer,
                          initial_daily_budget=float(spending),
                          remaining_daily_budget = 0.0,
                          date=date)
    daily_log.put()


def _get_spending_for_date(campaign, date):
    
    slicer = BudgetSlicer.get_or_insert_for_campaign(campaign)
    daily_log = slicer.daily_logs.filter("date =", date).get()
    
    return daily_log.spending


def _apply_if_able(campaign, cost, today=pac_today()):
    """ For testing purposes """
    success = has_budget(campaign, cost, today=today)
    if success:
        apply_expense(campaign, cost, today=today)
    return success


def _flush_cache_and_slicer(campaign):
    """ For testing. Deletes the slicer and all logs"""
    _delete_memcache(campaign)

    budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
    
    for log in budget_obj.timeslice_logs:
        log.delete()

    for log in budget_obj.daily_logs:
         log.delete()
    
    budget_obj.delete()

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
    
    key = _make_campaign_spent_today_key(campaign)
    memcache.delete(key, namespace="budget")

def _advance_all(testing=False):
    campaigns = Campaign.all()
    # We use campaigns as an iterator
    for camp in campaigns:
        if camp.budget is not None:
            timeslice_advance(camp, testing=testing)