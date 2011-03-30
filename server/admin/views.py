import logging, os, re, datetime, hashlib

from urllib import urlencode

from google.appengine.api import users, images
from google.appengine.api.urlfetch import fetch
from google.appengine.api import mail
from google.appengine.api import memcache
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
def dashboard_prep(request, *args, **kwargs):
    # go back in time N days
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    stats = SiteStats.gql("where date > :1 and owner = null order by date desc", start_date)

    # accumulate individual site stats into daily totals 
    unique_apps = {}
    unique_placements = {}
    unique_accounts = {}
    totals = {}

    # go and do it
    for s in stats:
        # add this site stats to the total for the day and increment user count
        a = totals.get(str(s.date)) or SiteStats(date=s.date, unique_user_count=0)
        unique_user_count = a.unique_user_count
        a = a + s
        a.unique_user_count = unique_user_count + 1
        totals[str(s.date)] = a
        
        # add a hash key for the site key and account key to calculate uniques
        try:
            unique_placements[str(s.site.key())] = s + (unique_placements.get(str(s.site.key())) or SiteStats(site=s.site))
            unique_apps[str(s.site.app_key.key())] = s + (unique_apps.get(str(s.site.app_key.key())) or SiteStats(site=s.site))
            unique_accounts[str(s.site.account.key())] = s + (unique_accounts.get(str(s.site.account.key())) or SiteStats(owner=s.site.account))      
        except:
            pass
    
    # organize daily stats by date
    total_stats = totals.values()
    total_stats.sort(lambda x,y: cmp(x.date,y.date))

    # organize apps by req count, also prepopulate some metadata to avoid db.get in /d render pipeline
    apps = unique_apps.values()
    apps.sort(lambda x,y: cmp(y.request_count, x.request_count))
    
    # get folks who want to be on the mailing list
    mailing_list = Account.gql("where date_added > :1 order by date_added desc", start_date).fetch(1000)
    
    # params
    render_p = {"stats": total_stats, 
        "start_date": start_date,
        "today": total_stats[-1],
        "yesterday": total_stats[-2],
        "all": SiteStats(request_count=sum([x.request_count for x in total_stats]), 
            impression_count=sum([x.impression_count for x in total_stats]), 
            click_count=sum([x.click_count for x in total_stats]),
            unique_user_count=max([x.unique_user_count for x in total_stats])),
        "apps": apps,
        "unique_apps": unique_apps, 
        "unique_placements": unique_placements, 
        "unique_accounts": unique_accounts,
        "mailing_list": [a for a in mailing_list if a.mailing_list]}
    memcache.set("jpayne:admin/d:render_p", render_p)
    
    return HttpResponseRedirect(reverse('admin_dashboard'))
 
@login_required
def dashboard(request, *args, **kwargs):
    render_p = memcache.get("jpayne:admin/d:render_p")
    if render_p:
        return render_to_response(request, 
            'admin/d.html', 
             render_p)
    else:
        return HttpResponseRedirect(reverse('dashboard_prep'))        
    
@login_required
def report(request, *args, **kwargs):
    today = datetime.date.today() - datetime.timedelta(days=1)
    
    # get stats from beginning of period and today
    today_stats = SiteStats.gql("where date = :1 and owner = null", today)
    
    # compute totals
    today_requests = sum([x.request_count for x in today_stats])
    ad_units = len(set([x.site.key() for x in today_stats]))
    
    # send a note
    mail.send_mail(sender='jpayne@mopub.com', 
                   to='support@mopub.com',
                   subject="Served %d requests across %d ad units" % (today_requests, ad_units), 
                   body="See more at http://app.mopub.com/admin/d")
    return HttpResponseRedirect(reverse('admin_dashboard'))
    