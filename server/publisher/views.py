import logging, os, re, datetime, hashlib

import urllib
urllib.getproxies_macosx_sysconf = lambda: {}
from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required


from publisher.models import Site, Account, App
from publisher.forms import SiteForm, AppForm
from advertiser.models import Campaign, AdGroup, HtmlCreative
from reporting.models import SiteStats

class RequestHandler(object):
    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request
        self.account = None
        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key_name = request.COOKIES.get("account_impersonation",None)
            if account_key_name:
              self.account = Account.get_by_key_name(account_key_name)
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
    max(map(lambda x: x.stats.impression_count, [s["app"] for s in series])) * 1.5,
    max(map(lambda x: x.stats.impression_count, [s["app"] for s in series])) * 1.5,
    '|'.join(map(lambda x: x["app"].name, series[0:2])))
  
  return chart_url

class AppIndexHandler(RequestHandler):
  def get(self):
    # compute start times; start day before today so incomplete days don't mess up graphs
    days = SiteStats.lastdays(14)

    apps = App.gql("where account = :1 and deleted = :2", self.account, False).fetch(50)
    today = SiteStats()
    if len(apps) > 0:
      for a in apps:
        a.stats = SiteStats()
        a.sites = Site.gql("where app_key = :1 and deleted = :2", a, False).fetch(50)   
        
        # organize impressions by days
        if len(a.sites) > 0:
          for s in a.sites:
            s.all_stats = SiteStats.sitestats_for_days(s, days)
            s.stats = reduce(lambda x, y: x+y, s.all_stats, SiteStats())
            a.stats = reduce(lambda x, y: x+y, s.all_stats, a.stats)
          a.totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[s.all_stats for s in a.sites])]
        else:
          a.totals = [SiteStats() for d in days]
      
        app_stats = SiteStats.stats_for_days(a,days)
        # TODO: Dedupe this by having an account level rollup
        ## assigns the user count of the app from the app stat rollup
        for stat,app_stat in zip(a.totals,app_stats):
          stat.unique_user_count = app_stat.unique_user_count        
          
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[a.totals for a in apps])]
      today = totals[-1]
      yesterday = totals[-2]

      chart_urls = {}
      # make a line graph showing impressions
      impressions = [s.impression_count for s in totals]
      chart_urls['imp'] = gen_chart_url(impressions, days, "Total+Daily+Impressions")
      
      # make a line graph showing clicks
      clicks = [s.click_count for s in totals]
      chart_urls['clk'] = gen_chart_url(clicks, days, "Total+Daily+Clicks")

      # make a line graph showing revenue
      revenue = [s.revenue for s in totals]
      chart_urls['rev'] = gen_chart_url(revenue, days, "Total+Revenue")
      
      # make a line graph showing users
      unique_users = [s.unique_user_count for s in totals]
      chart_urls['users'] = gen_chart_url(unique_users, days, "Total+Unique Users")

      # do a bar graph showing contribution of each site to impression count
      impressions_by_app = []
      clicks_by_app = []
      users_by_app = []
      pie_chart_urls = {}
      for a in apps:
        impressions_by_app.append({"app": a, "total": a.stats.impression_count})
        clicks_by_app.append({"app": a, "total": a.stats.click_count})
        users_by_app.append({"app": a, "total": a.stats.unique_user_count})
      impressions_by_app.sort(lambda x,y: cmp(y["total"], x["total"])) 
      clicks_by_app.sort(lambda x,y: cmp(y["total"], x["total"])) 
      users_by_app.sort(lambda x,y: cmp(y["total"], x["total"])) 
      pie_chart_urls['imp'] = gen_pie_chart_url(impressions_by_app, "Contribution+by+App")
      pie_chart_urls['clk'] = gen_pie_chart_url(clicks_by_app, "Contribution+by+App")
      pie_chart_urls['users'] = gen_pie_chart_url(users_by_app, "Contribution+by+App")

      return render_to_response(self.request,'publisher/index.html', 
        {'apps': apps,    
         'today': today,
         'yesterday': yesterday,
         'chart_urls': chart_urls,
         'pie_chart_urls': pie_chart_urls,
         'account': self.account})
    else:
      return HttpResponseRedirect(reverse('publisher_app_create'))

