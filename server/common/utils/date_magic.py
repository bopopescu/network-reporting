from datetime import datetime, time, date, timedelta
from common.utils.timezones import Pacific_tzinfo

DAYS_IN_MONTHS = (31,28,31,30,31,30,31,31,30,31,30,31)

def start_next_month(d):
    if d.month == 12:
        return date(d.year+1, 1, 1)
    else:
        return date(d.year, d.month+1, 1)

def start_next_week(d):
    new_d = d
    delta = timedelta(days=1)
    if new_d.weekday() == 0:
        new_d += delta
    while new_d.weekday() != 0:
        new_d += delta
    return new_d

def tomorrow(d):
    return d + timedelta(days=1)

def start_next_quarter(d):
    quarter = (d.month-1) / 3
    if quarter == 0:
        return date(d.year, 4, 1)
    elif quarter == 1:
        return date(d.year, 7, 1)
    elif quarter == 2:
        return date(d.year, 10, 1)
    elif quarter == 3:
        return date(d.year + 1, 1, 1)

def get_next_day(interv, d=None):
    if d is None:
        d = datetime.now().date()
    if interv == 'daily':
        return tomorrow(d)
    elif interv == 'weekly':
        return start_next_week(d)
    elif interv == 'monthly':
        return start_next_month(d)
    elif interv == 'quarterly':
        return start_next_quarter(d)
    return None

def this_month(d):
    return (start_this_month(d), d)

def last_month(d):
    return (start_last_month(d), end_last_month(d))

def start_this_month(d):
    return date(d.year, d.month, 1)

def start_last_month(d):
    new_d = start_this_month(d)
    if new_d.month == 1:
        return date(new_d.year-1, 12, 1)
    else:
        return date(new_d.year, new_d.month-1, 1)

def end_last_month(d):
    new_d = start_last_month(d)
    day = DAYS_IN_MONTHS[new_d.month-1]
    if new_d.month == 2 and is_leap_year(new_d):
        day += 1
    return date(new_d.year, new_d.month, day)

def this_week(d):
    return (start_this_week(d), d)

def last_week(d):
    return (start_last_week(d), end_last_week(d))

def start_this_week(d):
    new_d = d
    delta = timedelta(days = 1)
    while new_d.weekday() > 0:
        new_d -= delta
    return d

def start_last_week(d):
    new_d = start_this_week(d)
    delta = timedelta(days=7)
    return new_d - delta

def end_last_week(d):
    new_d = start_this_week(d)
    delta = timedelta(days=1)
    return new_d - delta

def is_leap_year(d):
    year = d.year
    if year % 400 == 0:
        return True
    elif year % 100 == 0:
        return False
    elif year % 4 == 0:
        return True
    else:
        return False

def last_seven(d):
    delta = timedelta(days=7)
    return (d-delta, d)

# start and end are inclusive
def gen_days(start, end, hours=False):
    """
    Makes a list of date objects for each day in between start and end, inclusive.
    `start` and `end` are datetime.date objects.
    """
    diff = (end - start).days + 1
    days = [start + timedelta(days=i) for i in range(0, diff)]
    if hours:
        return reduce(lambda x,y: x+y, get_hours(days))
    else:
        return days

def gen_days_for_range(start, date_range):
    """
    Take a start date and a date range.

    Return a list of days, [datetime.date,...], objects for the given range.
    """
    if start:
        return [start + timedelta(days=x) for x in range(0,
              date_range)]
    else:
        days = gen_last_days(date_range, 1)
    return days

def gen_last_days(date_range=7, omit=0):
    """
    Set omit=1 to eliminates partial days contributing to totals or appearing
    in graphs
    """
    today = datetime.now(Pacific_tzinfo()).date().today() - timedelta(days=omit)
    days = [today - timedelta(days=x) for x in range(0, date_range)]
    days.reverse()
    return days

def gen_date_range(n, hours=False):
    today = date.today()
    n_day = today - timedelta(n)
    return gen_days(n_day, today, hours)

def get_hours(days, hpd = 24):
    '''Turn a list of days into a list of lists where
    each list is a list of date_hours where the date
    ranges over the given days and the hour is held constant'''
    ret = []
    for hour in range(hpd):
        ent = []
        for day in days:
            date = day.day
            yr = day.year
            mo = day.month
            ent.append(datetime(yr,mo,date,hour))
        ret.append(ent)
    return ret

def get_days(days):
    '''turn a list of days into a list of lists where
    each list is a single day'''
    return map(lambda x: [x], days)

def get_weeks(days):
    '''turn a list of days into a list of lists where
    each list is a week'''
    #XXX Make sure this is the case!!!
    #assuming days[0] is first day and days[-1] is last day
    weeks = []
    week = []
    for day in days:
        if day.weekday() == 0:
            if len(week) > 0:
                weeks.append(week)
            week = [day]
        else:
            week.append(day)
    if len(week) > 0:
        weeks.append(week)
    return weeks

def get_months(days):
    '''turn a list of days into a list of lists where
    each list is a list of days that make up that month.
    This is done instead of using the fact that StatsModel
    rollups are done for the month because if I want to do a
    day, week, or hour breakdown for a given month it's easier
    if we start with a list of days than a single day denoting the month'''
    months = []
    this_month = -1
    month = []
    for day in days:
        if this_month != day.month:
            #first time through
            if this_month == -1:
                this_month = day.month
            #been here before, add old data and start a new month
            else:
                months.append(month)
            month = []
        month.append(day)
    if len(month) > 0:
        months.append(month)
    return months

MO = 'month'
WEEK = 'week'
DAY = 'day'
HOUR = 'hour'

def date_name(val, dim):
    if dim == MO:
        name = val.strftime('%m-%Y')
    elif dim == WEEK:
        #I think this is the right order...
        dte1, dte2 = val
        name = dte1.strftime('%m-%d') + ' - ' + dte2.strftime('%m-%d-%Y')
    elif dim == DAY:
        name = val.strftime('%m-%d-%Y')
    elif dim == HOUR:
        name = val.strftime('%H:00')
    else:
        name = 'Impossible State'
    return name


def date_key(time, dim):
    if dim == MO:
        return time.strftime('%y%m')
    elif dim == WEEK:
        return time.strftime('%y%m%W')
    elif dim == DAY:
        return time.strftime('%y%m%d')
    elif dim == HOUR:
        return time.strftime('%y%m%d%H')
