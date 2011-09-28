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

## Models
from advertiser.models import Campaign, AdGroup, HtmlCreative
from publisher.models import Site, Account, App
from publisher.forms import AppForm, AdUnitForm
from reporting.models import StatsModel, GEO_COUNTS

## Query Managers
from account.query_managers import AccountQueryManager
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, \
                                      CreativeQueryManager
from common.utils.query_managers import CachedQueryManager
from publisher.query_managers import AppQueryManager, AdUnitQueryManager, AdUnitContextQueryManager
from reporting.query_managers import StatsModelQueryManager

from common.utils import sswriter, date_magic
from common.utils.helpers import app_stats
from common.utils.request_handler import RequestHandler
from common.constants import *
from budget import budget_service

from common.utils.decorators import cache_page_until_post

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
      app.adunits = sorted(AdUnitQueryManager.get_adunits(app=app), key=lambda adunit:adunit.name)

    apps = sorted(apps, key=lambda app: app.name)

    totals_list = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(days=days)

    today = totals_list[-1]
    try:
        yesterday = totals_list[-2]
    except IndexError:
        yesterday = StatsModel()
    totals = reduce(lambda x, y: x+y, totals_list, StatsModel())
    # this is the max active users over the date range
    # NOT total unique users
    totals.user_count = max([t.user_count for t in totals_list])

    # prepare account_stats object
    key = "||"
    stats_dict = {}
    stats_dict[key] = {}
    stats_dict[key]['name'] = "||"
    stats_dict[key]['daily_stats'] = [s.to_dict() for s in totals_list]
    summed_stats = sum(totals_list, StatsModel())
    stats_dict[key]['sum'] = summed_stats.to_dict()

    response_dict = {}
    response_dict['status'] = 200
    response_dict['all_stats'] = stats_dict

    logging.warning("ACCOUNT: %s"%self.account.key())
    logging.warning("YESTERDAY: %s"%yesterday.key())
    logging.warning("TODAY: %s"%today.key())

    return render_to_response(self.request,'publisher/index.html',
      {'apps': apps,
       'account_stats': simplejson.dumps(response_dict),
       'start_date': days[0],
       'end_date': days[-1],
       'date_range': self.date_range,
       'today': today,
       'yesterday': yesterday,
       'totals': totals,
       'account': self.account})

@login_required
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
    all_stats = StatsModelQueryManager(self.account,self.offline,include_geo=True).get_stats_for_days(days=days)
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

@login_required
def index_geo(request,*args,**kwargs):
  return AppIndexGeoHandler()(request,*args,**kwargs)

class AppCreateHandler(RequestHandler):
  def get(self, app_form=None,adunit_form=None,reg_complete=None):
    app_form = app_form or AppForm()
    adunit_form = adunit_form or AdUnitForm(prefix="adunit")

    # attach on registration related parameters to the account for template
    if reg_complete:
        self.account.reg_complete = 1

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
      if not app_form.instance: #ensure form posts do not change ownership
        account = self.account  # attach account info
      else:
        account = app_form.instance.account
      app = app_form.save(commit=False)
      app.account = account

      # Nafis: Took this away b/c this page both things need to be valid before continuing
      # If we get the adunit information, try to create that too
      # if not self.request.POST.get("adunit_name"):
      #   return HttpResponseRedirect(reverse('publisher_app_show',kwargs={'app_key':app.key()}))

    if adunit_form.is_valid():
        if not adunit_form.instance: #ensure form posts do not change ownership
          account = self.account
        else:
          account = adunit_form.instance.account
        adunit = adunit_form.save(commit=False)
        adunit.account = account

        # update the database
        AppQueryManager.put(app)

        adunit.app_key = app

        AdUnitQueryManager.put(adunit)

        # Check if this is the first ad unit for this account
        if len(AdUnitQueryManager.get_adunits(account=self.account,limit=2)) == 1:
          add_demo_campaign(adunit)
        # Check if this is the first app for this account
        status = "success"
        if self.account.status == "new":
          self.account.status = "step4"  # skip to step 4 (add campaigns), but show step 2 (integrate)
          AccountQueryManager.put_accounts(self.account)
          status = "welcome"
        return HttpResponseRedirect(reverse('publisher_generate',kwargs={'adunit_key':adunit.key()})+'?status='+status)
    return self.get(app_form,adunit_form)

@login_required
def app_create(request,*args,**kwargs):
  return AppCreateHandler()(request,*args,**kwargs)

