import base64
import binascii
import hashlib
import logging
import math
import os
import re

from datetime import (datetime,
                      time,
                      date,
                      )

import urllib
# hack to get urllib to work on snow leopard
urllib.getproxies_macosx_sysconf = lambda: {}

from urllib import urlencode
from operator import itemgetter


from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
# from google.appengine.ext.db import djangoforms
# from common.utils import djangoforms
from google.appengine.api import images

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required

## Models
from advertiser.models import Campaign, AdGroup, HtmlCreative
from publisher.models import Site, Account, App
from publisher.forms import SiteForm, AppForm, AdUnitForm
from reporting.models import StatsModel, GEO_COUNTS

## Query Managers
from account.query_managers import AccountQueryManager
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, \
                                      CreativeQueryManager
from common.utils.query_managers import CachedQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager, AdUnitContextQueryManager
from reporting.query_managers import StatsModelQueryManager

from common.utils import sswriter
from common.utils.request_handler import RequestHandler
from common.constants import *


class AppIndexHandler(RequestHandler):
  def get(self):
    report = self.request.POST.get('report')
    
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = StatsModel.get_days(self.start_date, self.date_range)
    else:
      days = StatsModel.lastdays(self.date_range)

    apps = AppQueryManager.get_apps(self.account)
    if len(apps) == 0:
      return HttpResponseRedirect(reverse('publisher_app_create'))

    for app in apps:
      if app.icon:
        app.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(app.icon)

      # attaching adunits onto the app object
      app.adunits = AdUnitQueryManager.get_adunits(app=app)

      # organize impressions by days
      for adunit in app.adunits:
        adunit.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=adunit,days=days)

        # sum of stats for this date range
        adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, StatsModel())

      app.adunits = sorted(app.adunits, key=lambda adunit: adunit.stats.request_count, reverse=True)

      # We have to read the datastore at the app level since we need to get the de-duped user_count
      app.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=app,days=days)
      app.stats = reduce(lambda x, y: x+y, app.all_stats, StatsModel())

    apps = sorted(apps, key=lambda app: app.stats.request_count, reverse=True)

    totals_list = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(days=days)
    
    today = totals_list[-1]
    yesterday = totals_list[-2]
    totals = reduce(lambda x, y: x+y, totals_list, StatsModel())
    # this is the max active users over the date range
    # NOT total unique users
    totals.user_count = max([t.user_count for t in totals_list])
    
    logging.warning("ACCOUNT: %s"%self.account.key())
    logging.warning("YESTERDAY: %s"%yesterday.key())
    logging.warning("TODAY: %s"%today.key())

    # In the graph, only show the top 3 apps and bundle the rest if there are more than 4
    graph_apps = apps[0:4]
    if len(apps) > 4:
      graph_apps[3] = App(name='Others')
      graph_apps[3].all_stats = [reduce(lambda x, y: x+y, stats, StatsModel()) for stats in zip(*[a.all_stats for a in apps[3:]])]

    return render_to_response(self.request,'publisher/index.html', 
      {'apps': apps,
       'graph_apps': graph_apps,
       'start_date': days[0],
       'date_range': self.date_range,
       'today': today,
       'yesterday': yesterday,
       'totals': totals,
       'account': self.account})

@whitelist_login_required     
def index(request,*args,**kwargs):
  return AppIndexHandler()(request,*args,**kwargs)     

