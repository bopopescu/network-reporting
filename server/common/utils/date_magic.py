from datetime import datetime, time, date

DAYS_IN_MONTHS = (31,28,31,30,31,30,31,31,30,31,30,31)

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
    return (d, d-delta)