class CreateAdUnitHandler(RequestHandler):
 def post(self):
    f = AdUnitForm(data=self.request.POST)
    a = AppQueryManager.get(self.request.POST.get('id'))
    if f.is_valid():
      if not f.instance: #ensure form posts do not change ownership
        account = self.account
      else:
        acccount = f.instance.account
      adunit = f.save(commit=False)
      acunit.account = account
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

@login_required
def adunit_create(request,*args,**kwargs):
  return CreateAdUnitHandler()(request,*args,**kwargs)

def add_demo_campaign(site):
    # Set up a test campaign that returns a demo ad
    c = Campaign(name="MoPub Demo Campaign",
                 u=site.account.user,
                 account=site.account,
                 campaign_type="backfill_promo",
                 description="Demo campaign for checking that MoPub works for your application")
    CampaignQueryManager.put(c)

    # Set up a test ad group for this campaign
    ag = AdGroup(name="MoPub Demo Campaign",
                 campaign=c,
                 account=site.account,
                 priority_level=3,
                 bid=1.0,
                 bid_strategy="cpm",
                 site_keys=[site.key()])
    AdGroupQueryManager.put(ag)

    # And set up a default creative
    if site.format == "custom":
        h = HtmlCreative(ad_type="html",
                         ad_group=ag,
                         account=site.account,
                         custom_height = site.custom_height,
                         custom_width = site.custom_width,
                         format=site.format,
                         name="Demo HTML Creative",
                         html_data="<style type=\"text/css\">body {font-size: 12px;font-family:helvetica,arial,sans-serif;margin:0;padding:0;text-align:center;background:white} .creative_headline {font-size: 18px;} .creative_promo {color: green;text-decoration: none;}</style><div class=\"creative_headline\">Welcome to mopub!</div><div class=\"creative_promo\"><a href=\"http://www.mopub.com\">Click here to test ad</a></div><div>You can now set up a new campaign to serve other ads.</div>")

    else:
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
    app = AppQueryManager.get(app_key)

    # check to see that the user has viewership rights, ow return 404
    if app.account.key() != self.account.key():
      raise Http404

    app.adunits = AdUnitQueryManager.get_adunits(app=app)

    # organize impressions by days
    if len(app.adunits) > 0:
      for adunit in app.adunits:
        adunit.all_stats = StatsModelQueryManager(self.account,self.offline).get_stats_for_days(publisher=adunit, days=days)
        adunit.stats = reduce(lambda x, y: x+y, adunit.all_stats, StatsModel())

    app.adunits = sorted(app.adunits, key=lambda adunit: adunit.stats.request_count, reverse=True)

    app_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=app, days=days)
    app.all_stats = app_stats

    help_text = 'Create an Ad Unit below' if len(app.adunits) == 0 else None

    if app.icon:
      app.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(app.icon)

    # In the graph, only show the top 3 ad units and bundle the rest if there are more than 4
    app.graph_adunits = app.adunits[0:4]
    if len(app.adunits) > 4:
      app.graph_adunits[3] = Site(name='Others')
      app.graph_adunits[3].all_stats = [reduce(lambda x, y: x+y, stats, StatsModel()) for stats in zip(*[au.all_stats for au in app.adunits[3:]])]
    # in order to make the app editable
    app_form_fragment = AppUpdateAJAXHandler(self.request).get(app=app)
    # in order to have a creat adunit form
    adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(app=app)

    today = app_stats[-1]
    try:
        yesterday = app_stats[-2]
    except IndexError:
        yesterday = StatsModel()
    app.stats = reduce(lambda x, y: x+y, app_stats, StatsModel())
    # this is the max active users over the date range
    # NOT total unique users
    app.stats.user_count = max([sm.user_count for sm in app_stats])

    # get adgroups targeting this app
    app.adgroups = AdGroupQueryManager.get_adgroups(app=app)

    for ag in app.adgroups:
      ag.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=app,advertiser=ag,days=days)
      ag.stats = reduce(lambda x, y: x+y, ag.all_stats, StatsModel())
      ag.percent_delivered = budget_service.percent_delivered(ag.campaign)

    promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['promo'], app.adgroups)
    promo_campaigns = sorted(promo_campaigns, lambda x,y: cmp(y.bid, x.bid))

    guarantee_campaigns = filter(lambda x: x.campaign.campaign_type in ['gtee_high', 'gtee_low', 'gtee'], app.adgroups)
    guarantee_campaigns = sorted(guarantee_campaigns, lambda x,y: cmp(y.bid, x.bid))
    levels = ('high', '', 'low')
    gtee_str = "gtee_%s"
    gtee_levels = []
    for level in levels:
        this_level = gtee_str % level if level else "gtee"
        name = level if level else 'normal'
        level_camps = filter(lambda x:x.campaign.campaign_type == this_level, guarantee_campaigns)
        gtee_levels.append(dict(name = name, adgroups = level_camps))

    marketplace_campaigns = filter(lambda x: x.campaign.campaign_type in ['marketplace'], app.adgroups)
    marketplace_campaigns = sorted(marketplace_campaigns, lambda x,y: cmp(x.bid, y.bid))

    network_campaigns = filter(lambda x: x.campaign.campaign_type in ['network'], app.adgroups)
    network_campaigns = sorted(network_campaigns, lambda x,y: cmp(y.bid, x.bid))

    backfill_promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_promo'], app.adgroups)
    backfill_promo_campaigns = sorted(backfill_promo_campaigns, lambda x,y: cmp(y.bid, x.bid))

    backfill_marketplace_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_marketplace'], app.adgroups)
    backfill_marketplace_campaigns = sorted(backfill_marketplace_campaigns, lambda x,y: cmp(x.bid, y.bid))



    return render_to_response(self.request,'publisher/app.html',
        {'app': app,
         'app_form_fragment':app_form_fragment,
         'adunit_form_fragment':adunit_form_fragment,
         'start_date': days[0],
         'end_date': days[-1],
         'date_range': self.date_range,
         'today': today,
         'yesterday': yesterday,
         'account': self.account,
         'helptext': help_text,
         'gtee': gtee_levels,
         'promo': promo_campaigns,
         'marketplace': marketplace_campaigns,
         'network': network_campaigns,
         'backfill_promo': backfill_promo_campaigns,
         'backfill_marketplace': backfill_marketplace_campaigns})


