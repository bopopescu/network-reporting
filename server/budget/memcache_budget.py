from google.appengine.api import memcache

import logging
from budget.models import BudgetSliceCounter


BUDGET_SLICE_KEY = 'Th3Budg3tSlic3K3y'

def set_slice(slice_num):
    """ sets the memc value for the current timeslice """
    memcache.set(BUDGET_SLICE_KEY, slice_num, namespace='budget')

def memcache_get_slice():
    """ Gets the memc value for the current timeslice """
    slice_num = memcache.get(BUDGET_SLICE_KEY, namespace = 'budget')
    if slice_num is None:
        slice_counter = BudgetSliceCounter.all().get()
        slice_num = slice_counter.slice_num
        set_slice(slice_num)

    return slice_num

def remaining_ts_budget(budget):
    """ Either gets the remaining from memc, or constructs it from
    the budget for this TS and the
    (total currently spent in MC less the amount spent total previously)
    """
    key = _make_budget_ts_key(budget)

    memc_budget = memcache.get(key, namespace='budget')
    if memc_budget is None:
        logging.info("Budget cache miss budget with key: %s" % key)

        key = _make_budget_ts_key(budget)

        # MC has missed due to either brand new TS or actual MC miss
        spent_this_slice = total_spent(budget) - budget.total_spent
        ts_budget = budget.next_slice_budget - spent_this_slice

        memc_budget = _to_memcache_int(ts_budget)
        memcache.add(key, memc_budget, namespace='budget')

    return _from_memcache_int(memc_budget)


def total_spent(budget):

    key = _make_budget_spent_key(budget)

    memc_total = memcache.get(key, namespace='budget')

    if memc_total is None:
        logging.info("Spending cache miss for budget with key: %s" % key)

        total = budget.total_spent
        if total is None:
            return 0
        memc_total = _to_memcache_int(total)
        memcache.add(key, memc_total, namespace='budget')

    return _from_memcache_int(memc_total)


def braking_fraction(budget):
    key = _make_budget_braking_key(budget)
    braking = memcache.get(key, namespace = 'budget')
    if braking:
        # Return the memc braking value if it's there
        return braking
    else:
        last_log = budget.last_slice_log
        # otherwise try to get it from a previous timeslice
        if last_log:
            return last_log.prev_braking_fraction
        else:
            return 1.0


def _from_memcache_int(value):
    """ Removes the 10^5 mult factor """
    value = float(value)
    value = value/(10 ** 5)
    return value

def _to_memcache_int(value):
    """multiplies by 10^5 and converts to an int"""
    return int(value * (10 ** 5))

def _make_budget_ts_key(budget):
    return 'ts_budget:%s' % str(budget.key())

def _make_budget_spent_key(budget):
    return 'total_spent:%s' % str(budget.key())

def _make_budget_braking_key(budget):
    return 'braking:%s' % str(budget.key())