@whitelist_login_required     
def index(request,*args,**kwargs):
  # return HttpResponseRedirect(reverse('publisher_create'))
  return AppIndexHandler()(request,*args,**kwargs)     
  
class AppCreateHandler(RequestHandler):
  def get(self):
    f = AppForm()
    return render_to_response(self.request,'publisher/new_app.html', {"f": f})

  def post(self):
    f = AppForm(data=self.request.POST)
    if f.is_valid():
      app = f.save(commit=False)
      app.account = self.account
      app.put()
      return HttpResponseRedirect(reverse('publisher_app_show')+'?id=%s'%app.key())
    else:
      return render_to_response(self.request,'publisher/new_app.html', {"f": f})

@whitelist_login_required  
def app_create(request,*args,**kwargs):
  return AppCreateHandler()(request,*args,**kwargs)
    
class CreateAdUnitHandler(RequestHandler):
 def post(self):
    f = SiteForm(data=self.request.POST)
    a = App.get(self.request.POST.get('id'))
    if f.is_valid():
      site = f.save(commit=False)
      site.account = self.account
      site.app_key = a
      site.put()
      # Check if this is the first ad unit for this account
      if Site.gql("where account = :1 limit 2", self.account).count() == 1:
        add_demo_campaign(site)
      return HttpResponseRedirect(reverse('publisher_generate')+'?id=%s'%site.key())
    else:
      print f.errors

@whitelist_login_required  
def create(request,*args,**kwargs):
  return CreateAdUnitHandler()(request,*args,**kwargs)   

def add_demo_campaign(site):
  # Set up a test campaign that returns a demo ad
  c = Campaign(name="MoPub Demo Campaign",
               u=site.account.user,
               campaign_type="promo",
               description="Demo campaign for checking that MoPub works for your application")
  c.put()

  # Set up a test ad group for this campaign
  ag = AdGroup(name="MoPub Demo Ad Group",
               campaign=c,
               priority_level=3,
               bid=1.0,
               site_keys=[site.key()])
  ag.put()

  # And set up a default creative
  h = HtmlCreative(ad_type="html", ad_group=ag)
  h.put()
  
class ShowAppHandler(RequestHandler):
  def get(self):
    days = SiteStats.lastdays(14)
   
    # load the site
    a = App.get(self.request.GET.get('id'))
    if a.account.key() != self.account.key():
      self.error(404)
      return

    # load the ad units
    # TODO: This is duplicate code, move to separate function
    a.stats = SiteStats()
    today = SiteStats()
    a.sites = Site.gql("where app_key = :1 and deleted = :2", a, False).fetch(50)
    
    # organize impressions by days
    if len(a.sites) > 0:
      for s in a.sites:
        s.all_stats = SiteStats.sitestats_for_days(s, days)
        s.stats = reduce(lambda x, y: x+y, s.all_stats, SiteStats())
        a.stats = reduce(lambda x, y: x+y, s.all_stats, a.stats)
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[s.all_stats for s in a.sites])]
    else:
      totals = [SiteStats() for d in days]
      
    app_stats = SiteStats.stats_for_days(a,days)
    # set the apps unique user count from the app stats rollup
    for stat,app_stat in zip(totals,app_stats):
      stat.unique_user_count = app_stat.unique_user_count
      
    # today is the latest day  
    today = totals[-1] 
    yesterday = totals[-2] 
        
    chart_urls = {}
    # make a line graph showing impressions
    impressions = [s.impression_count for s in totals]
    chart_urls['imp'] = gen_chart_url(impressions, days, "Total+Daily+Impressions")
  
    # make a line graph showing clicks
    clicks = [s.click_count for s in totals]
    chart_urls['clk'] = gen_chart_url(clicks, days, "Total+Daily+Clicks")
  
    # make a line graph showing revenue
    revenue = [s.revenue for s in totals]
    chart_urls['rev'] = gen_chart_url(revenue, days, "Total+Revenue")
    
    # make a line graph showing users
    unique_users = [s.unique_user_count for s in totals]
    chart_urls['users'] = gen_chart_url(unique_users, days, "Total+Unique Users")
    

    # do a bar graph showing contribution of each site to impression count
    pie_chart_urls = {}
    if len(a.sites) > 0:
      impressions_by_site = []
      clicks_by_site = []
      users_by_site = []
      for s in a.sites:
        impressions_by_site.append({"app": s, "total": s.stats.impression_count})
        clicks_by_site.append({"app": s, "total": s.stats.click_count})
        users_by_site.append({"app": a, "total": s.stats.unique_user_count})
      impressions_by_site.sort(lambda x,y: cmp(y["total"], x["total"])) 
      clicks_by_site.sort(lambda x,y: cmp(y["total"], x["total"])) 
      users_by_site.sort(lambda x,y: cmp(y["total"], x["total"])) 
      pie_chart_urls['imp'] = gen_pie_chart_url(impressions_by_site, "Contribution+by+Ad+Unit")
      pie_chart_urls['clk'] = gen_pie_chart_url(clicks_by_site, "Contribution+by+Ad+Unit")
      pie_chart_urls['users'] = gen_pie_chart_url(users_by_site, "Contribution+by+Ad+Unit")
    else:
      pie_chart_urls['imp'] = ""
      pie_chart_urls['clk'] = ""

    help_text = 'Create an Ad Unit below' if len(a.sites) == 0 else None

    return render_to_response(self.request,'publisher/show_app.html', 
        {'app': a,    
         'today': today,
         'yesterday': yesterday,
         'chart_urls': chart_urls,
         'pie_chart_urls': pie_chart_urls,
         'account': self.account,
         'helptext': help_text})

    # write response
    return render_to_response(self.request,'publisher/show_app.html', {'app':app, 'sites':sites,
      'account':self.account})
  
