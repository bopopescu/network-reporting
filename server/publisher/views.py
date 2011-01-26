import logging, os, re, datetime, hashlib

import urllib
# hack to get urllib to work on snow leopard
urllib.getproxies_macosx_sysconf = lambda: {}

from urllib import urlencode
from operator import itemgetter
import base64, binascii

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms
from google.appengine.api import images

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required


from publisher.models import Site, Account, App
from publisher.forms import SiteForm, AppForm
from advertiser.models import Campaign, AdGroup, HtmlCreative
from reporting.models import SiteStats

from common.utils.cachedquerymanager import CachedQueryManager
from account.query_managers import AccountQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager
from reporting.query_managers import SiteStatsQueryManager
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, \
                                      CreativeQueryManager

class RequestHandler(object):
    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request
        self.account = None
        
        try:
          # Limit date range to 31 days, otherwise too heavy
          self.date_range = min(int(self.params.get('r')),31)  # date range
        except:
          self.date_range = 14
          
        try:
          s = self.request.GET.get('s').split('-')
          self.start_date = datetime.date(int(s[0]),int(s[1]),int(s[2]))
        except:
          self.start_date = None

        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key_name = request.COOKIES.get("account_impersonation",None)
            if account_key_name:
              self.account = AccountQueryManager().get_by_key_name(account_key_name)
        if not self.account:  
          self.account = Account.current_account()
          
        if request.method == "GET":
            return self.get(*args,**kwargs)
        elif request.method == "POST":
            return self.post(*args,**kwargs)    
    def get(self):
        pass
    def put(self):
        pass  

def gen_chart_url(series, days, title):
  chart_url = "http://chart.apis.google.com/chart?cht=lc&chtt=%s&chs=580x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
    title,
    ','.join(map(lambda x: str(x), series)),
    max(series) * 1.5,
    max(series) * 1.5,
    '|'.join(map(lambda x: x.strftime("%m/%d"), days)))

  return chart_url
  
def gen_pie_chart_url(series, title):
  #TODO: Shouldn't use 'app' as a key name since it also works for ad units
  chart_url = "http://chart.apis.google.com/chart?cht=p&chtt=%s&chs=200x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chl=&chdlp=b&chdl=%s" % (
    title,
    ','.join(map(lambda x: str(x["total"]), series)),
    max(map(lambda x: x.stats.request_count, [s["app"] for s in series])) * 1.5,
    max(map(lambda x: x.stats.request_count, [s["app"] for s in series])) * 1.5,
    '|'.join(map(lambda x: x["app"].name, series[0:2])))
  
  return chart_url

class AppIndexHandler(RequestHandler):
  def get(self):
    report = self.request.POST.get('report')

    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    apps = AppQueryManager().get_apps(self.account)
    if len(apps) == 0:
      return HttpResponseRedirect(reverse('publisher_app_create'))

    for a in apps:
      if a.icon:
        a.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(a.icon)

      a.stats = SiteStats()
      # attaching adunits onto the app object
      a.adunits = AdUnitQueryManager().get_adunits(app=a)

      # organize impressions by days
      for adunit in a.adunits:
        adunit.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=adunit,days=days)
        adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, SiteStats())

      a.adunits = sorted(a.adunits, key=lambda adunit: adunit.stats.request_count, reverse=True)

      # We have to read the datastore at the app level since we need to get the de-duped unique_user_count
      a.all_stats = SiteStatsQueryManager().get_sitestats_for_days(owner=a,days=days)
      a.stats = reduce(lambda x, y: x+y, a.all_stats, SiteStats())

    apps = sorted(apps, key=lambda app: app.stats.request_count, reverse=True)

    # In the graph, only show the top 3 apps and bundle the rest if there are more than 4
    graph_apps = apps[0:4]
    if len(apps) > 4:
      graph_apps[3] = {'name': 'Others',
                       'totals': [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[a.all_stats for a in apps[3:]])]
                       }

    return render_to_response(self.request,'publisher/index.html', 
      {'apps': apps,
       'graph_apps': graph_apps,
       'start_date': days[0],
       'date_range': self.date_range,
       'totals': reduce(lambda x, y: x+y.stats, apps, SiteStats()),
       'account': self.account})

@whitelist_login_required     
def index(request,*args,**kwargs):
  return AppIndexHandler()(request,*args,**kwargs)     

