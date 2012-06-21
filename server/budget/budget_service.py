from __future__ import with_statement
import random
import logging
from datetime import datetime, timedelta, date

from google.appengine.api import memcache

from ad_server.debug_console import trace_logging

from advertiser.query_managers import AdGroupQueryManager
from budget.helpers import get_curr_slice_num, get_slice_from_datetime, get_datetime_from_slice
from budget.memcache_budget import (remaining_ts_budget,
                                    total_spent,
                                    braking_fraction,
                                    set_slice,
                                    memcache_get_slice,
                                    _make_budget_ts_key,
                                    _make_budget_spent_key,
                                    _make_budget_braking_key,
                                    _to_memcache_int,
                                    _from_memcache_int,
                                    )
from budget.models import BudgetSliceLog, BudgetSliceCounter, Budget
from budget.query_managers import BudgetQueryManager
from common.utils.tzinfo import Pacific, utc

"""
A service that determines if a campaign can be shown based upon the defined
budget for that campaign. If the budget_type is "evenly", a minute by minute
timeslice-budget is kept as well.
"""
ONE_DAY = timedelta(days = 1)

SUCCESSFUL_DELIV_PER = .95

def has_budget(budget, cost, today=None):
    trace_logging.warning("Checking Budget...")

    if budget is None:
        return False
 
    if not budget.is_active:
        trace_logging.warning('Budget is not active for slice: %s' % budget.curr_slice)
        return False

    if random.random() > braking_fraction(budget):
        trace_logging.warning("Braking says slllowww down (didn't pass random check)")
        return False

    memc_ts_budget = remaining_ts_budget(budget)
    trace_logging.warning("Memcache ts: %s" % memc_ts_budget)

    if memc_ts_budget < cost:
        logging.warning("You's too poor.  Trying to spend %s with a ts budget of %s" % (cost, memc_ts_budget))
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
    logs = _get_ts_logs_for_date_range(budget, start_date, end_date, testing)
    tot = 0.0
    for log in logs:
        if log and log.actual_spending:
            tot += log.actual_spending
    return tot

def _get_ts_logs_for_date_range(budget, start_date, end_date, testing=False):
    if isinstance(start_date, datetime):
        start_date = start_date.date()
    if isinstance(end_date, datetime):
        end_date = end_date.date()

    start_slice = get_slice_from_datetime(start_date, testing)
    end_slice = (get_slice_from_datetime(end_date + ONE_DAY, testing))
    keys = BudgetSliceLog.get_keys_for_slices(budget, xrange(start_slice, end_slice))
    logs = BudgetSliceLog.get(keys)
    return logs

def _get_daily_logs_for_date_range(budget, start_date, end_date, testing=False):
    daily_logs = []
    temp = start_date
    i = 0
    while temp <= end_date:
        if budget.is_active_for_date(temp):
            daily_log = dict(date = temp,
                             initial_daily_budget = budget.daily_budget,
                             spent_today = 0
                             )
            logs = _get_ts_logs_for_date_range(budget, temp, temp, testing)
            for log in logs:
                try:
                    daily_log['spent_today'] += log.actual_spending
                except:
                    pass
            daily_logs.append(daily_log)
        temp += ONE_DAY
    return daily_logs


def _get_spending_for_date(budget, date, testing=False):
    return get_spending_for_date_range(budget, date, date, testing)

def percent_delivered(budget):
    """ Get the % of the budget that has been delivered """
    if not budget:
        return None
    if budget.static_slice_budget and not budget.finite:
        spent_today = budget.spent_today
        if spent_today:
            return budget.daily_budget / (spent_today * 1.0)
        else:
            return 0.0

    total_budget = budget.total_budget
    if total_budget:
        # includes the memcache spending
        return total_spent(budget) / (total_budget * 1.0)
    else:
        logging.warning("OMG no total budget...? %s" % budget)
        return None

def get_pace(budget):
    try:
        return budget.last_slice_log.pace
    except:
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