@whitelist_login_required
def app_show(request,*args,**kwargs):
  return ShowAppHandler()(request,*args,**kwargs)   

class ShowHandler(RequestHandler):
  def get(self):
    # load the site
    site = Site.get(self.request.GET.get('id'))
    if site.account.key() != self.account.key():
      raise Http404

    # do all days requested
    days = SiteStats.lastdays(14)
    site.all_stats = SiteStats.sitestats_for_days(site, days)
    for i in range(len(days)):
      site.all_stats[i].date = days[i]

    site.stats = reduce(lambda x, y: x+y, site.all_stats, SiteStats())
    
    # Get all of the ad groups for this site
    site.adgroups = AdGroup.gql("where site_keys = :1", site.key()).fetch(50)
    for ag in site.adgroups:
      ag.all_stats = SiteStats.stats_for_days(ag, days)
      ag.stats = reduce(lambda x, y: x+y, ag.all_stats, SiteStats())
      
    # chart
    chart_urls = {}
    
    impressions = [s.impression_count for s in site.all_stats]
    chart_urls['imp'] = gen_chart_url(impressions, days, "Total+Daily+Impressions")
    
    # make a line graph showing clicks
    clicks = [s.click_count for s in site.all_stats]
    chart_urls['clk'] = gen_chart_url(clicks, days, "Total+Daily+Clicks")

    # make a line graph showing revenue
    revenue = [s.revenue for s in site.all_stats]
    chart_urls['rev'] = gen_chart_url(revenue, days, "Total+Revenue")
    
    # make a line graph showing users
    unique_users = [s.unique_user_count for s in site.all_stats]
    chart_urls['users'] = gen_chart_url(unique_users, days, "Total+Unique Users")

    # totals
    today = site.all_stats[-1]
    yesterday = site.all_stats[-2]
    
    # do a bar graph showing contribution of each site to impression count
    pie_chart_urls = {}
    
    if len(site.adgroups) > 0:
      impressions_by_ag = []
      clicks_by_ag = []
      users_by_ag = []
      for ag in site.adgroups:
        impressions_by_ag.append({"app": ag, "total": ag.stats.impression_count})
        clicks_by_ag.append({"app": ag, "total": ag.stats.click_count})
        users_by_ag.append({"app": ag, "total": ag.stats.unique_user_count})
      impressions_by_ag.sort(lambda x,y: cmp(y["total"], x["total"])) 
      clicks_by_ag.sort(lambda x,y: cmp(y["total"], x["total"])) 
      users_by_ag.sort(lambda x,y: cmp(y["total"], x["total"])) 
      pie_chart_urls['imp'] = gen_pie_chart_url(impressions_by_ag, "Contribution+by+Ad+Group")
      pie_chart_urls['clk'] = gen_pie_chart_url(clicks_by_ag, "Contribution+by+Ad+Group")
      pie_chart_urls['users'] = gen_pie_chart_url(users_by_ag, "Contribution+by+Ad+Group")
    else:
      pie_chart_urls['imp'] = ""
      pie_chart_urls['clk'] = ""
    
    # write response
    return render_to_response(self.request,'publisher/show.html', 
        {'site':site,
         'today': today,
         'yesterday': yesterday,
         'account':self.account, 
         'chart_urls': chart_urls,
         'pie_chart_urls': pie_chart_urls,
         'days': days})
  
