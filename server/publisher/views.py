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
    def __call__(self,request):
        self.params = request.POST or request.GET
        self.request = request
        if request.method == "GET":
            return self.get()
        elif request.method == "POST":
            return self.post()    
    def get(self):
        pass
    def put(self):
        pass    

class AppIndexHandler(RequestHandler):
  def get(self):
    # compute start times; start day before today so incomplete days don't mess up graphs
    today = datetime.date.today() - datetime.timedelta(days=1)
    begin_time = today - datetime.timedelta(days=14)
    days = [today - datetime.timedelta(days=x) for x in range(0, 14)]

    apps = App.gql("where account = :1", Account.current_account()).fetch(50)   
    if len(apps) > 0:    
      day_impressions = {}
      for app in apps:
        app.sites = []
        app.impression_count = 0
        app.click_count = 0
        sites = Site.gql("where app_key = :1", app).fetch(50)   
        # organize impressions by days
        for site in sites:
          stats = SiteStats.gql("where site = :1 and date >= :2", site, begin_time).fetch(100)
          site.stats = SiteStats()
          site.stats.impression_count = sum(map(lambda x: x.impression_count, stats))
          site.stats.click_count = sum(map(lambda x: x.click_count, stats))
          app.sites.append(site)
          app.impression_count += site.stats.impression_count
          app.click_count += site.stats.click_count

          # now aggregate it into days
          for stat in stats:
            day_impressions[stat.date] = (day_impressions.get(stat.date) or 0) + stat.impression_count
        app.ctr = float(app.click_count) / float(app.impression_count) if app.impression_count > 0 else 0

      # organize the info on a day by day basis across all sites
      series = [day_impressions.get(a,0) for a in days]
      series.reverse()
      url = "http://chart.apis.google.com/chart?cht=lc&chtt=Total+Daily+Impressions&chs=580x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
        ','.join(map(lambda x: str(x), series)),
        max(series) * 1.5,
        max(series) * 1.5,
        '|'.join(map(lambda x: x.strftime("%m/%d"), days)))

      # do a bar graph showing contribution of each site to impression count
      total_impressions_by_app = []
      for app in apps:
        total_impressions_by_app.append({"app": app, "total": app.impression_count})
      total_impressions_by_app.sort(lambda x,y: cmp(y["total"], x["total"])) 
      bar_chart_url = "http://chart.apis.google.com/chart?cht=p&chtt=Contribution+by+Placement&chs=200x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chl=&chdlp=b&chdl=%s" % (
         ','.join(map(lambda x: str(x["total"]), total_impressions_by_app)),
         max(map(lambda x: x.impression_count, apps)) * 1.5,
         max(map(lambda x: x.impression_count, apps)) * 1.5,
         '|'.join(map(lambda x: x["app"].name, total_impressions_by_app[0:2])))

      return render_to_response(self.request,'apps_index.html', 
        {'apps': apps,    
         'chart_url': url,
         'bar_chart_url': bar_chart_url,
         'account': Account.current_account()})
    else:
      return HttpResponseRedirect(reverse('publisher_app_create'))

@whitelist_login_required     
def index(request,*args,**kwargs):
  # return HttpResponseRedirect(reverse('publisher_create'))
  return AppIndexHandler()(request,*args,**kwargs)     
  
class IndexHandler(RequestHandler):
  def get(self):
    # compute start times; start day before today so incomplete days don't mess up graphs
    today = datetime.date.today() - datetime.timedelta(days=1)
    begin_time = today - datetime.timedelta(days=14)
    days = [today - datetime.timedelta(days=x) for x in range(0, 14)]

    # gather aggregate data into each site
    sites = Site.gql("where account = :1", Account.current_account()).fetch(50)   
    if len(sites) > 0:    
      # organize impressions by days
      day_impressions = {}
      for site in sites:
        stats = SiteStats.gql("where site = :1 and date >= :2", site, begin_time).fetch(100)
        site.stats = SiteStats()
        site.stats.impression_count = sum(map(lambda x: x.impression_count, stats))
        site.stats.click_count = sum(map(lambda x: x.click_count, stats))

        # now aggregate it into days
        for stat in stats:
          day_impressions[stat.date] = (day_impressions.get(stat.date) or 0) + stat.impression_count

      # organize the info on a day by day basis across all sites
      series = [day_impressions.get(a,0) for a in days]
      series.reverse()
      url = "http://chart.apis.google.com/chart?cht=lc&chtt=Total+Daily+Impressions&chs=580x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
         ','.join(map(lambda x: str(x), series)),
         max(series) * 1.5,
         max(series) * 1.5,
         '|'.join(map(lambda x: x.strftime("%m/%d"), days)))

      # do a bar graph showing contribution of each site to impression count
      total_impressions_by_site = []
      for site in sites:
        total_impressions_by_site.append({"site": site, "total": site.stats.impression_count})
      total_impressions_by_site.sort(lambda x,y: cmp(y["total"], x["total"])) 
      bar_chart_url = "http://chart.apis.google.com/chart?cht=p&chtt=Contribution+by+Placement&chs=200x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chl=&chdlp=b&chdl=%s" % (
         ','.join(map(lambda x: str(x["total"]), total_impressions_by_site)),
         max(map(lambda x: x.stats.impression_count, sites)) * 1.5,
         max(map(lambda x: x.stats.impression_count, sites)) * 1.5,
         '|'.join(map(lambda x: x["site"].name, total_impressions_by_site[0:2])))

      # stats
      return render_to_response(self.request,'index.html', 
        {'sites': sites,    
         'chart_url': url,
         'bar_chart_url': bar_chart_url,
         'account': Account.current_account()})
    else:
      return HttpResponseRedirect(reverse('publisher_create'))