def apply_expense(budget, cost, curr_slice=None, today = None):
    """ Subtract $$$ from the budget, add to total spent
    This will get cleaned up later """

    if budget and budget.is_active:

        ts_key = _make_budget_ts_key(budget)
        spent_key = _make_budget_spent_key(budget)

        memcache.decr(ts_key, _to_memcache_int(cost), namespace='budget')

        memcache.incr(spent_key, _to_memcache_int(cost), namespace='budget', initial_value = total_spent(budget))

def _mock_budget_advance(advance_to_datetime=None, testing=False):
    """ This simulates what the budget_advance Cron Job will do without
    all the fancy TQ's and other junk because screw that """

    slice_counter = BudgetSliceCounter.all().get()
    # If there is no global thing set, then set that shit
    if not slice_counter:
        # If no date is specified, start @ NOW
        if advance_to_datetime is None:
            advance_to_datetime = datetime.now()
        slice_num = get_slice_from_datetime(advance_to_datetime,testing)
        slice_counter = BudgetSliceCounter(slice_num = slice_num)
    else:
        # we're advancing, if a date is specified advance to that date
        if advance_to_datetime:
            slice_counter.slice_num = get_slice_from_datetime(advance_to_datetime,testing)
        # otherwise just go up by one
        else:
            slice_counter.slice_num += 1

    set_slice(slice_counter.slice_num)
    slice_counter.put()
    budgets = Budget.all().filter('active =', True).fetch(100)
    for budget in budgets:
        timeslice_advance(budget, testing=testing, advance_to_datetime=advance_to_datetime)
        budget.put()


def timeslice_advance(budget, testing=False, advance_to_datetime = None):
    """ Update the budget_obj to have the correct total_spent at the start of this TS
    Update the old slicelog to hvae the correct total_spent at the end of it's TS
    Save the current memcache snapshot in a new slicelog

    TIMESLICE ADVANCE IS THE GOD OF BUDGETS. THIS METHOD CREATES, DESTROYS, UPDATES, ETC. """

    # The memc TS is advanced before timeslice_advance is called by anyone.
    slice_num = memcache_get_slice()
    if advance_to_datetime is None:
        advance_to_datetime = get_datetime_from_slice(slice_num, budget.testing).replace(tzinfo = utc)

    if not budget:
        return

    last_log = budget.last_slice_log

    # no previous slice log, this budget hasn't been initialized
    if last_log is None:
        # No previous log, but it needs to be updated so update it.  Must do this first because 
        # it could affect things later down
        if budget.update:
            BudgetQueryManager.exec_update_budget(budget)
        # We're advancing to a slice that is exactly when or after the budget
        # shoudl be init'd
        if slice_num and slice_num >= budget.start_slice:
            _initialize_budget(budget, testing = testing, slice_num = slice_num, date = advance_to_datetime.date())

        # advancing to a date that is before we shoudl start
        elif slice_num:
            budget.curr_slice = slice_num
            if budget.day_tz == 'Pacific':
                advance_to_datetime = advance_to_datetime.astimezone(Pacific)
            budget.curr_date = advance_to_datetime.date()
            budget.put()
    else:
######################### ONLY DONE WHEN TESTING ########################
        # Budget is Init'd, but we're advancing more than a single TS.
        if slice_num is not None and testing:
            while budget.curr_slice != slice_num:
                last_log = budget.last_slice_log

                curr_total_spent = total_spent(budget)
                spent_this_ts = curr_total_spent - budget.total_spent

                budget.total_spent = curr_total_spent
                budget.put()

                _update_budgets(budget, slice_num, last_log, spent_this_timeslice = spent_this_ts, testing=testing)
