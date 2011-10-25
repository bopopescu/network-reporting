from datetime import datetime
import time
import math

SEC_PER_MIN = 60
MIN_PER_TS = 5
MIN_PER_DAY = 1440

TS_PER_DAY = MIN_PER_DAY / MIN_PER_TS
SEC_PER_TS = MIN_PER_TS * SEC_PER_MIN

TEST_SEC_PER_MIN = 60
TEST_MIN_PER_TS = 120
TEST_MIN_PER_DAY = 1440

TEST_TS_PER_DAY = TEST_MIN_PER_DAY / TEST_MIN_PER_TS
TEST_SEC_PER_TS = TEST_MIN_PER_TS * TEST_SEC_PER_MIN


BUDGET_UPDATE_STR = '%s:%s:%s:%s:%s:%s'

BUDGET_DTE_FMT = '%d-%m-%Y-%H-%M'

def get_curr_slice_num(curr_ts=None):
    """ Returns the current UTC Timeslice """
    if curr_ts is None:
        curr_ts = time.time()
    return int(math.floor(curr_ts/SEC_PER_TS))

def get_slice_from_datetime(dte, testing=False):
    """ Given a datetime obj, returns the UTC timeslice """
    dte_ts = time.mktime(dte.timetuple())
    if testing:
        return int(math.floor(dte_ts/TEST_SEC_PER_TS))
    else:
        return int(math.floor(dte_ts/SEC_PER_TS))

def get_datetime_from_slice(slice_num, testing = False):
    """ Given a UTC slice num, return the date """
    if testing:
        utc_ts = slice_num * TEST_SEC_PER_TS
    else:
        utc_ts = slice_num * SEC_PER_TS
    return datetime.fromtimestamp(utc_ts)


def build_budget_update_string(start=None, 
                               end = None, 
                               active = None,
                               delivery_type = None,
                               static_total = None, 
                               static_slice = None):
    if static_total is not None and static_slice is not None:
        # Should probs raise an error, I'm lazy
        return False
    start = start.strftime(BUDGET_DTE_FMT)
    try:
        end = end.strftime(BUDGET_DTE_FMT)
    except:
        end = None
    return BUDGET_UPDATE_STR % (start, end, active, delivery_type, static_total, static_slice)

def nonity(val):
    if val == 'None':
        return None
    else:
        return val

def parse_budget_update_string(update_str):
    """ Takes an update_budget string and turns it into a list of
    meaningful values """
    start, end, active, delivery, static_total, static_slice = map(nonity, update_str.split(':'))

    if start is not None:
        start = datetime.strptime(start, BUDGET_DTE_FMT)
    if end is not None:
        end = datetime.strptime(end, BUDGET_DTE_FMT)
    if static_total:
        static_total = float(static_total)
    if static_slice:
        static_slice = float(static_slice)
    return (start, end, active, delivery, static_total, static_slice)