class AppIndexGeoHandler(RequestHandler):
  def get(self):
    # compute start times; start day before today so incomplete days don't mess up graphs
    days = SiteStats.lastdays(14)
    
    apps = AppQueryManager().get_apps(self.account)
    
    if len(apps) == 0:
      return HttpResponseRedirect(reverse('publisher_app_create'))

    geo_req = {}  
    geo_imp = {}
    geo_clk = {}
    geo_rev = {}
    for a in apps:
      a.adunits = AdUnitQueryManager().get_adunits(app=a)
      if len(a.adunits) > 0:
        for adunit in a.adunits:
          adunit.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=adunit, days=days)
          for stats in adunit.all_stats:
            #stats.geo_imp = simplejson.loads(stats.geo_impressions)
            #stats.geo_clk = simplejson.loads(stats.geo_clicks)
            #stats.geo_rev = simplejson.loads(stats.geo_revenue)
            geo_req = dict( (n, geo_req.get(n,0)+stats.geo_requests.get(n,0)) for n in set(geo_req)|set(stats.geo_requests) )
            #geo_imp = dict( (n, geo_imp.get(n,0)+stats.geo_imp.get(n,0)) for n in set(geo_imp)|set(stats.geo_imp) )
            #geo_clk = dict( (n, geo_clk.get(n,0)+stats.geo_clk.get(n,0)) for n in set(geo_clk)|set(stats.geo_clk) )
            #geo_rev = dict( (n, geo_rev.get(n,0)+stats.geo_rev.get(n,0)) for n in set(geo_rev)|set(stats.geo_rev) )

    geo_req = sorted(geo_req.items(), key=itemgetter(1), reverse=True)
    return render_to_response(self.request,'publisher/index_geo.html', 
      {'geo_imp': geo_imp,    
       'geo_clk': geo_clk,
       'geo_rev': geo_rev,
       'geo_req': geo_req,
       'account': self.account})

@whitelist_login_required     
def index_geo(request,*args,**kwargs):
  return AppIndexGeoHandler()(request,*args,**kwargs)     

class AppCreateHandler(RequestHandler):
  def get(self):
    apps = AppQueryManager().get_apps(self.account,limit=1)
    f = AppForm()
    return render_to_response(self.request,'publisher/new_app.html', {"f": f, "has_app": len(apps)})

  def post(self):
    app = None
    if self.request.POST.get("app_key"):
      app = AppQueryManager().get_by_key(self.request.POST.get("app_key"))
      f = AppForm(data=self.request.POST, instance=app)
    else:
      f = AppForm(data=self.request.POST)
      
    if f.is_valid():
      app = f.save(commit=False)
      app.account = self.account
      # Store the image
      if not self.request.POST.get("img_url") == "":
        try:
          response = urllib.urlopen(self.request.POST.get("img_url"))
          img = response.read()
          app.icon = db.Blob(img)
        except:
          pass
      elif self.request.FILES.get("img_file"):
        try:
          icon = images.resize(self.request.FILES.get("img_file").read(), 60, 60)
          app.icon = db.Blob(icon)
        except:
          pass

      AppQueryManager().put_apps(app)

      # If we get the adunit information, try to create that too
      if not self.request.POST.get("adunit_name"):
        return HttpResponseRedirect(reverse('publisher_app_show',kwargs={'app_key':app.key()}))
      
      data = self.request.POST.copy()
      data['name'] = self.request.POST.get("adunit_name")
      data['adunit_description'] = self.request.POST.get("adunit_description")
      sf = SiteForm(data=data)
      if sf.is_valid():
        adunit = sf.save(commit=False)
        adunit.account = self.account
        adunit.app_key = app

        # update the database
        AdUnitQueryManager().put_adunits(adunit)

        # update the cache as necessary 
        # replace=True means don't do anything if not already in the cache
        CachedQueryManager().cache_delete(adunit)

        # Check if this is the first ad unit for this account
        # if Site.gql("where account = :1 limit 2", self.account).count() == 1:
        if len(AdUnitQueryManager().get_adunits(account=self.account,limit=2)) == 1:      
          add_demo_campaign(adunit)
        return HttpResponseRedirect(reverse('publisher_generate',kwargs={'adunit_key':adunit.key()}))
      else:
        return render_to_response(self.request,'publisher/new_app.html', {"f": f, "app": app, "app_key":app.key()})
    else:
      return render_to_response(self.request,'publisher/new_app.html', {"f": f})

@whitelist_login_required  
def app_create(request,*args,**kwargs):
  return AppCreateHandler()(request,*args,**kwargs)
    