class AppIndexGeoHandler(RequestHandler):
  def get(self):
    # compute start times; start day before today so incomplete days don't mess up graphs

    if self.start_date:
      days = StatsModel.get_days(self.start_date, self.date_range)
    else:
      days = StatsModel.lastdays(self.date_range)

    now = datetime.now()
    
    apps = AppQueryManager.get_apps(self.account)
    
    if len(apps) == 0:
      return HttpResponseRedirect(reverse('publisher_app_create'))

    geo_dict = {}
    totals = StatsModel(date=now) # sum across all days and countries
    
    # hydrate geo count dicts with stats counts on account level
    all_stats = StatsModelQueryManager(self.account,self.offline).get_stats_for_days(days=days) 
    for stats in all_stats:
      totals = totals + StatsModel(request_count=stats.request_count, 
                                   impression_count=stats.impression_count, 
                                   click_count=stats.click_count, 
                                   user_count=stats.user_count,
                                   date=now)                                   
      countries = stats.get_countries()
      for c in countries:
        geo_dict[c] = geo_dict.get(c, StatsModel(country=c, date=now)) + \
                        StatsModel(country=c,  
                                   request_count=stats.get_geo(c, GEO_COUNTS[0]), 
                                   impression_count=stats.get_geo(c, GEO_COUNTS[1]), 
                                   click_count=stats.get_geo(c, GEO_COUNTS[2]), 
                                   date=now)
    
    # creates a sorted table based on request count 
    geo_table = []
    keys = geo_dict.keys()
    keys.sort(lambda x,y: cmp(geo_dict[y].request_count, geo_dict[x].request_count))
    for k in keys:
      geo_table.append((k, geo_dict[k]))
    
    # create copy of geo_dict with counts on log scale
    geo_log_dict = {}
    for c, stats in geo_dict.iteritems():
      geo_log_dict[c] = StatsModel(country=c,
                                   # check to see if count is 0 since log 0 is invalid; +0.5 at the end for rounding
                                   request_count=int(math.log10(stats.request_count if stats.request_count > 0 else 1) + 0.5), 
                                   impression_count=int(math.log10(stats.impression_count if stats.impression_count > 0 else 1) + 0.5),
                                   click_count=int(math.log10(stats.click_count if stats.click_count > 0 else 1) + 0.5),
                                   date=now)
    
    return render_to_response(self.request, 'publisher/index_geo.html', 
      {'geo_dict': geo_dict,
       'geo_log_dict': geo_log_dict,
       'geo_table': geo_table,
       'totals' : totals,
       'date_range': self.date_range,
       'account': self.account})

@whitelist_login_required     
def index_geo(request,*args,**kwargs):
  return AppIndexGeoHandler()(request,*args,**kwargs)     

class AppCreateHandler(RequestHandler):
  def get(self, app_form=None,adunit_form=None):
    app_form = app_form or AppForm()
    adunit_form = adunit_form or AdUnitForm(prefix="adunit")
    return render_to_response(self.request,'publisher/new_app.html', {"app_form": app_form, 
                                                                      "adunit_form":adunit_form,  
                                                                      "account": self.account})

  def post(self):
    app = None
    if self.request.POST.get("app_key"):
      app = AppQueryManager.get(self.request.POST.get("app_key"))
      app_form = AppForm(data=self.request.POST, files = self.request.FILES, instance=app)
    else:
      app_form = AppForm(data=self.request.POST, files = self.request.FILES )
      
    adunit_form = AdUnitForm(data=self.request.POST, prefix="adunit")
      
    if app_form.is_valid():
      app = app_form.save(commit=False)
      app.account = self.account # attach account info


      # Nafis: Took this away b/c this page both things need to be valid before continuing
      # If we get the adunit information, try to create that too
      # if not self.request.POST.get("adunit_name"):
      #   return HttpResponseRedirect(reverse('publisher_app_show',kwargs={'app_key':app.key()}))
      
      if adunit_form.is_valid():
        adunit = adunit_form.save(commit=False)
        adunit.account = self.account

        # update the database
        AppQueryManager.put(app)
        
        adunit.app_key = app
        
        AdUnitQueryManager.put(adunit)

        # update the cache as necessary 
        # replace=True means don't do anything if not already in the cache
        AdUnitContextQueryManager.cache_delete_from_adunits(adunit)

        # Check if this is the first ad unit for this account
        if len(AdUnitQueryManager.get_adunits(account=self.account,limit=2)) == 1:      
          add_demo_campaign(adunit)
        # Check if this is the first app for this account
        status = "success"
        if self.account.status == "new":
          self.account.status = "step3"  # skip setting 'step2' since the step 2 page is only displayed once
          AccountQueryManager().put_accounts(self.account)
          status = "welcome"
        return HttpResponseRedirect(reverse('publisher_generate',kwargs={'adunit_key':adunit.key()})+'?status='+status)
    return self.get(app_form,adunit_form)