######################### DONE WITH ONLY TESTING ########################
        else:
            # Due to situations beyond our control we're doing this
            curr_total_spent = max(total_spent(budget), budget.total_spent)
            spent_this_ts = curr_total_spent - budget.total_spent
            # And this.
            spent_this_ts = max(spent_this_ts, 0)

            budget.total_spent = curr_total_spent
            budget.put()

            _update_budgets(budget, slice_num, last_log, spent_this_timeslice = spent_this_ts, testing=testing)
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
    # If the day_tz is not set, then this is an old budget that
    # was made to run in the future, as such it hasn't been init'd,
    # so it can be init'd w/ the Pacific datetime without any problems
    if not testing and not budget.day_tz:
        budget.day_tz = 'Pacific'
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

    # Don't init budget to 0, init to total spent amt.  This is useful for migrations. Otherwise shit is fucked
    memcache.set(spent_key, _to_memcache_int(budget.total_spent), namespace = 'budget')
    memcache.set(ts_key, _to_memcache_int(new_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_log.prev_braking_fraction, namespace = 'budget')


def _update_slicelogs(budget, slice_num, last_log, new_braking, spent_this_timeslice):
    """ Sets the actual spending of the most recent TS and
        Sets the prev_total_spending, and
        prev_braking_fraction of the new slice """
    last_log.actual_spending = spent_this_timeslice
    last_log.put()
    new_log = BudgetSliceLog(budget = budget,
                             slice_num = slice_num,
                             desired_spending = budget.next_slice_budget,
                             prev_total_spending = budget.total_spent,
                             prev_braking_fraction = new_braking)
    new_log.put()
    if budget.curr_slice != new_log.slice_num:
        logging.warning("Ayyyeee tharr be problems around.  Budget curr slice: %s  Timeslice currslice: %s" % (budget.curr_slice, new_log.slice_num))
    return new_log


def _update_budgets(budget, slice_num, last_log, spent_this_timeslice=None, testing=False):
    """ Updates budget related objects
        Updates previous slicelog
        Creates current slicelog
        Updates spending and braking fraction in Memcache
        """
    # Slice_num is the slice_num specified by a global BudgetSliceCounter.
    # Keeps everyone on the same page :D
    budget.curr_slice = slice_num

    next_day = budget.curr_date + ONE_DAY
    next_day = datetime(next_day.year, next_day.month, next_day.day,0,0,0)
    # Add in more tz support if necessary
    if budget.day_tz == 'Pacific':
        next_day = next_day.replace(tzinfo = Pacific)
    elif budget.day_tz == 'UTC':
        next_day = next_day.replace(tzinfo = utc)
    else:
        next_day = next_day.replace(tzinfo = utc)

    # Advance the day counter if it makes sense to do so
    if budget.curr_slice >= get_slice_from_datetime(next_day.astimezone(utc), testing):
        budget.curr_date = next_day.date()
    budget.put()

    if budget.update:
        BudgetQueryManager.exec_update_budget(budget)

    ts_key = _make_budget_ts_key(budget)
    brake_key = _make_budget_braking_key(budget)

    desired_spend = last_log.desired_spending
    old_braking = braking_fraction(budget)
    if spent_this_timeslice == 0 and desired_spend == 0:
        new_braking = old_braking
    else:
        new_braking = calc_braking_fraction(desired_spend, spent_this_timeslice, old_braking)

    new_slice_log  = _update_slicelogs(budget, slice_num, last_log, new_braking, spent_this_timeslice)

    if not budget.is_active:
        # Budget isn't active, make sure vals are properly 0'd, continue
        memcache.set(ts_key, 0, namespace = 'budget')
        memcache.set(brake_key, 1.0, namespace = 'budget')
        return

    # Update memc with values from the new slice log (since it's the backup for MC anyway)

    logging.warning("New spending for slice: %s is %s" % (budget.curr_slice, new_slice_log.desired_spending))
    memcache.set(ts_key, _to_memcache_int(new_slice_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_slice_log.prev_braking_fraction, namespace = 'budget')

    return

def get_osi(budget):
    """ Returns True if the most recent completed TS spent ~95% of the desired total.

    Because OSI is a function of the last timeslice log, chaning budgets
    won't cause it to get all fucked up-like

        First TS that is run has no record, so return True in this case """
    last_complete_slice = budget.most_recent_slice_log

    if last_complete_slice is None:
        return True

    else:
        adgroup = AdGroupQueryManager().get_adgroups(campaign = budget.campaign.get())[0]

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
    return max(min(new_braking, 1.0), 0.01)
