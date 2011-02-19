import logging, os, re, datetime, hashlib

from urllib import urlencode

from google.appengine.api import users, images
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm

from publisher.models import Site, Account, App
from reporting.models import SiteStats

@login_required
def admin_switch_user(request,*args,**kwargs):
  params = request.POST or request.GET
  url = request.META["HTTP_REFERER"]
  # redirect where the request came from
  response = HttpResponseRedirect(url)
  # drop a cookie of the email is the admin user is trying to impersonate
  if users.is_current_user_admin():
    user_key_name = params.get('user_key',None)
    set_cookie = False
    if user_key_name:
      account = Account.get_by_key_name(user_key_name)
      if account:
        response.set_cookie('account_impersonation',params.get('user_key'))
        set_cookie = True
    if not set_cookie:
      response.delete_cookie('account_impersonation')    
  return response
  
@login_required
def dashboard(request, *args, **kwargs):
  start_date = datetime.date.today() - datetime.timedelta(days=14)
  stats = SiteStats.gql("where date > :1 and owner = null order by date desc", start_date).fetch(1000)
  
  # calculate unique active Site and Account
  # plus accumulate total impression and click counts
  unique_placements = {}
  unique_accounts = {}
  totals = {}
  
  # go and do it
  for s in stats:
    try:
      if s.site and not s.owner:
        # add this site stats to the total for the day
        a = totals.get(str(s.date)) or SiteStats(date=s.date)
        totals[str(s.date)] = a + s
    
        # add a hash key for the site key and account key to calculate uniques
        unique_accounts[s.site.account.key()] = s.site.account
        
        # ad unit stats
        stats_agg = unique_placements.get(s.site.key())
        if stats_agg:
          stats_agg = stats_agg + s
        else:
          unique_placements[s.site.key()] = s
        
    except Exception, e:
      logging.debug(e)
    
  # organize daily stats
  total_stats = totals.values()
  total_stats.sort(lambda x,y: cmp(x.date,y.date))
  
  # make a graph
  url = "http://chart.apis.google.com/chart?cht=lc&chs=800x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
     ','.join(map(lambda x: str(x.request_count), total_stats)), 
     max(map(lambda x: x.request_count, total_stats)) * 1.5,
     max(map(lambda x: x.request_count, total_stats)) * 1.5,
     '|'.join(map(lambda x: x.date.strftime("%m/%d"), total_stats)))
    
  # sort placements by impression count
  placements = unique_placements.values()
  placements.sort(lambda x,y: cmp(y.request_count, x.request_count))
  
  # thanks
  return render_to_response(request, 
    'admin/d.html', 
    {"stats": total_stats, 
      "chart_url": url,
      "request_count": sum(map(lambda x: x.request_count, total_stats)),
      "click_count": sum(map(lambda x: x.click_count, total_stats)),
      "unique_placements": unique_placements, 
      "unique_accounts": unique_accounts, 
      "placements": placements})