@login_required
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


@login_required
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
      ag.percent_delivered = budget_service.percent_delivered(ag.campaign)

    # to allow the adunit to be edited
    adunit_form_fragment = AdUnitUpdateAJAXHandler(self.request).get(adunit=adunit)


    promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['promo'], adunit.adgroups)
    promo_campaigns = sorted(promo_campaigns, lambda x,y: cmp(y.bid, x.bid))

    guarantee_campaigns = filter(lambda x: x.campaign.campaign_type in ['gtee_high', 'gtee_low', 'gtee'], adunit.adgroups)
    guarantee_campaigns = sorted(guarantee_campaigns, lambda x,y: cmp(y.bid, x.bid))
    levels = ('high', '', 'low')
    gtee_str = "gtee_%s"
    gtee_levels = []
    for level in levels:
        this_level = gtee_str % level if level else "gtee"
        name = level if level else 'normal'
        level_camps = filter(lambda x:x.campaign.campaign_type == this_level, guarantee_campaigns)
        gtee_levels.append(dict(name = name, adgroups = level_camps))

    marketplace_campaigns = filter(lambda x: x.campaign.campaign_type in ['marketplace'], adunit.adgroups)
    marketplace_campaigns = sorted(marketplace_campaigns, lambda x,y: cmp(x.bid, y.bid))

    network_campaigns = filter(lambda x: x.campaign.campaign_type in ['network'], adunit.adgroups)
    network_campaigns = sorted(network_campaigns, lambda x,y: cmp(y.bid, x.bid))

    backfill_promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_promo'], adunit.adgroups)
    backfill_promo_campaigns = sorted(backfill_promo_campaigns, lambda x,y: cmp(y.bid, x.bid))

    backfill_marketplace_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_marketplace'], adunit.adgroups)
    backfill_marketplace_campaigns = sorted(backfill_marketplace_campaigns, lambda x,y: cmp(x.bid, y.bid))


    today = adunit.all_stats[-1]
    try:
        yesterday = adunit.all_stats[-2]
    except:
        yesterday = StatsModel()

    # write response
    return render_to_response(self.request,'publisher/adunit.html',
        {'site': adunit,
         'adunit': adunit,
         'today': today,
         'yesterday': yesterday,
         'start_date': days[0],
         'end_date': days[-1],
         'date_range': self.date_range,
         'account': self.account,
         'days': days,
         'adunit_form_fragment': adunit_form_fragment,
         'gtee': gtee_levels,
         'promo': promo_campaigns,
         'marketplace': marketplace_campaigns,
         'network': network_campaigns,
         'backfill_promo': backfill_promo_campaigns,
         'backfill_marketplace': backfill_marketplace_campaigns})

@login_required
def adunit_show(request,*args,**kwargs):
  return AdUnitShowHandler()(request,*args,**kwargs)

