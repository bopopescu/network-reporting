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
from django.core.mail import send_mail, EmailMessage

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
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    stats = SiteStats.gql("where date > :1 and owner = null order by date desc", start_date)

    # calculate unique active Site and Account
    # plus accumulate total impression and click counts
    unique_placements = {}
    unique_accounts = {}
    totals = {}

    # go and do it
    for s in stats:
        # add this site stats to the total for the day
        a = totals.get(str(s.date)) or SiteStats(date=s.date)
        totals[str(s.date)] = a + s
        
        # add a hash key for the site key and account key to calculate uniques
        try:
            unique_placements[str(s.site.key())] = s + (unique_placements.get(str(s.site.key())) or SiteStats(site=s.site))
        except:
            pass
    
    # organize daily stats
    total_stats = totals.values()
    total_stats.sort(lambda x,y: cmp(x.date,y.date))

    # make a graph
    url = "http://chart.apis.google.com/chart?cht=lc&chs=600x240&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
    ','.join(map(lambda x: str(x.request_count), total_stats)), 
    max(map(lambda x: x.request_count, total_stats)) * 1.5,
    max(map(lambda x: x.request_count, total_stats)) * 1.5,
    '|'.join(map(lambda x: x.date.strftime("%m/%d"), total_stats)))

    # sort placements by impression count
    placements = unique_placements.values()
    placements.sort(lambda x,y: cmp(y.request_count, x.request_count))
    
    # figure out unique accounts
    unique_accounts = set([x.site.account.key() for x in placements])

    # thanks
    return render_to_response(request, 
    'admin/d.html', 
    {"stats": total_stats, 
    "chart_url": url,
    "request_count": sum(map(lambda x: x.request_count, total_stats)),
    "click_count": sum(map(lambda x: x.click_count, total_stats)),
    "growth": total_stats[-2].request_count / float(total_stats[0].request_count) - 1.0,
    "unique_placements": unique_placements, 
    "unique_accounts": unique_accounts, 
    "placements": placements})
    
@login_required
def report(request, *args, **kwargs):
    start_date = datetime.date.today() - datetime.timedelta(days=8)
    today = datetime.date.today() - datetime.timedelta(days=1)
    
    # get stats from beginning of period and today
    start_stats = SiteStats.gql("where date = :1 and owner = null order by date desc", start_date)
    today_stats = SiteStats.gql("where date >= :1 and owner = null order by date desc", today)
    
    # compute totals
    start_requests = sum([x.request_count for x in start_stats])
    today_requests = sum([x.request_count for x in today_stats])
    ad_units = len(set([x.site.key() for x in today_stats]))
    growth = 100 * ((today_requests / float(start_requests)) - 1.0)
    
    # send a note
    metrics = "Served %d requests across %d ad units (%.1f%% w/w)" % (today_requests, ad_units, growth)
    send_mail(metrics,"http://ads.mopub.com/admin/d/",'olp@mopub.com',['metrics@mopub.com'],fail_silently=True)
    return HttpResponse()
    