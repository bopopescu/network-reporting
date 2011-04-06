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
from reporting.models import SiteStats,StatsModel
from publisher.query_managers import AppQueryManager
from reporting.query_managers import StatsModelQueryManager

MEMCACHE_KEY = "jpayne:admin/d:render_p"

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
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False

    days = StatsModel.lastdays(30)
    # gets all undeleted applications
    start_date = datetime.date.today() - datetime.timedelta(days=30)
    apps = AppQueryManager().get_apps(limit=1000)
    logging.info("apps:%s"%apps)
    
    # get all the daily stats for the undeleted apps
    # app_stats = StatsModelQueryManager(None,offline=offline).get_stats_for_days(publisher=apps[0],account=apps[0].account,days=days)
    app_stats = StatsModelQueryManager(None,offline=offline).get_stats_for_apps(apps=apps,num_days=30)

    # accumulate individual site stats into daily totals 
    unique_apps = {}
    totals = {}
    
    for d in days:
        dt = datetime.datetime(year=d.year,month=d.month,day=d.day)
        totals[str(dt)] = StatsModel(date=dt)
        totals[str(dt)].user_count = 0
    
    # init the totals dictionary
    def _incr_dict(d,k,v):
        if not k in d:
            d[k] = v
        else:
            d[k] += v
    
    # go and do it
    for app_stat in app_stats:
        # add this site stats to the total for the day and increment user count
        if app_stat.date:
            _incr_dict(totals,str(app_stat.date),app_stat)
            totals[str(app_stat.date)].user_count += 1
        if app_stat._publisher:
            _incr_dict(unique_apps,str(app_stat._publisher),app_stat)
    
    # organize daily stats by date
    total_stats = totals.values()
    total_stats.sort(lambda x,y: cmp(x.date,y.date))
    apps = unique_apps.values()
    apps.sort(lambda x,y: cmp(y.request_count, x.request_count))
    logging.info("\n\napps:%s\n\n\n"%apps)
    
    # get folks who want to be on the mailing list
    mailing_list = Account.gql("where date_added > :1 order by date_added desc", start_date).fetch(1000)
    
    # params
    render_p = {"stats": total_stats, 
        "start_date": start_date,
        "today": total_stats[-1],
        "yesterday": total_stats[-2],
        "all": StatsModel(request_count=sum([x.request_count for x in total_stats]), 
            impression_count=sum([x.impression_count for x in total_stats]), 
            click_count=sum([x.click_count for x in total_stats]),
            user_count=max([x.user_count for x in total_stats])),
        "apps": apps,
        "unique_apps": unique_apps, 
        "mailing_list": [a for a in mailing_list if a.mailing_list]}
    key = MEMCACHE_KEY
    if offline:
        key += ':offline'    
    memcache.set(key, render_p)
    
    url = reverse('admin_dashboard')
    if offline:
        url += '?offline=1'
    
    return HttpResponseRedirect(url)
 
@login_required
def dashboard(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False
    refresh = request.GET.get('refresh',False)
    refresh = True if refresh == "1" else False
    
    key = MEMCACHE_KEY
    if offline:
        key += ':offline'
    render_p = memcache.get(key)
    if render_p and not refresh:
        return render_to_response(request, 
            'admin/d.html', 
             render_p)
    else:
        url = reverse('dashboard_prep')
        if offline:
            url += '?offline=1'
        return HttpResponseRedirect(url)        
    
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
    