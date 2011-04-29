from datetime import datetime, time, date, timedelta

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
    return (d-delta, d)

def gen_days(start, end):
    dt = timedelta(days=1)
    temp = start
    days = [temp]
    while temp != end:
        temp = temp + dt
        days.append(temp)
    return days

def get_hours(days):
    '''Turn a list of days into a list of lists where
    each list is a list of date_hours where the date
    ranges over the given days and the hour is held constant'''
    ret = []
    for hour in range(24):
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

def date_name(day, dim):
    if dim == MO:
        name = val[0].strftime('%B, %Y')
    elif dim == WEEK:
        #I think this is the right order...
        name = val[0].strftime('%b %d') + ' - ' + val[-1].strftime('%b %d, %Y')
    elif dim == DAY:
        name = val[0].strftime('%b %d, %Y')
    elif dim == HOUR:
        name = val[0].strftime('%I:%M %p')
    else:
        name = 'Impossible State'
    return name
