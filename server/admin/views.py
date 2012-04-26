from __future__ import with_statement

import logging, os, re, datetime, hashlib

from urllib import urlencode
from urllib2 import urlopen
import time

from django.http import Http404

from google.appengine.api import users
from google.appengine.api.urlfetch import fetch
from google.appengine.api import mail
from google.appengine.api import memcache
from google.appengine.api import files
from google.appengine.ext import db, blobstore
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, render_to_string
from django.core.mail import send_mail, EmailMessage

from advertiser.models import *

from admin.models import AdminPage
from publisher.models import Site, Account, App
from reporting.models import SiteStats,StatsModel
from reports.models import Report
from account.query_managers import AccountQueryManager, UserQueryManager
from publisher.query_managers import AppQueryManager
from reporting.query_managers import StatsModelQueryManager
from common.utils.stats_helpers import MarketplaceStatsFetcher, MPStatsAPIException

from google.appengine.api import taskqueue

from admin import beatbox
from common.utils.decorators import cache_page_until_post, staff_login_required
from common.utils import simplejson
from common.utils.helpers import to_ascii, to_uni

MEMCACHE_KEY = "jpayne:admin/d:render_p"
NUM_DAYS = 14

BIDDER_SPENT_URL = "http://mpx.mopub.com/spent?api_key=asf803kljsdflkjasdf"
BIDDER_SPENT_MAX = 2000

ADMIN_MONGO_ACCT = 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eDlEww'
ADMIN_MONGO_PUB = 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eDlEww'
ADMIN_MONGO_ADV = 'agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eDlEww'

@staff_login_required
@cache_page_until_post()
def admin_switch_user(request,*args,**kwargs):
    params = request.POST or request.GET
    url = params.get('next',None) or request.META["HTTP_REFERER"]

    # redirect where the request came from
    response = HttpResponseRedirect(url)

    # drop a cookie of the email is the admin user is trying to impersonate
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


    days = StatsModel.lastdays(NUM_DAYS)
    # gets all undeleted applications
    start_date = StatsModel.today() - datetime.timedelta(days=(NUM_DAYS-1)) # NOTE: change
    logging.warning('start_date: %s days :%s', start_date, days)
    days.remove(StatsModel.today())

    total_stats = StatsModelQueryManager(None, offline=False).get_stats_for_days(publisher=ADMIN_MONGO_PUB,
                                                                                 account=ADMIN_MONGO_ACCT, 
                                                                                 advertiser=ADMIN_MONGO_ADV, 
                                                                                 days=days, use_mongo=True)

    # apps = AppQueryManager.get_all_apps()

    # # get all the daily stats for the undeleted apps
    # # app_stats = StatsModelQueryManager(None,offline=offline).get_stats_for_apps(apps=apps,num_days=30)

    # # accumulate individual site stats into daily totals
    # unique_apps = {}
    # totals = {}

    # for d in days:
    #     dt = datetime.datetime(year=d.year,month=d.month,day=d.day)
    #     totals[str(dt)] = StatsModel(date=dt)
    #     totals[str(dt)].user_count = 0

    # # init the totals dictionary
    # def _incr_dict(d,k,v):
    #     if not k in d:
    #         d[k] = v
    #     else:
    #         d[k] += v

    # # go and do it
    # for app in apps:
    #     app_stats = StatsModelQueryManager(None,offline=offline).get_stats_for_apps(apps=[app],days=days)
    #     yesterday = app_stats[-1]

    #     for app_stat in app_stats:
    #         # add this site stats to the total for the day and increment user count
    #         if app_stat.date:
    #             user_count = totals[str(app_stat.date)].user_count + 1
    #             _incr_dict(totals,str(app_stat.date),app_stat)
    #             totals[str(app_stat.date)].user_count = user_count
    #         if app_stat._publisher:
    #             _incr_dict(unique_apps,str(app_stat._publisher),app_stat)

    #     # Calculate a 1 day delta between yesterday and the day before that
    #     if app_stats[-2].date and app_stats[-3].date and app_stats[-2]._publisher and app_stats[-3].request_count > 0:
    #         unique_apps[str(app_stats[-2]._publisher)].requests_delta1day = \
    #             float(app_stats[-2].request_count - app_stats[-3].request_count) / app_stats[-3].request_count
    #     # % US for yesterday
    #     unique_apps[str(app_stats[-2]._publisher)].percent_us = app_stats[-2].get_geo('US', 'request_count') / float(yesterday.request_count) if yesterday.request_count > 0 else 0

    #     # get mpx revenue/cpm numbers
    #     try:
    #         stats_fetcher = MarketplaceStatsFetcher(yesterday.publisher.account.key())
    #         mpx_stats = stats_fetcher.get_app_stats(str(yesterday._publisher), start_date, days[-1])
    #         unique_apps[str(yesterday._publisher)].mpx_revenue = float(mpx_stats.get('revenue', 0.0))
    #         unique_apps[str(yesterday._publisher)].mpx_impression_count = int(mpx_stats.get('impressions', 0))
    #         request_total = float(sum(x.request_count for x in app_stats))
    #         if request_total > 0:
    #             unique_apps[str(yesterday._publisher)].mpx_clear_rate = int(mpx_stats.get('impressions', 0)) / request_total
    #         else:
    #             unique_apps[str(yesterday._publisher)].mpx_clear_rate = 0
    #         unique_apps[str(yesterday._publisher)].mpx_cpm = mpx_stats.get('ecpm')
    #     except MPStatsAPIException, e:
    #         unique_apps[str(yesterday._publisher)].mpx_revenue = 0
    #         unique_apps[str(yesterday._publisher)].mpx_impression_count = 0
    #         unique_apps[str(yesterday._publisher)].mpx_clear_rate = 0
    #         unique_apps[str(yesterday._publisher)].mpx_cpm = '-'

    # # organize daily stats by date
    # total_stats = totals.values()
    # total_stats.sort(lambda x,y: cmp(x.date,y.date))
    # apps = unique_apps.values()
    # apps.sort(lambda x,y: cmp(y.request_count, x.request_count))

    # get folks who want to be on the mailing list
    new_users = Account.gql("where date_added >= :1 order by date_added desc", start_date).fetch(1000)
    mail = []
    unsafe_users = []
    for a in new_users:
        try:
            if a.mpuser.mailing_list: mail.append(a)
        except Exception, e:
            unsafe_users.append(a)
            pass
    new_users = [a for a in new_users if a not in unsafe_users]

    # params
    render_params = {"stats": total_stats,
        "start_date": start_date,
        "yesterday": total_stats[-1],
        "all": StatsModel(request_count=sum([x.request_count for x in total_stats]),
            impression_count=sum([x.impression_count for x in total_stats]),
            click_count=sum([x.click_count for x in total_stats]),
            user_count=max([x.user_count for x in total_stats])),
        "apps": None,
        "unique_apps": None,
        "new_users": new_users,
        "mailing_list": mail}

    #need to convert to uni, then ascii for blobstore encoding
    html = to_ascii(to_uni(render_to_string(request,'admin/pre_render.html',render_params)))

    internal_file_name = files.blobstore.create(
                        mime_type="text/plain",
                        _blobinfo_uploaded_filename='admin-d.html')


    # open the file and write lines
    with files.open(internal_file_name, 'a') as f:
        f.write(html)

    # finalize this file
    files.finalize(internal_file_name)

    page = AdminPage(offline=offline,
                     blob_key=files.blobstore.get_blob_key(internal_file_name),
                     yesterday_requests=total_stats[-1].request_count)

    page.put()

    return HttpResponse("OK")