@whitelist_login_required  
def app_create(request,*args,**kwargs):
  return AppCreateHandler()(request,*args,**kwargs)
    
class CreateAdUnitHandler(RequestHandler):
 def post(self):
    f = SiteForm(data=self.request.POST)
    a = AppQueryManager.get(self.request.POST.get('id'))
    if f.is_valid():
      adunit = f.save(commit=False)
      adunit.account = self.account
      adunit.app_key = a
      
      # update the database
      AdUnitQueryManager.put(adunit)
      
      # update the cache as necessary 
      # replace=True means don't do anything if not already in the cache
      AdUnitContextQueryManager.cache_delete_from_adunits(adunit)
      
      # Check if this is the first ad unit for this account
      # if Site.gql("where account = :1 limit 2", self.account).count() == 1:
      if len(AdUnitQueryManager.get_adunits(account=self.account,limit=2)) == 1:      
        add_demo_campaign(adunit)
      return HttpResponseRedirect(reverse('publisher_generate',kwargs={'adunit_key':adunit.key()})+'?status=success')
    else:
      print f.errors

@whitelist_login_required  
def adunit_create(request,*args,**kwargs):
  return CreateAdUnitHandler()(request,*args,**kwargs)   

def add_demo_campaign(site):
    # Set up a test campaign that returns a demo ad
    c = Campaign(name="MoPub Demo Campaign",
                 u=site.account.user,
                 account=site.account,
                 campaign_type="promo",
                 description="Demo campaign for checking that MoPub works for your application")
    CampaignQueryManager.put(c)

    # Set up a test ad group for this campaign
    ag = AdGroup(name="MoPub Demo Campaign",
                 campaign=c,
                 account=site.account,
                 priority_level=3,
                 bid=1.0,
                 site_keys=[site.key()])
    AdGroupQueryManager.put(ag)

    # And set up a default creative
    h = HtmlCreative(ad_type="html",
                     ad_group=ag,
                     account=site.account,
                     format=site.format,
                     name="Demo HTML Creative",
                     html_data="<style type=\"text/css\">body {font-size: 12px;font-family:helvetica,arial,sans-serif;margin:0;padding:0;text-align:center;background:white} .creative_headline {font-size: 18px;} .creative_promo {color: green;text-decoration: none;}</style><div class=\"creative_headline\">Welcome to mopub!</div><div class=\"creative_promo\"><a href=\"http://www.mopub.com\">Click here to test ad</a></div><div>You can now set up a new campaign to serve other ads.</div>")
    CreativeQueryManager.put(h)
  