class AppUpdateAJAXHandler(RequestHandler):
  TEMPLATE  = 'publisher/forms/app_form.html'
  def get(self,app_form=None,app=None):
    app_form = app_form or AppForm(instance=app, is_edit_form=True)
    app_form.is_edit_form = True
    return self.render(form=app_form)

  def render(self,template=None,**kwargs):
    template_name = template or self.TEMPLATE
    return render_to_string(self.request,
                            template_name = template_name,
                            data = kwargs)

  def json_response(self,json_dict):
    return JSONResponse(json_dict)

  def post(self,app_key=None):
    app_key = app_key or self.request.POST.get('app_key')
    if app_key:
      app = AppQueryManager.get(app_key)
    else:
      app = None

    app_form = AppForm(data = self.request.POST,
                       files = self.request.FILES,
                       instance = app,
                       is_edit_form = True)

    json_dict = {'success':False,'errors':[]}
    if app_form.is_valid():
      if not app_form.instance: #ensure form posts do not change ownership
        account = self.account
      else:
        account = app_form.instance.account
      app = app_form.save(commit=False)
      app.account = account
      AppQueryManager.put(app)

      json_dict.update(success=True)

      return self.json_response(json_dict)

    flatten_errors = lambda frm : [(k, unicode(v[0])) for k, v in frm.errors.items()]
    grouped_errors = flatten_errors(app_form)

    json_dict.update(success = False, errors = grouped_errors)
    return self.json_response(json_dict)

@login_required
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
    json_dict = {'success':False, 'errors': []}

    if adunit_form.is_valid():
      if not adunit_form.instance: #ensure form posts do not change ownership
        account = self.account
      else:
        account = adunit_form.instance.account
      adunit = adunit_form.save(commit=False)
      adunit.account = account
      AdUnitQueryManager.put(adunit)

      json_dict.update(success=True)
      return self.json_response(json_dict)

    flatten_errors = lambda frm : [(k, unicode(v[0])) for k, v in frm.errors.items()]
    grouped_errors = flatten_errors(adunit_form)

    json_dict.update(success=False, errors = grouped_errors)
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

class RemoveAdUnitHandler(RequestHandler):
    def post(self, adunit_key):
        a = AdUnitQueryManager.get(adunit_key)
        if a != None and a.app_key.account == self.account:
            a.deleted = True
            AdUnitQueryManager.put(a)

        return HttpResponseRedirect(reverse('publisher_app_show', kwargs={'app_key': a.app.key()}))

@login_required
def publisher_adunit_delete(request,*args,**kwargs):
    return RemoveAdUnitHandler()(request,*args,**kwargs)

class RemoveAppHandler(RequestHandler):
    def post(self, app_key):
        app = AppQueryManager.get(app_key)
        adunits = AdUnitQueryManager.get_adunits(app=app)
        if app and app.account == self.account:
            app.deleted = True
            # also "delete" all the adunits associated with the app
            for adunit in adunits:
                adunit.deleted = True
            AppQueryManager.put(app)
            AdUnitQueryManager.put(adunits)


        return HttpResponseRedirect(reverse('publisher_index'))

@login_required
def app_delete(request,*args,**kwargs):
    return RemoveAppHandler()(request,*args,**kwargs)

class GenerateHandler(RequestHandler):
  def get(self,adunit_key):
    adunit = AdUnitQueryManager.get(adunit_key)
    status = self.params.get('status')
    return render_to_response(self.request,'publisher/code.html', {'site': adunit, 'status': status, 'account': self.account})

@login_required
def generate(request,*args,**kwargs):
  return GenerateHandler()(request,*args,**kwargs)

class AppExportHandler(RequestHandler):
    def post(self, app_key, file_type, start, end):
        start = datetime.strptime(start,'%m%d%y')
        end = datetime.strptime(end,'%m%d%y')
        days = date_magic.gen_days(start, end)

        app = AppQueryManager.get(app_key)
        all_stats = StatsModelQueryManager(self.account, offline=self.offline).get_stats_for_days(publisher=app, days=days)
        f_name_dict = dict(app_title = app.name,
                           start = start.strftime('%b %d'),
                           end   = end.strftime('%b %d, %Y'),
                           )

        f_name = "%(app_title)s AppStats,  %(start)s - %(end)s" % f_name_dict
        f_name = f_name.encode('ascii', 'ignore')
        data = map(lambda x: [x[0]] + x[1], zip([day.strftime('%a, %b %d, %Y') for day in days], [app_stats(stat) for stat in all_stats]))
        titles = ['Date', 'Requests', 'Impressions', 'Fill Rate', 'Clicks', 'CTR']
        return sswriter.export_writer(file_type, f_name, titles, data)



def app_export(request, *args, **kwargs):
    return AppExportHandler()(request, *args, **kwargs)