def rep_timed_out(rep):
    return not rep.data and rep.status == 'Pending' and (datetime.datetime.now() - rep.created_at).seconds > 7200

@staff_login_required
def reports_dashboard(request, *args, **kwargs):
    reps = Report.all().order('-created_at').fetch(50)
    rep_status = [(rep, rep.status) if not rep_timed_out(rep) else (rep, 'Timed Out') for rep in reps]
    render_params = dict(status = rep_status)
    return render_to_response(request, 'admin/reports.html', render_params)

@staff_login_required
def dashboard(request, *args, **kwargs):
    offline = request.GET.get('offline',False)
    offline = False if offline == "0" else True # defaults use offline
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
                              url='/admin/prep/',
                              target='admin-prep')
        try:
            task.add("admin-dashboard-queue")
            return HttpResponseRedirect(reverse('admin_dashboard')+'?loading=1')
        except Exception, e:
            logging.warning("task error: %s"%e)

    page = AdminPage.get_by_stats_source(offline=offline)

    html_file = blobstore.BlobReader(page.blob_key)
    page.html = html_file.read()

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
    PW = "fhaaCohb2SbVB0IFXhsseGfJ3Onr9UA46"
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
        except beatbox.SoapFaultError, errorInfo:
            mail.send_mail_to_admins(sender="olp@mopub.com",
                                     subject="SFDC upsert failed",
                                     body="%s %s" % (results, errorInfo.faultString))
            logging.error("Submit into SFDC failed for %d records" % BATCH_SIZE)
        accounts[:BATCH_SIZE] = []

    # Cool
    return HttpResponse(results)

def migrate_many_images(request, *args, **kwargs):
    pass


def migrate_image(request, *args, **kwargs):
    """ Migrates a text and tile image. """
    from google.appengine.api import files
    from common.utils import helpers

    params = request.POST or request.GET

    app_keys = params.getlist('app_key')
    for app_key in app_keys:
        app = App.get(app_key)

        # Create the file
        file_name = files.blobstore.create(mime_type='image/png')

        # Open the file and write to it
        with files.open(file_name, 'a') as f:
          f.write(app.icon)

        # Finalize the file. Do this before attempting to read it.
        files.finalize(file_name)

        # Get the file's blob key
        blob_key = files.blobstore.get_blob_key(file_name)

        # Do not delete image yet
        # app.icon = None
        app.icon_blob = blob_key
        url = helpers.get_url_for_blob(blob_key)
        app.put()

    return HttpResponse('(%s, %s)' % (blob_key, url))

def bidder_spent(request, *args, **kwargs):
    num_sent = 0
    try:
        f = urlopen(BIDDER_SPENT_URL)
        spent_dict = simplejson.loads(f.read())
        for id, spent_vals in spent_dict.iteritems():
            #send email if bidder is over quota
            if float(spent_vals['spent']) > BIDDER_SPENT_MAX:
                body = "Bidder (%s) is over budget. Has spent $%s today<br />"%(spent_vals['bidder_name'],spent_vals['spent'])
                mail.send_mail_to_admins(sender="olp@mopub.com",
                                         subject="Bidder Over Quota",
                                         body="%s"%body)
                num_sent += 1
    except:
        pass
    return HttpResponse(str(num_sent))



