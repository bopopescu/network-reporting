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

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm

from admin.models import AdminPage
from publisher.models import Site, Account, App
from reporting.models import SiteStats,StatsModel
from account.query_managers import AccountQueryManager, UserQueryManager
from publisher.query_managers import AppQueryManager
from reporting.query_managers import StatsModelQueryManager

from google.appengine.api import taskqueue

from admin import beatbox

MEMCACHE_KEY = "jpayne:admin/d:render_p"

@login_required
def admin_switch_user(request,*args,**kwargs):
    params = request.POST or request.GET
    url = params.get('next',None) or request.META["HTTP_REFERER"]
    
    # redirect where the request came from
    response = HttpResponseRedirect(url)
    
    # drop a cookie of the email is the admin user is trying to impersonate
    if users.is_current_user_admin():
    	email = params.get('user_email',None)
    	set_cookie = False
    	if email:
    	  user = UserQueryManager.get_by_email(email)
    	  account = AccountQueryManager.get_current_account(user=user)
    	  if account:
    		response.set_cookie('account_impersonation',str(account.key()))
    		response.set_cookie('account_email',str(account.mpuser.email))
    		set_cookie = True
    	if not set_cookie:
    	  response.delete_cookie('account_impersonation')	 
    return response
  
  
def dashboard_prep(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False


    # mark the page as loading
    def _txn():
        page = AdminPage.get_by_stats_source(offline=offline)
        if page:
            page.loading = True
            page.put()
    db.run_in_transaction(_txn)    
    
    
    days = StatsModel.lastdays(30)
    # gets all undeleted applications
    start_date = datetime.date.today() - datetime.timedelta(days=30) # NOTE: change
    apps = AppQueryManager.get_apps(limit=1000)    
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
            user_count = totals[str(app_stat.date)].user_count + 1
            _incr_dict(totals,str(app_stat.date),app_stat)
            totals[str(app_stat.date)].user_count = user_count
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
        "mailing_list": [a for a in new_users if a.mpuser.mailing_list]}

    page = AdminPage(offline=offline,
                     html=render_to_string(request,'admin/pre_render.html',render_params),
                     today_requests=total_stats[-1].request_count)
    page.put()
    
    return HttpResponse("OK")
 
@login_required
def dashboard(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = True if offline == "1" else False
    refresh = request.GET.get('refresh',False)
    refresh = True if refresh == "1" else False
    loading = request.GET.get('loading',False)
    loading = True if loading == "1" else False
    
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
            return HttpResponseRedirect(reverse('admin_dashboard')+'?loading=1')
        except Exception, e:
            logging.warning("task error: %s"%e)                
        
    page = AdminPage.get_by_stats_source(offline=offline)
    loading = loading or page.loading
    return render_to_response(request,'admin/d.html',{'page': page, 'loading': loading})
        
def update_sfdc_leads(request, *args, **kwargs):
    #
    # a convenience function that maps accounts > SFDC fields
    #
    def account_to_sfdc(a):
        apps = App.gql("where account = :1", a).fetch(100)
        return {'FirstName': (a.mpuser.first_name or '')[:40],
                'LastName': (a.mpuser.last_name or '')[:80],
                'Email': a.mpuser.email or '',
                'Title': (a.mpuser.title or '')[:80],
                'Company': (a.company or a.mpuser.email or '')[:255], 
                'City': (a.mpuser.city or '')[:40],
                'State': (a.mpuser.state or '')[:20],
                'Country': (a.country or '')[:40],
                'Phone': (a.phone or '')[:40],
                'Mailing_List__c': a.mpuser.mailing_list,
                'Apps__c': "\n".join(app.name for app in apps),
                'Number_of_Apps__c': len(apps),
                'iTunesURL__c': max(app.url for app in apps) if apps else None,
                'LeadSource': 'app.mopub.com', 
                'Impressions_Month__c': str(a.traffic) or "Unknown",
                'MoPub_Account_ID__c': str(a.key()),
                'MoPub_Signup_Date__c': a.date_added,
                'type': 'Lead'}
    
    # Gnarly constants
    USER = "jim@mopub.com"
    PW = "fhaaCohb0hXCNSQnreJUPhHbgKYNaQf00"
    BATCH_SIZE = 1      # this is so low because we cannot override the urlfetch timeout easily w/ beatbox, so only have 5 seconds to do it
    DAYS_BACK = 1       # only update N days of recent users at a time
    ACCOUNT_FETCH_MAX = 1000   # maximum number of records to pull out of Account table

    # Login to SFDC as Jim
    sforce = beatbox.PythonClient()
    try:
        login_result = sforce.login(USER, PW)
    except beatbox.SoapFaultError, errorInfo:
        print "Login failed: %s %s" % (errorInfo.faultCode, errorInfo.faultString)
        return
    
    # Create/update the recent leads...  
    start_date = datetime.date.today() - datetime.timedelta(days=DAYS_BACK)
    accounts = Account.gql("where date_added >= :1", start_date).fetch(ACCOUNT_FETCH_MAX)
    results = ""
    while len(accounts) > 0:
        try:
            create_result = sforce.upsert('MoPub_Account_ID__c', [account_to_sfdc(a) for a in accounts[:BATCH_SIZE]])
            results += str(create_result)
        except:
            logging.info("Submit into SFDC failed for %d records" % BATCH_SIZE)
        accounts[:BATCH_SIZE] = []

    # Cool
    return HttpResponse(results)