class CreateAdUnitHandler(RequestHandler):
 def post(self):
    f = SiteForm(data=self.request.POST)
    a = AppQueryManager().get_by_key(self.request.POST.get('id'))
    if f.is_valid():
      adunit = f.save(commit=False)
      adunit.account = self.account
      adunit.app_key = a
      
      # update the database
      AdUnitQueryManager().put_adunits(adunit)
      
      # update the cache as necessary 
      # replace=True means don't do anything if not already in the cache
      CachedQueryManager().cache_delete(adunit)
      
      # Check if this is the first ad unit for this account
      # if Site.gql("where account = :1 limit 2", self.account).count() == 1:
      if len(AdUnitQueryManager().get_adunits(account=self.account,limit=2)) == 1:      
        add_demo_campaign(adunit)
      return HttpResponseRedirect(reverse('publisher_generate',kwargs={'adunit_key':adunit.key()}))
    else:
      print f.errors

@whitelist_login_required  
def adunit_create(request,*args,**kwargs):
  return CreateAdUnitHandler()(request,*args,**kwargs)   

def add_demo_campaign(site):
  # Set up a test campaign that returns a demo ad
  c = Campaign(name="MoPub Demo Campaign",
               u=site.account.user,
               campaign_type="promo",
               description="Demo campaign for checking that MoPub works for your application")
  CampaignQueryManager().put_campaigns(c)

  # Set up a test ad group for this campaign
  ag = AdGroup(name="MoPub Demo Campaign",
               campaign=c,
               priority_level=3,
               bid=1.0,
               site_keys=[site.key()])
  AdGroupQueryManager().put_adgroups(ag)

  # And set up a default creative
  h = HtmlCreative(ad_type="html", ad_group=ag)
  CreativeQueryManager().put_creatives(h)
  
class ShowAppHandler(RequestHandler):
  def get(self,app_key):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    # load the site
    a = AppQueryManager().get_by_key(app_key)
    if a.account.key() != self.account.key():
      raise Http404

    a.stats = SiteStats()
    a.adunits = AdUnitQueryManager().get_adunits(app=a)
    
    # organize impressions by days
    if len(a.adunits) > 0:
      for adunit in a.adunits:
        adunit.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=adunit,days=days)
        adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, SiteStats())
        a.stats += adunit.stats
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[au.all_stats for au in a.adunits])]
    else:
      totals = [SiteStats() for d in days]
      
    a.adunits = sorted(a.adunits, key=lambda adunit: adunit.stats.request_count, reverse=True)
      
    # TODO: We are calculating app-level totals twice
    app_stats = SiteStatsQueryManager().get_sitestats_for_days(owner=a,days=days)
    # set the apps unique user count from the app stats rollup
    for stat,app_stat in zip(totals,app_stats):
      stat.unique_user_count = app_stat.unique_user_count

    help_text = 'Create an Ad Unit below' if len(a.adunits) == 0 else None
    
    if a.icon:
      a.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(a.icon)

    # In the graph, only show the top 3 ad units and bundle the rest if there are more than 4
    a.graph_adunits = a.adunits[0:4]
    if len(a.adunits) > 4:
      a.graph_adunits[3] = {'name': 'Others',
                            'all_stats': [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[au.all_stats for au in a.adunits[3:]])]
                           }

    return render_to_response(self.request,'publisher/show_app.html', 
        {'app': a,    
         'start_date': days[0],
         'date_range': self.date_range,
         'account': self.account,
         'helptext': help_text})

@whitelist_login_required
def app_show(request,*args,**kwargs):
  return ShowAppHandler()(request,*args,**kwargs)   

class AdUnitShowHandler(RequestHandler):
  def get(self,adunit_key):
    # load the site
    adunit = AdUnitQueryManager().get_by_key(adunit_key)
    if adunit.account.key() != adunit.account.key():
      raise Http404

    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    adunit.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=adunit,days=days)
    for i in range(len(days)):
      adunit.all_stats[i].date = days[i]

    adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, SiteStats())

    # Get all of the ad groups for this site
    adunit.adgroups = AdGroupQueryManager().get_adgroups(adunit=adunit)
    adunit.adgroups = sorted(adunit.adgroups, lambda x,y: cmp(y.bid, x.bid))
    for ag in adunit.adgroups:
      ag.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=adunit,owner=ag,days=days)
      ag.stats = reduce(lambda x, y: x+y, ag.all_stats, SiteStats())
      
    # write response
    return render_to_response(self.request,'publisher/show.html', 
        {'site':adunit,
         'start_date': days[0],
         'date_range': self.date_range,
         'account':self.account, 
         'days': days})
  
