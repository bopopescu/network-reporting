import re
import time
from datetime import datetime
from django import template
import base64, binascii

register = template.Library()

def currency(value):
  if value:
    return "$%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
  else:
    return "$0.00"
    
def currency_no_symbol(value):
  if value:
    return "%s%s" % (withsep(int(value)), ("%0.2f" % value)[-3:])
  else:
    return "0.00"

def percentage(value):
  if value:
  	return "%1.1f%%" % ((value or 0) * 100)
  else:
	return "0.0%"	
  
def withsep(x):
  if x:
  	return re.sub(r'(\d{3})(?=\d)', r'\1,', str(x)[::-1])[::-1] 
  else:
	return "0"
  
def format_date(value):
  return value.strftime("%a, %b %d, %Y")
  
def truncate(value, arg):
  if len(value) > arg:
    return "%s..." % value[:(arg-3)]
  else:
    return value

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
  
register.filter(currency)
register.filter(currency_no_symbol)
register.filter(withsep)
register.filter(percentage)
register.filter(format_date)
register.filter(truncate)
register.filter(time_ago_in_words)
