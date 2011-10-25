from __future__ import with_statement
import random 
import logging
from datetime import datetime, timedelta

from google.appengine.api import memcache

from ad_server.debug_console import trace_logging
from advertiser.models import Campaign
from advertiser.query_managers import AdGroupQueryManager
from budget.helpers import get_curr_slice_num, get_slice_from_datetime
from budget.memcache_budget import (remaining_ts_budget,
                                    total_spent,
                                    braking_fraction,
                                    _make_budget_ts_key,
                                    _make_budget_spent_key,
                                    _make_budget_braking_key,
                                    _to_memcache_int,
                                    _from_memcache_int,
                                    )
from budget.models import BudgetSliceLog
from budget.query_managers import BudgetQueryManager

ONE_DAY = timedelta(days = 1)

SUCCESSFUL_DELIV_PER = .95



def has_budget(budget, cost, today=None):

    if budget is None:
        return False
    logging.warning("Start slice: %s  end slice: %s   curr slice: %s" % (budget.start_slice, budget.end_slice, budget.curr_slice))

    # I maintain that this is slightly fucked
    if not budget.is_active_for_timeslice(budget.curr_slice):
        trace_logging.warning('Budget is not active for slice: %s' % budget.curr_slice)
        logging.warning("Not active")
        return False

    if random.random() > braking_fraction(budget):
        trace_logging.warning("Braking says slllowww down (didn't pass random check)")
        return False

    memc_ts_budget = remaining_ts_budget(budget)
    trace_logging.warning("Memcache ts: %s" % memc_ts_budget)
    logging.warning("Has_budget Memcache ts: %s   cost: %s" % (memc_ts_budget, cost))

    if memc_ts_budget < cost:
        logging.warning("Bitch you's too poor.  Trying to spend %s with a ts budget of %s" % (cost, memc_ts_budget))
        return False

    return True

################## Used for testing #####################
def _delete_memcache(budget):
    keys = (_make_budget_ts_key(budget), _make_budget_spent_key(budget), _make_budget_braking_key(budget))

    for key in keys:
        memcache.delete(key, namespace = 'budget')

def _apply_if_able(budget, cost, today=None):
    success = has_budget(budget, cost, today)
    if success:
        apply_expense(budget, cost, today)
    return success
#########################################################

def get_spending_for_date_range(budget, start_date, end_date, testing=False):
    start_slice = get_slice_from_datetime(start_date.date(), testing)
    end_slice = (get_slice_from_datetime(end_date.date() + ONE_DAY, testing))
    #logging.warning("\n\nSpending for slice:%s to slice:%s\n\n" % (start_slice, end_slice))
    keys = BudgetSliceLog.get_keys_for_slices(budget, xrange(start_slice, end_slice))
    logs = BudgetSliceLog.get(keys)
    tot = 0.0
    for log in logs:
        if log and log.actual_spending:
            tot += log.actual_spending
    return tot

def _get_spending_for_date(budget, date, testing=False):
    return get_spending_for_date_range(budget, date, date, testing)

def percent_delivered(budget):
    if not budget:
        return None

    total_budget = budget.total_budget
    if total_budget:
        t_spent = total_spent(budget)
        logging.warning("Total budget: %s\nTotal Spent: %s" % (total_budget, t_spent))
        # includes the memcache spending
        return total_spent(budget) / (total_budget * 1.0)
    else:
        return None

def remaining_daily_budget(budget):
    """ Legacy for testing, also
    for $/day allatonce campaigns maybe """

    # if it's an allatonce with static total, just dump everything, so what's 
    # left for today is everything that hasn't been spent otherwise
    if budget.delivery_type == 'allatonce' and budget.static_total_budget:
        return budget.daily_budget - total_spent(budget)

    ts_spend = total_spent(budget) - budget.total_spent
    tot_spend_today = budget.spent_today + ts_spend
    return budget.daily_budget - tot_spend_today

def apply_expense(budget, cost, curr_slice=None):
    """ Subtract $$$ from the budget, add to total spent
    This will get cleaned up later """

    # I feel like this is redundant....
    if budget and budget.is_active_for_timeslice(budget.curr_slice):

        ts_key = _make_budget_ts_key(budget)
        spent_key = _make_budget_spent_key(budget)

        memcache.decr(ts_key, _to_memcache_int(cost), namespace='budget')

        memcache.incr(spent_key, _to_memcache_int(cost), namespace='budget', initial_value = total_spent(budget))