@whitelist_login_required
def adunit_show(request,*args,**kwargs):
  return AdUnitShowHandler()(request,*args,**kwargs)   

class AppUpdateHandler(RequestHandler):
  def get(self,app_key):
    a = AppQueryManager().get_by_key(app_key)
    f = AppForm(instance=a)
    
    if a.icon:
      a.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(a.icon)
    
    return render_to_response(self.request,'publisher/edit_app.html', {"f": f, "app": a})

  def post(self,app_key):
    a = AppQueryManager().get_by_key(app_key)
    f = AppForm(data=self.request.POST, instance=a)
    if a.account.user == self.account.user:
      f.save(commit=False)

      # Store the image
      if not self.request.POST.get("img_url") == "":
        try:
          response = urllib.urlopen(self.request.POST.get("img_url"))
          img = response.read()
          a.icon = db.Blob(img)
        except:
          pass
      elif self.request.FILES.get("img_file"):
        try:
          icon = images.resize(self.request.FILES.get("img_file").read(), 60, 60)
          a.icon = db.Blob(icon)
        except:
          pass

      AppQueryManager().put_apps(a)

    return HttpResponseRedirect(reverse('publisher_app_show',kwargs={'app_key':a.key()}))

@whitelist_login_required
def app_update(request,*args,**kwargs):
  return AppUpdateHandler()(request,*args,**kwargs)   

class UpdateAdUnitHandler(RequestHandler):
  def get(self,adunit_key):
    adunit = AdUnitQueryManager().get_by_key(adunit_key)
    f = SiteForm(instance=adunit)
    return render_to_response(self.request,'publisher/edit.html', {"f": f, "site": adunit})

  def post(self,adunit_key):
    adunit = AdUnitQueryManager().get_by_key(adunit_key)
    f = SiteForm(data=self.request.POST, instance=adunit)
    if adunit.account.user == self.account.user:
      f.save(commit=False)

      # update the database
      AdUnitQueryManager().put_adunits(adunit)
      
      # update the cache as necessary 
      # replace=True means don't do anything if not already in the cache
      CachedQueryManager().cache_delete(adunit)
      
    return HttpResponseRedirect(reverse('publisher_adunit_show',kwargs={'adunit_key':adunit.key()}))
  
@whitelist_login_required
def adunit_update(request,*args,**kwargs):
  return UpdateAdUnitHandler()(request,*args,**kwargs)   

class AppIconHandler(RequestHandler):
  def get(self, app_key):
    a = App.get(app_key)
    if a.icon:
      response = HttpResponse(a.icon)
      response['Content-Type'] = 'image/png'
      return response
    else:
      HttpResponseRedirect('/images/noicon.png')

def app_icon(request,*args,**kwargs):
  return AppIconHandler()(request,*args,**kwargs)
    
# Set up a new user with a default campaign
class GetStartedHandler(RequestHandler):
  def get(self):
    # Check if the user is in the data store and create it if not

    user = self.account.user
    account = Account.get_by_key_name(user.user_id())
    if not account:
      account = Account(key_name=user.user_id(),user=user)
      AccountQueryManager.put_accounts(account)
      
    return HttpResponseRedirect(reverse('publisher_index'))

@whitelist_login_required
def getstarted(request,*args,**kwargs):
  return GetStartedHandler()(request,*args,**kwargs)   

class RemoveAdUnitHandler(RequestHandler):
  def post(self):
    ids = self.request.POST.getlist('id')
    for adunit_key in ids:
      a = AdUnitQueryManager().get_by_key(adunit_key)
      if a != None and a.app_key.account == self.account:
        a.deleted = True
        AdUnitQueryManager().put_adunits(a)
        # delete from cache
        CachedQueryManager().cache_delete(a)
    return HttpResponseRedirect(reverse('publisher_app_show','app_key',a.app_key.key()))
 
@whitelist_login_required
def adunit_delete(request,*args,**kwargs):
  return RemoveAdUnitHandler()(request,*args,**kwargs)

class GenerateHandler(RequestHandler):
  def get(self,adunit_key):
    adunit = AdUnitQueryManager().get_by_key(adunit_key)
    return render_to_response(self.request,'publisher/code.html', {'site': adunit})
  
@whitelist_login_required
def generate(request,*args,**kwargs):
  return GenerateHandler()(request,*args,**kwargs) 
