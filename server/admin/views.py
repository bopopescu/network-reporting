import logging, os, re, datetime, hashlib

from urllib import urlencode
import time

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
from common.ragendja.template import render_to_response, render_to_string
from django.core.mail import send_mail, EmailMessage

from common.utils.decorators import whitelist_login_required

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm

from admin.models import AdminPage
from publisher.models import Site, Account, App
from reporting.models import SiteStats,StatsModel
from publisher.query_managers import AppQueryManager
from reporting.query_managers import StatsModelQueryManager

from google.appengine.api import taskqueue

MEMCACHE_KEY = "jpayne:admin/d:render_p"

@login_required
def admin_switch_user(request,*args,**kwargs):
    params = request.POST or request.GET
    url = request.META["HTTP_REFERER"]
    
    # redirect where the request came from
    response = HttpResponseRedirect(url)
    
    # drop a cookie of the email is the admin user is trying to impersonate
    if users.is_current_user_admin():
    	user_key = params.get('user_key',None)
    	set_cookie = False
    	if user_key:
    	  account = Account.get(user_key)
    	  if account:
    		response.set_cookie('account_impersonation',params.get('user_key'))
    		set_cookie = True
    	if not set_cookie:
    	  response.delete_cookie('account_impersonation')	 
    return response
  
  
def dashboard_prep(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False

    days = StatsModel.lastdays(30)
    # gets all undeleted applications
    start_date = datetime.date.today() - datetime.timedelta(days=29) # NOTE: change
    apps = AppQueryManager().get_apps(limit=1000)    
    # get all the daily stats for the undeleted apps
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
            user_count = totals[str(app_stat.date)].user_count
            _incr_dict(totals,str(app_stat.date),app_stat)
            totals[str(app_stat.date)].user_count = user_count + 1
        if app_stat._publisher:
            _incr_dict(unique_apps,str(app_stat._publisher),app_stat)
    
    # organize daily stats by date
    total_stats = totals.values()
    total_stats.sort(lambda x,y: cmp(x.date,y.date))
    apps = unique_apps.values()
    apps.sort(lambda x,y: cmp(y.request_count, x.request_count))
    
    # get folks who want to be on the mailing list
    new_users = Account.gql("where date_added >= :1 order by date_added desc", start_date).fetch(1000)
    
    # params
    render_params = {"stats": total_stats, 
        "start_date": start_date,
        "today": total_stats[-1],
        "yesterday": total_stats[-2],
        "all": StatsModel(request_count=sum([x.request_count for x in total_stats]), 
            impression_count=sum([x.impression_count for x in total_stats]), 
            click_count=sum([x.click_count for x in total_stats]),
            user_count=max([x.user_count for x in total_stats])),
        "apps": apps,
        "unique_apps": unique_apps, 
        "new_users": new_users,
        "mailing_list": [a for a in new_users if a.mailing_list]}

    page = AdminPage(offline=offline,html=render_to_string(request,'admin/d.html',render_params))
    page.put()
    
    return HttpResponse("OK")
 
@login_required
def dashboard(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False
    refresh = request.GET.get('refresh',False)
    refresh = True if refresh == "1" else False
    
    if offline:
        key_name = "offline"
    else:
        key_name = "realtime"
    if refresh:
        now = time.time()
        time_bucket = int(now)/300 #only allow once ever 5 minutes
        task_name = "admin-%s"%time_bucket
        if offline:
            task_name = 'offline-' + task_name
        task = taskqueue.Task(name=task_name,
                              params=dict(offline="1" if offline else "0"),
                              method='GET',
                              url='/admin/prep/')
        try:                      
            task.add("admin-dashboard-queue")
        except Exception, e:
            logging.warning("task error: %s"%e)                
        
    page = AdminPage.get_by_key_name(key_name)
    return HttpResponse(page.html)