def timeslice_advance(budget, testing=False, advance_to_datetime = None):
    """ Update the budget_obj to have the correct total_spent at the start of this TS
    Update the old slicelog to hvae the correct total_spent at the end of it's TS
    Save the current memcache snapshot in a new slicelog

    TIMESLICE ADVANCE IS THE GOD OF BUDGETS. THIS METHOD CREATES, DESTROYS, UPDATES, ETC. """
    if not testing and advance_to_datetime is None:
        advance_to_datetime = datetime.now()
        slice_num = get_slice_from_datetime(advance_to_datetime, testing)
    elif testing and advance_to_datetime is None:
        slice_num = None
    else:
        slice_num = get_slice_from_datetime(advance_to_datetime, testing)


    if not budget:
        return

    last_log = budget.last_slice_log

    # no previous slice log, this budget hasn't been initialized
    if last_log is None:
        # We're advancing to a slice that is exactly when or after the budget
        # shoudl be init'd
        if slice_num and slice_num >= budget.start_slice:
            logging.warning("\n\nNo Last Log, initing budget")
            _initialize_budget(budget, testing = testing, slice_num = slice_num, date = advance_to_datetime.date())
        # advancing to a date that is before we shoudl start
        elif slice_num:
            logging.warning("\n\nNo Last Log, advancing to slice_num")
            budget.curr_slice = slice_num
            budget.curr_date = advance_to_datetime.date()
            budget.put()
        # budget has a curr slice
        elif budget.curr_slice:
            logging.warning("\n\nNo Last Log, advancing a slice")
            budget.curr_slice += 1
            budget.put()
    else:
######################### ONLY DONE WHEN TESTING ########################
        # Budget is Init'd, but we're advancing more than a single TS.  
        if slice_num is not None and testing:
            logging.warning("\n\nLast Log, mega-advancing")
            while budget.curr_slice != slice_num:
                last_log = budget.last_slice_log

                curr_total_spent = total_spent(budget)
                spent_this_ts = curr_total_spent - budget.total_spent

                budget.total_spent = curr_total_spent
                budget.put()


                _update_budgets(budget, last_log, spent_this_timeslice = spent_this_ts, testing=testing)
######################### DONE WITH ONLY TESTING ########################
        else:
            logging.warning("\n\nLast Log, default advancing")

            curr_total_spent = total_spent(budget)
            spent_this_ts = curr_total_spent - budget.total_spent

            budget.total_spent = curr_total_spent
            budget.put()

            _update_budgets(budget, last_log, spent_this_timeslice = spent_this_ts, testing=testing)
    return budget.curr_slice

