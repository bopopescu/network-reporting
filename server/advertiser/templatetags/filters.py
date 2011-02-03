import re
import time
from datetime import datetime
from django import template
import base64, binascii

register = template.Library()

@register.filter
def currency(value):
    if value:
        return "$%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
    else:
        return "$0.00"
    
@register.filter
def currency_no_symbol(value):
    if value:
        return "%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
    else:
        return "0.00"

@register.filter
def percentage(value):
    if value:
        return "%1.1f%%" % ((value or 0) * 100)
    else:
        return "0.0%"	
  
@register.filter
def withsep(x):
    if x:
        return re.sub(r'(\d{3})(?=\d)', r'\1,', str(x)[::-1])[::-1] 
    else:
        return "0"
  
@register.filter
def format_date(value):
    if value:
        return value.strftime("%a, %b %d, %Y")
    else:
        return ""

@register.filter
def format_date_compact(value):
    if value:
        return value.strftime("%m/%d")
    else:
        return ""
  
@register.filter
def truncate(value, arg):
    if len(value) > arg:
        return "%s..." % value[:(arg-3)]
    else:
        return value

@register.filter
def time_ago_in_words(value):
    if value:
        if type(value) == str or type(value) == unicode:
            value = datetime(*time.strptime(value, "%a %b %d %H:%M:%S +0000 %Y")[0:5])

        d = datetime.now() - value
        if d.days < 1:
            if d.seconds < 60:
                return "less than a minute"
            elif d.seconds < 120:
                return "about a minute"
            elif d.seconds < (60 * 60):
                return "%d minutes" % (d.seconds / 60)
            elif d.seconds < (2 * 60 * 60):
                return "about an hour"
            elif d.seconds < (24 * 60 * 60):
                return "%d hours" % (d.seconds / 60 / 60)
            elif d.days < 2:
                return "one day"
            else:
                return "%d days" % (d.days)

@register.filter
def campaign_status(c):
    d = datetime.now()
    if (c.start_date is None or d > c.start_date) and (c.end_date is None or d < c.end_date):
        if c.budget: 
            if c.stats.revenue >= c.budget:
                return "Delivered"
            elif c.stats.impression_count > 0:
                return "In-flight, %d%%" % (c.stats.revenue / float(c.budget))
            else:
                return "Eligible"
        else:
            return "In-flight"
    elif end_date and d > c.end_date:
        return "Expired"
    elif start_date and d < c.start_date:
        return "Scheduled"
    else:
        return "Unknown"
	
@register.filter
def all_user_dropdown(request,value=200):
    from django.utils.safestring import mark_safe
    from account.models import Account
    from google.appengine.ext import db
    value = int(value)
    htmls = []
    for account in Account.all().order("user").fetch(value):
        htmls.append('<option value="%s">%s</option>'%(account.key().name(),account.user.email()))
    return mark_safe('\n'.join(htmls))

@register.filter
def binary_data(data):
    return "data:image/png;base64,%s" % binascii.b2a_base64(data)