class ShowAppHandler(RequestHandler):
  def get(self,app_key):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = StatsModel.get_days(self.start_date, self.date_range)
    else:
      days = StatsModel.lastdays(self.date_range)

    # load the site
    a = AppQueryManager.get(app_key)
    
    # check to see that the user has viewership rights, ow return 404
    if a.account.key() != self.account.key():
      raise Http404

    a.adunits = AdUnitQueryManager.get_adunits(app=a)
    
    # organize impressions by days
    if len(a.adunits) > 0:
      for adunit in a.adunits:
        adunit.all_stats = StatsModelQueryManager(self.account,self.offline).get_stats_for_days(publisher=adunit,days=days)
        adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, StatsModel())
      
    a.adunits = sorted(a.adunits, key=lambda adunit: adunit.stats.request_count, reverse=True)
      
    app_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=a,days=days)

    help_text = 'Create an Ad Unit below' if len(a.adunits) == 0 else None
    
    if a.icon:
      a.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(a.icon)

    # In the graph, only show the top 3 ad units and bundle the rest if there are more than 4
    a.graph_adunits = a.adunits[0:4]
    if len(a.adunits) > 4:
      a.graph_adunits[3] = Site(name='Others')
      a.graph_adunits[3].all_stats = [reduce(lambda x, y: x+y, stats, StatsModel()) for stats in zip(*[au.all_stats for au in a.adunits[3:]])]
    # in order to make the app editable
    app_form_fragment = AppUpdateAJAXHandler(self.request).get(app=a)
    # in order to have a creat adunit form
    adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(app=a)
    
    today = app_stats[-1]
    yesterday = app_stats[-2]
    a.stats = reduce(lambda x, y: x+y, app_stats, StatsModel())
    # this is the max active users over the date range
    # NOT total unique users
    a.stats.user_count = max([sm.user_count for sm in app_stats])

    return render_to_response(self.request,'publisher/show_app.html', 
        {'app': a,  
         'app_form_fragment':app_form_fragment,
         'adunit_form_fragment':adunit_form_fragment,
         'start_date': days[0],
         'date_range': self.date_range,
         'today': today,
         'yesterday': yesterday,
         'account': self.account,
         'helptext': help_text})
         

@whitelist_login_required
def app_show(request,*args,**kwargs):
  return ShowAppHandler()(request,*args,**kwargs)   