def _initialize_budget(budget, testing = False, slice_num = None, date=None):
    """ Start this budget running!
        Create slicelog
        Update spending, braking in memc
    """
    if slice_num is None:
        slice_num = get_curr_slice_num()
    if date is None:
        date = datetime.now().date()

    if budget.start_slice > slice_num:
        # Don't init the budget if it shouldn't be init'd
        logging.warning("There is something wrong.  This campaign starts on slice %s, but initializing on slice: %s" % (budget.start_slice, slice_num))
        return 
    budget.curr_slice = slice_num
    budget.curr_date = date
    budget.put()

    new_log = BudgetSliceLog(budget = budget,
                             slice_num = slice_num,
                             desired_spending = budget.next_slice_budget,
                             prev_total_spending = budget.total_spent,
                             prev_braking_fraction = 1.0)

    new_log.put()
    ts_key = _make_budget_ts_key(budget)
    brake_key = _make_budget_braking_key(budget)
    spent_key = _make_budget_spent_key(budget)

    logging.warning("Setting spent to 0\nSetting ts budget to:%s\nSetting braking fraction to:%s" % (new_log.desired_spending, new_log.prev_braking_fraction))

    memcache.set(spent_key, 0, namespace = 'budget')
    memcache.set(ts_key, _to_memcache_int(new_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_log.prev_braking_fraction, namespace = 'budget')


def _update_slicelogs(budget, last_log, new_braking, spent_this_timeslice):
    """ Sets the actual spending of the most recent TS and
        Sets the prev_total_spending, and
        prev_braking_fraction of the new slice """

    last_log.actual_spending = spent_this_timeslice
    last_log.put()
    new_log = BudgetSliceLog(budget = budget,
                             slice_num = last_log.slice_num + 1,
                             desired_spending = budget.next_slice_budget,
                             prev_total_spending = budget.total_spent,
                             prev_braking_fraction = new_braking)
    new_log.put()
    if budget.curr_slice != new_log.slice_num:
        logging.warning("Ayyyeee tharr be problems around.  Budget curr slice: %s  Timeslice currslice: %s" % (budget.curr_slice, new_log.slice_num))
    return new_log


def _update_budgets(budget, last_log, spent_this_timeslice=None, testing=False):
    """ Updates budget related objects
        Updates previous slicelog
        Creates current slicelog
        Updates spending and braking fraction in Memcache
        """
    budget.curr_slice += 1
    next_day = budget.curr_date + ONE_DAY
    # Advance the day counter if it makes sense to do so
    if budget.curr_slice >= get_slice_from_datetime(next_day, testing):
        budget.curr_date = next_day
    budget.put()

    if budget.update:
        BudgetQueryManager.exec_update_budget(budget)

    ts_key = _make_budget_ts_key(budget)
    brake_key = _make_budget_braking_key(budget)

    desired_spend = last_log.desired_spending
    old_braking = braking_fraction(budget)
    if spent_this_timeslice == 0:
        new_braking = old_braking
    else:
        new_braking = calc_braking_fraction(desired_spend, spent_this_timeslice, old_braking)

    new_slice_log  = _update_slicelogs(budget, last_log, new_braking, spent_this_timeslice)

    if not budget.is_active:
        # Budget isn't active, make sure vals are properly 0'd, continue
        logging.warning("Zeroing TS, braking to 1.0, budget is inactive for it's current slice")
        memcache.set(ts_key, 0, namespace = 'budget')
        memcache.set(brake_key, 1.0, namespace = 'budget')
        return

    # Update memc with values from the new slice log (since it's the backup for MC anyway)

    #logging.warning("Setting ts budget to:%s\nSetting braking fraction to:%s" % (new_slice_log.desired_spending, new_slice_log.prev_braking_fraction))
    memcache.set(ts_key, _to_memcache_int(new_slice_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_slice_log.prev_braking_fraction, namespace = 'budget')

    return

def get_osi(budget):
    """ Returns True if the most recent completed TS spent ~95% of the desired total.

    Because OSI is a function of the last timeslice log, chaning budgets
    won't cause it to get all fucked up-like
    
        First TS that is run has no record, so return True in this case """
    last_complete_slice = budget.most_recent_slice_log
    logging.warning("Log %s" % last_complete_slice)
    
    if last_complete_slice is None:
        return True

    else:
        adgroup = AdGroupQueryManager().get_adgroups(campaign = budget.campaign.get())[0]
        logging.warning("Adgroup: %s\nAdGroup bid: %s\nLast des: %s" % (adgroup, adgroup.bid, last_complete_slice.desired_spending))

        if adgroup and last_complete_slice.desired_spending < adgroup.bid/1000:
            return True
        else:
            return last_complete_slice.osi

def calc_braking_fraction(desired_spend, actual_spend, prev_fraction):
    """ Given the desired spend, the actual spend, and the previous braking fraction
    compute the new braking fraction.  Basically, the current fraction delivers the
    proper amount, keep it, otherwise adjust it to be accurate """

    # prev braking rate is .5, we show this campaign 50% of the time that we actually can show it
    # so we get 1000 requests, but only show 500

    # if we overdeliver by 2x, actual will be 20 to desired 10, rate factor is 2
    # if we underdeliver by 2x, actual will be 5 to desired 10, rate factor of .5
    try:
        new_rate_factor = float(actual_spend)/desired_spend
    except:
        # 0 error, theoretically infinity, go to a large number
        new_rate_factor = 100.0

    # in the overdeliver case, we should've delivered 250 instead of 500, brake is now .25
    # which yields the correct behavior
    # in the underdeliver case we should've delivered 1000 instead of 500, brake is now 1
    try:
        new_braking = prev_fraction/new_rate_factor
    except:
        # div by 0 error, theoretically infinity, go to largest possible value (1)
        new_braking = 1.0

    # if the actual_spend and desired spend are fine, then the factor is ~1, so the divide is fine
    # dont' return a value >1
    return min(new_braking, 1.0)