@whitelist_login_required     
def adunits_index(request,*args,**kwargs):
  # return HttpResponseRedirect(reverse('publisher_create'))
  return IndexHandler()(request,*args,**kwargs)     

class AppCreateHandler(RequestHandler):
  def get(self):
    f = AppForm()
    return render_to_response(self.request,'new_app.html', {"f": f})

  def post(self):
    f = AppForm(data=self.request.POST)
    if f.is_valid():
      app = f.save(commit=False)
      app.account = Account.current_account()
      app.put()
      return HttpResponseRedirect(reverse('publisher_app_show')+'?id=%s'%app.key())
    else:
      return render_to_response(self.request,'new_app.html', {"f": f})

@whitelist_login_required  
def app_create(request,*args,**kwargs):
  return AppCreateHandler()(request,*args,**kwargs)
    
class CreateAdUnitHandler(RequestHandler):
 def post(self):
    f = SiteForm(data=self.request.POST)
    a = App.get(self.request.POST.get('id'))
    if f.is_valid():
      site = f.save(commit=False)
      site.account = Account.current_account()
      site.app_key = a
      site.put()
      return HttpResponseRedirect(reverse('publisher_generate')+'?id=%s'%site.key())
    else:
      print f.errors

@whitelist_login_required  
def create(request,*args,**kwargs):
  return CreateAdUnitHandler()(request,*args,**kwargs)   

class ShowAppHandler(RequestHandler):
  def get(self):
    # load the site
    app = App.get(self.request.GET.get('id'))
    if app.account.key() != Account.current_account().key():
      self.error(404)
      return

    # load the ad units
    sites = Site.gql("where app_key=:1", app).fetch(50)

    # write response
    return render_to_response(self.request,'show_app.html', {'app':app, 'sites':sites,
      'account':Account.current_account()})
  
@whitelist_login_required
def app_show(request,*args,**kwargs):
  return ShowAppHandler()(request,*args,**kwargs)   

class ShowHandler(RequestHandler):
  def get(self):
    # load the site
    site = Site.get(self.request.GET.get('id'))
    if site.account.key() != Account.current_account().key():
      self.error(404)
      return

    # do all days requested
    today = datetime.date.today() - datetime.timedelta(days=1)
    stats = []
    for x in range(0, 14):
      a = today - datetime.timedelta(days=x)
      stats.append(SiteStats.gql("where site = :1 and date = :2", site, a).get() or SiteStats(site = site, date = a))

    # chart
    stats.reverse()
    url = "http://chart.apis.google.com/chart?cht=lc&chs=800x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
       ','.join(map(lambda x: str(x.impression_count), stats)), 
       max(map(lambda x: x.impression_count, stats)) * 1.5,
       max(map(lambda x: x.impression_count, stats)) * 1.5,
       '|'.join(map(lambda x: x.date.strftime("%m/%d"), stats)))

    # totals
    impression_count = sum(map(lambda x: x.impression_count, stats))
    click_count = sum(map(lambda x: x.click_count, stats))
    ctr = float(click_count) / float(impression_count) if impression_count > 0 else 0

    # write response
    return render_to_response(self.request,'show.html', {'site':site, 
      'impression_count': impression_count, 'click_count': click_count, 'ctr': ctr,
      'account':Account.current_account(), 
      'chart_url': url,
      'stats':stats})
  
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
    if a.account.user == users.get_current_user():
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
    if s.account.user == users.get_current_user():
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

    user = users.get_current_user()
    u = Account.get_by_key_name(user.user_id())
    if not u:
      u = Account(key_name=user.user_id(),user=user)
      u.put()

      logging.debug('oh hai')
      # Set up a test campaign that returns a demo ad
      c = Campaign(name="MoPub Test Campaign",
                   u=user,
                   campaign_type="promo",
                   description="Test campaign for checking the mopub works in your application")
      c.put()

      # Set up a test ad group for this campaign
      ag = AdGroup(name="MoPub Test Ad Group", campaign=c)
      ag.put()

      # And set up a default creative
      h = HtmlCreative(ad_type="html", ad_group=ag)
      h.put()
      
    return HttpResponseRedirect(reverse('publisher_index'))

@login_required
def getstarted(request,*args,**kwargs):
  return GetStartedHandler()(request,*args,**kwargs)   

class GenerateHandler(RequestHandler):
  def get(self):
    site = Site.get(self.request.GET.get('id'))
    return render_to_response(self.request,'code.html', {'site': site})
  
@whitelist_login_required
def generate(request,*args,**kwargs):
  return GenerateHandler()(request,*args,**kwargs) 
