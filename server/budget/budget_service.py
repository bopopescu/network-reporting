import random

from datetime import datetime

from ad_server.debug_console import trace_logging
from advertiser.models import Campaign
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



def has_budget(budget, cost, today=None):
    slice_num = get_curr_slice_num()
    #if today is None:
    #    today = pac_today()

    if budget is None:
        return False

    if not budget.is_active_for_timeslice(slice_num):
        return False

    if random.random() > braking_fraction(budget):
        return False

    memc_ts_budget = remaining_ts_budget(budget)
    trace_logging.warning("Memcache ts: %s" % memc_ts_budget)

    if memc_ts_budget < cost:
        return False

    return True

################## Used for testing #####################
def _apply_if_able(budget, cost, today=None):
    success = has_budget(budget, cost, today)
    if success:
        apply_expense(budget, cost, today)

    return success
#########################################################

def apply_expense(budget, cost, today=None):
    """ Subtract $$$ from the budget, add to total spent
    This will get cleaned up later """

    # I feel like this is redundant....
    if budget and budget.is_active_for_timeslice(budget.curr_slice):

        ts_key = _make_budget_ts_key(budget)
        spent_key = _make_budget_spent_key(budget)

        memcache.decr(ts_key, _to_memcache_int(cost), namespace='budget')
        memcache.incr(spent_key, _to_memcache_int(cost), namespace='budget', initial_value = total_spent(budget))

def timeslice_advance(budget, testing=False, advance_to_slice=None):
    """ Update the budget_obj to have the correct total_spent at the start of this TS
    Update the old slicelog to hvae the correct total_spent at the end of it's TS
    Save the current memcache snapshot in a new slicelog

    TIMESLICE ADVANCE IS THE GOD OF BUDGETS. THIS METHOD CREATES, DESTROYS, UPDATES, ETC. """
    if not budget:
        return

    last_log = budget.last_slice_log

    # no previous slice log, this budget hasn't been initialized
    if last_log is None:
        _initialize_budget(budget)

    else:
        key = _make_budget_ts_key(budget)

        curr_total_spent = total_spent(budget)
        spent_this_ts = curr_total_spent - budget.total_spent

        budget.curr_slice += 1
        budget.total_spent = curr_total_spent
        budget.put()

        _update_budgets(budget, last_log, spent_this_timeslice = spent_this_ts)

def _initialize_budget(budget, slice_num = None):
    """ Start this budget running! 
        Create slicelog
        Update spending, braking in memc
    """
    if slice_num is None:
        slice_num = get_curr_slice_num()

    if budget.start_slice != slice_num:
        logging.warning("There is something wrong.  This campaign starts on slice %s, but initializing on slice: %s" % (budget.start_slice, slice_num))
    budget.curr_slice = slice_num
    budget.put()

    new_log = BudgetSliceLog(budget = budget,
                             slice_num = slice_num,
                             desired_spending = budget.next_slice_budget,
                             prev_total_spending = budget.total_spent,
                             prev_braking_fraction = 1.0)

    new_log.put()
    ts_key = _make_budget_ts_key(budget)
    brake_key = _make_budget_braking_key(budget)

    memcache.set(ts_key, _to_memcache_int(new_slice_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_slice_log.prev_braking_fraction, namespace = 'budget')


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
    return new_slice_log
    

def _update_budgets(budget, last_log, spent_this_timeslice=None):
    """ Updates budget related objects
        Updates previous slicelog
        Creates current slicelog
        Updates spending and braking fraction in Memcache
        """

    desired_spend = last_log.desired_spending
    old_braking = braking_fraction(budget)
    new_braking = calc_braking_fraction(desired_spend, spent_this_timeslice, old_braking)

    new_slice_log  = _update_slicelogs(budget, last_log, spent_this_ts)

    # Update memc with values from the new slice log (since it's the backup for MC anyway)
    ts_key = _make_budget_ts_key(budget)
    brake_key = _make_budget_braking_key(budget)

    memcache.set(ts_key, _to_memcache_int(new_slice_log.desired_spending), namespace = 'budget')
    memcache.set(brake_key, new_slice_log.prev_braking_fraction, namespace = 'budget')

    return


def calc_braking_fraction(desired_spend, actual_spend, prev_fraction):
    """ Given the desired spend, the actual spend, and the previous braking fraction
    compute the new braking fraction.  Basically, the current fraction delivers the
    proper amount, keep it, otherwise adjust it to be accurate """

    # prev braking rate is .5, we show this campaign 50% of the time that we actually can show it
    # so we get 1000 requests, but only show 500

    # if we overdeliver by 2x, actual will be 20 to desired 10, rate factor is 2
    # if we underdeliver by 2x, actual will be 5 to desired 10, rate factor of .5
    new_rate_factor = float(actual_spend)/desired_spend

    # in the overdeliver case, we should've delivered 250 instead of 500, brake is now .25
    # which yields the correct behavior
    # in the underdeliver case we should've delivered 1000 instead of 500, brake is now 1
    new_braking = prev_fraction/new_rate_factor

    # if the actual_spend and desired spend are fine, then the factor is ~1, so the divide is fine
    # dont' return a value >1
    return min(new_braking, 1.0)
