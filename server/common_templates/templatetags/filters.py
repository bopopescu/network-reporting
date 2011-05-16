import re
import time
from datetime import datetime
from django import template
import base64, binascii
from django.utils import simplejson as json
import logging

from country_codes import COUNTRY_CODE_DICT

register = template.Library()

@register.filter
def attrs(bound_field, attrs_json):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    parsed = json.loads(attrs_json)
    bound_field.add_attrs(attrs=parsed)
    return bound_field
  
@register.filter
def raw(bound_field):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    bound_field.TEMPLATE = 'raw_bound_field.html'
    return bound_field

@register.filter
def raw_required(bound_field):
    """
    Parses a json attrs object from template and passes them to the bound_field
    """
    bound_field.TEMPLATE = 'raw_bound_field_required.html'
    return bound_field

    
@register.filter
def label(bound_field, label):
    """
    Sets the label of a field
    """
    bound_field.add_label(label)
    return bound_field

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
        return "%1.2f%%" % ((value or 0) * 100)
    else:
        return "0.00%"
        
@register.filter
def percentage_rounded(value):
    if value:
        return "%1.0f%%" % ((value or 0) * 100)
    else:
        return "0%"        
  
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
        return "%d/%d" % (value.month, value.day)
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
def campaign_status(adgroup):
    d = datetime.now().date()
    if (adgroup.start_date is None or d > adgroup.start_date) and (adgroup.end_date is None or d < adgroup.end_date):
        if not adgroup.active:
            return "Paused"
        if adgroup.campaign.budget: 
            if adgroup.percent_delivered and adgroup.percent_delivered < 100.0:
                return "Running"
            elif adgroup.percent_delivered and adgroup.percent_delivered >= 100.0:
                return "Completed"
            else:
                # Eligible campaigns have 0% delivery.
                # They should only last a couple seconds before becoming running campaigns
                return "Eligible"
        else:
            return "Running"
    elif adgroup.end_date and d > adgroup.end_date:
        return "Expired"
    elif adgroup.start_date and d < adgroup.start_date:
        return "Scheduled"
    else:
        return "Unknown"
	
@register.filter
def all_user_dropdown(request,value=1000):
    from django.utils.safestring import mark_safe
    from account.models import Account
    from google.appengine.ext import db
    value = int(value)
    htmls = []
    accounts = Account.all().order("user").fetch(value)
    for account in accounts:
        if account.mpuser:
            htmls.append('<option value="%s">%s</option>'%(account.key(),account.mpuser.email))
    return mark_safe('\n'.join(htmls))

@register.filter
def binary_data(data):
    return "data:image/png;base64,%s" % binascii.b2a_base64(data)
    
@register.filter
def country_code_to_name(country_code):
    if country_code in COUNTRY_CODE_DICT:
        return COUNTRY_CODE_DICT.get(country_code)
    else:
        logging.warning("No country name for code: %s"%country_code)
        return None    
    