class ExportFileHandler( RequestHandler ):
    def get( self, key, key_type, f_type ):
        #XXX make sure this is the right way to do it 
        spec = self.params.get('spec') 
        if self.start_date:
            days = StatsModel.get_days( self.start_date, self.date_range )
        else:
            days = StatsModel.lastdays( self.date_range )

        stat_names, stat_models = self.get_desired_stats(key, key_type, days, spec=spec)
        logging.warning(stat_models)
        logging.warning("\n\nDays len:%s\nStats len:%s\n\n" % (len(days),len(stat_models)))
        return sswriter.write_stats( f_type, stat_names, stat_models, site=key, days=days, key_type=key_type )


    def get_desired_stats(self, key, key_type, days, spec=None):
        manager = StatsModelQueryManager(self.account, offline=self.offline)
        """ Given a key, key_type, and specificity, return 
        the appropriate stats to get AND their names"""
        #default for all
        stat_names = (IMP_STAT, CLK_STAT, CTR_STAT)
        #sanity check
        assert key_type in ('adunit', 'app', 'adgroup', 'account')
        if spec:
            assert spec in ('creatives', 'adunits', 'campaigns', 'days', 'apps')



        #Set up attr getters/names
        if key_type == 'app' or (key_type == 'account' and spec == 'apps') or (key_type == 'adunit' and spec == 'days'): 
            stat_names = (REQ_STAT,) + stat_names
            if spec == 'days':
                stat_names = (DTE_STAT,) + stat_names
        elif key_type == 'account' and spec == 'campaigns':
            stat_names += (CPM_STAT, CNV_RATE_STAT, CPA_STAT)
        elif key_type == 'adgroup':
            if spec == 'days':
                stat_names = (DTE_STAT,) + stat_names
            stat_names += (REV_STAT, CNV_RATE_STAT, CPA_STAT)
        elif key_type == 'adunit' and spec == 'campaigns':
            stat_names += (REV_STAT,)



        #General rollups for all data
        if key_type == 'account':
            if spec == 'apps':
                apps = AppQueryManager.get_apps(self.account)
                if len(apps) == 0:
                    #should probably handle this more gracefully
                    logging.warning("Apps for account is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(publisher=a, days=days) for a in apps]) 
            elif spec == 'campaigns':
                camps = CampaignQueryManager.get_campaigns(account=self.account)
                if len(camps) == 0:
                    logging.warning("Campaigns for account is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=c, days=days) for c in camps])
        #Rollups for adgroup data
        elif key_type == 'adgroup':
            if spec == 'creatives':
                creatives = list(CreativeQueryManager.get_creatives(adgroup=key))
                if len(creatives) == 0:
                    logging.warning("Creatives for adgroup is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=c, days=days) for c in creatives])
            if spec == 'adunits':
                adunits = map(lambda x: Site.get(x), AdGroupQueryManager.get(key).site_keys)
                if len(adunits) == 0:
                    logging.warning("Adunits for adgroup is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(advertiser=key, publisher=a, days=days) for a in adunits]) 
            if spec == 'days':
                return (stat_names, manager.get_stats_for_days(advertiser=key, days=days))
        #Rollups + not-rollup for adunit data            
        elif key_type == 'adunit':
            if spec == 'campaigns':
                adgroups = AdGroupQueryManager.get_adgroups(adunit=key)
                if len(adgroups) == 0:
                    logging.warning("Campaigns for adunit is empty")
                return (stat_names, [manager.get_stat_rollup_for_days(publisher=key, advertiser=a, days=days) for a in adgroups])
            if spec == 'days':
                return (stat_names, manager.get_stats_for_days(publisher=key, days=days))
        #App adunit rollup data
        elif key_type == 'app':
            adunits = AdUnitQueryManager.get_adunits(app=key)
            if len(adunits) == 0:
                logging.warning("Apps is empty")
            return (stat_name, [manager.get_stat_rollup_for_days(publisher=a, days=days) for a in adunits])


@whitelist_login_required
def export_file( request, *args, **kwargs ):
    return ExportFileHandler()( request, *args, **kwargs )

            

class AdUnitShowHandler(RequestHandler):
  def get(self,adunit_key):
    # load the site
    adunit = AdUnitQueryManager.get(adunit_key)
    if adunit.account.key() != adunit.account.key():
      raise Http404
      
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = StatsModel.get_days(self.start_date, self.date_range)
    else:
      days = StatsModel.lastdays(self.date_range)
    days = [day if type(day) == datetime else datetime.combine(day, time()) for day in days] 
    
    adunit.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=adunit,days=days)
    #XXX Wat?
    for i in range(len(days)):
      adunit.all_stats[i].date = days[i]

    adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, StatsModel())

    # Get all of the ad groups for this site
    adunit.adgroups = AdGroupQueryManager.get_adgroups(adunit=adunit)
    adunit.adgroups = sorted(adunit.adgroups, lambda x,y: cmp(y.bid, x.bid))
    for ag in adunit.adgroups:
      ag.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=adunit,advertiser=ag,days=days)
      ag.stats = reduce(lambda x, y: x+y, ag.all_stats, StatsModel())
    
    # to allow the adunit to be edited
    adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(adunit=adunit)
    
      
    # write response
    return render_to_response(self.request,'publisher/show.html', 
        {'site':adunit,
         'adunit':adunit,
         'today': adunit.all_stats[-1],
         'yesterday': adunit.all_stats[-2],
         'start_date': days[0],
         'date_range': self.date_range,
         'account':self.account, 
         'days': days,
         'adunit_form_fragment':adunit_form_fragment})
  
@whitelist_login_required
def adunit_show(request,*args,**kwargs):
  return AdUnitShowHandler()(request,*args,**kwargs)   

class AppUpdateAJAXHandler(RequestHandler):
  TEMPLATE  = 'publisher/forms/app_form.html'
  def get(self,app_form=None,app=None):
    app_form = app_form or AppForm(instance=app)

    return self.render(form=app_form)

  def render(self,template=None,**kwargs):
    template_name = template or self.TEMPLATE
    return render_to_string(self.request,template_name=template_name,data=kwargs)

  def json_response(self,json_dict):
    return JSONResponse(json_dict)

  def post(self,app_key=None):
    app_key = app_key or self.request.POST.get('app_key')
    if app_key:
      app = AppQueryManager.get(app_key)
    else:
      app = None

    app_form = AppForm(data=self.request.POST, files = self.request.FILES, instance=app)

    json_dict = {'success':False,'html':None}

    if app_form.is_valid():
      app = app_form.save(commit=False)
      app.account = self.account
      AppQueryManager.put(app)
      
      json_dict.update(success=True)
      
      # Delete related adunit contexts from memcache
      adunits = AdUnitQueryManager.get_adunits(app=app)
      AdUnitContextQueryManager.cache_delete_from_adunits(adunits)
      
      return self.json_response(json_dict)
    new_html = self.get(app_form=app_form)
    json_dict.update(success=False,html=new_html)    
    return self.json_response(json_dict)  

@whitelist_login_required
def app_update_ajax(request,*args,**kwargs):
  return AppUpdateAJAXHandler()(request,*args,**kwargs)   

class AdUnitUpdateAJAXHandler(RequestHandler):
  TEMPLATE  = 'publisher/forms/adunit_form.html'
  def get(self,adunit_form=None,adunit=None,app=None):
    initial = {}
    if app:
      initial.update(app_key=app.key())
    adunit_form = adunit_form or AdUnitForm(instance=adunit,initial=initial, prefix="adunit")
    return self.render(form=adunit_form)

  def render(self,template=None,**kwargs):
    template_name = template or self.TEMPLATE
    return render_to_string(self.request,template_name=template_name,data=kwargs)

  def json_response(self,json_dict):
    return JSONResponse(json_dict)

  def post(self,adunit_key=None):
    adunit_key = adunit_key or self.request.POST.get('adunit_key')
    if adunit_key:
      adunit = AdUnitQueryManager.get(adunit_key) # Note this gets things from the cache ?
    else:
      adunit = None

    adunit_form = AdUnitForm(data=self.request.POST,instance=adunit, prefix="adunit")
    json_dict = {'success':False,'html':None}

    if adunit_form.is_valid():
      adunit = adunit_form.save(commit=False)
      adunit.account = self.account
      AdUnitQueryManager.put(adunit)
      
      AdUnitContextQueryManager.cache_delete_from_adunits(adunit)
      
      json_dict.update(success=True)
      return self.json_response(json_dict)
    new_html = self.get(adunit_form=adunit_form)
    json_dict.update(success=False,html=new_html)    
    return self.json_response(json_dict)  

def adunit_update_ajax(request,*args,**kwargs):
  return AdUnitUpdateAJAXHandler()(request,*args,**kwargs)

class AppIconHandler(RequestHandler):
  def get(self, app_key):
    a = App.get(app_key)
    if a.icon:
      response = HttpResponse(a.icon)
      response['Content-Type'] = 'image/png'
      return response
    else:
      return HttpResponseRedirect('/images/misc/appicon-missing.png')

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
      a = AdUnitQueryManager.get(adunit_key)
      if a != None and a.app_key.account == self.account:
        a.deleted = True
        AdUnitQueryManager.put(a)
        # delete from cache
        # CachedQueryManager().cache_delete(a)
        AdUnitContextQueryManager.cache_delete_from_adunits(a)
        
    return HttpResponseRedirect(reverse('publisher_app_show','app_key',a.app_key.key()))
 
@whitelist_login_required
def adunit_delete(request,*args,**kwargs):
  return RemoveAdUnitHandler()(request,*args,**kwargs)

class GenerateHandler(RequestHandler):
  def get(self,adunit_key):
    adunit = AdUnitQueryManager.get(adunit_key)
    status = self.params.get('status')
    return render_to_response(self.request,'publisher/code.html', {'site': adunit, 'status': status, 'account': self.account})
  
@whitelist_login_required
def generate(request,*args,**kwargs):
  return GenerateHandler()(request,*args,**kwargs) 