@whitelist_login_required
def show(request,*args,**kwargs):
  return ShowHandler()(request,*args,**kwargs)   

class AppUpdateHandler(RequestHandler):
  def get(self):
    a = App.get(self.request.GET.get("id"))
    f = AppForm(instance=a)
    return render_to_response(self.request,'publisher/edit_app.html', {"f": f, "app": a})

  def post(self):
    a = App.get(self.request.GET.get('id'))
    f = AppForm(data=self.request.POST, instance=a)
    if a.account.user == self.account.user:
      f.save(commit=False)
      a.put()
    return HttpResponseRedirect(reverse('publisher_app_show')+'?id=%s'%a.key())
  

@whitelist_login_required
def app_update(request,*args,**kwargs):
  return AppUpdateHandler()(request,*args,**kwargs)   

class UpdateHandler(RequestHandler):
  def get(self):
    c = Site.get(self.request.GET.get("id"))
    f = SiteForm(instance=c)
    return render_to_response(self.request,'publisher/edit.html', {"f": f, "site": c})

  def post(self):
    s = Site.get(self.request.GET.get('id'))
    f = SiteForm(data=self.request.POST, instance=s)
    if s.account.user == self.account.user:
      f.save(commit=False)
      s.put()
    return HttpResponseRedirect(reverse('publisher_show')+'?id=%s'%s.key())
  
@whitelist_login_required
def update(request,*args,**kwargs):
  return UpdateHandler()(request,*args,**kwargs)   

class GetArtworkHandler(RequestHandler):
  def get(self):
    p = self.request.GET.get("app_type")
    url = self.request.GET.get("url")
    if (p == "iphone"):
      m = re.search('itunes.apple.com/.*/id(\d+)', url)
      if m:
        id = m.group(1)
        itunes_url = "http://ax.itunes.apple.com/WebObjects/MZStoreServices.woa/wa/wsLookup?id=" + id
        response = urllib.urlopen(itunes_url)
        return HttpResponse(response.read())

    return HttpResponse()

@whitelist_login_required
def getartwork(request,*args,**kwargs):
  return GetArtworkHandler()(request,*args,**kwargs)   
  
# Set up a new user with a default campaign
class GetStartedHandler(RequestHandler):
  def get(self):
    # Check if the user is in the data store and create it if not

    user = self.account.user
    u = Account.get_by_key_name(user.user_id())
    if not u:
      u = Account(key_name=user.user_id(),user=user)
      u.put()
      
    return HttpResponseRedirect(reverse('publisher_index'))

@whitelist_login_required
def getstarted(request,*args,**kwargs):
  return GetStartedHandler()(request,*args,**kwargs)   

class RemoveAdUnitHandler(RequestHandler):
  def post(self):
    ids = self.request.POST.getlist('id')
    for adunit_key in ids:
      a = Site.get(adunit_key)
      if a != None and a.app_key.account == self.account:
        a.deleted = True
        a.put()
    return HttpResponseRedirect(reverse('publisher_app_show') + '?id=%s' % a.app_key.key())
 
@whitelist_login_required
def adunit_delete(request,*args,**kwargs):
  return RemoveAdUnitHandler()(request,*args,**kwargs)
    

class GenerateHandler(RequestHandler):
  def get(self):
    site = Site.get(self.request.GET.get('id'))
    return render_to_response(self.request,'publisher/code.html', {'site': site})
  
@whitelist_login_required
def generate(request,*args,**kwargs):
  return GenerateHandler()(request,*args,**kwargs) 
