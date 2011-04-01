import logging, os, re, datetime, hashlib

from urllib import urlencode
from copy import deepcopy

import base64, binascii
from google.appengine.api import users, images
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm, \
                             BaseCreativeForm, TextCreativeForm, \
                             ImageCreativeForm, TextAndTileCreativeForm, \
                             HtmlCreativeForm

from publisher.models import Site, Account, App
from reporting.models import SiteStats

from common.utils.cachedquerymanager import CachedQueryManager

from account.query_managers import AccountQueryManager
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, \
                                      CreativeQueryManager, TextCreativeQueryManager, \
                                      ImageCreativeQueryManager, TextAndTileCreativeQueryManager, \
                                      HtmlCreativeQueryManager
from publisher.query_managers import AdUnitQueryManager, AppQueryManager
from reporting.query_managers import SiteStatsQueryManager

class RequestHandler(object):
    def __init__(self,request=None):
      if request:
        self.request = request
        self.account = None
        user = users.get_current_user()
        if user:
          if users.is_current_user_admin():
            account_key_name = request.COOKIES.get("account_impersonation",None)
            if account_key_name:
              self.account = AccountQueryManager().get_by_key_name(account_key_name)
        if not self.account:  
          self.account = Account.current_account()
        
      super(RequestHandler,self).__init__()  
  
    def __call__(self,request,*args,**kwargs):
        self.params = request.POST or request.GET
        self.request = request or self.request
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

class IndexHandler(RequestHandler):
  def get(self):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    campaigns = CampaignQueryManager().get_campaigns(account=self.account)
    for c in campaigns:
      c.all_stats = SiteStatsQueryManager.get_sitestats_for_days(owner=c, days=days)      
      c.stats = reduce(lambda x, y: x+y, c.all_stats, SiteStats())
            
    # compute rollups to display at the top
    totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[c.all_stats for c in campaigns])]
    
    promo_campaigns = filter(lambda x: x.campaign_type in ['promo'], campaigns)
    garauntee_campaigns = filter(lambda x: x.campaign_type in ['gtee'], campaigns)
    network_campaigns = filter(lambda x: x.campaign_type in ['network'], campaigns)
    backfill_promo_campaigns = filter(lambda x: x.campaign_type in ['backfill_promo'], campaigns)

    help_text = None
    if network_campaigns:
      if not (self.account.adsense_pub_id or self.account.admob_pub_id):
        help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

    return render_to_response(self.request, 
      'advertiser/index.html', 
      {'campaigns':campaigns, 
       'start_date': days[0],
       'date_range': self.date_range,
       'gtee': garauntee_campaigns,
       'promo': promo_campaigns,
       'backfill_promo': backfill_promo_campaigns,
       'network': network_campaigns,
       'helptext':help_text })
      
@whitelist_login_required     
def index(request,*args,**kwargs):
    return IndexHandler()(request,*args,**kwargs)     

class AdGroupIndexHandler(RequestHandler):
  def get(self):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    apps = AppQueryManager().get_apps(account=self.account)
    campaigns = CampaignQueryManager().get_campaigns(account=self.account)
    
    if campaigns:
      adgroups = AdGroupQueryManager().get_adgroups(campaigns=campaigns)
    else:
      adgroups = []
    
    for c in adgroups:
      c.all_stats = SiteStatsQueryManager().get_sitestats_for_days(owner=c, days=days)      
      c.stats = reduce(lambda x, y: x+y, c.all_stats, SiteStats())

    promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['promo'], adgroups)
    promo_campaigns = sorted(promo_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
    guarantee_campaigns = filter(lambda x: x.campaign.campaign_type in ['gtee_high', 'gtee_low', 'gtee'], adgroups)
    guarantee_campaigns = sorted(guarantee_campaigns, lambda x,y: cmp(y.bid, x.bid))
    levels = ('high', '', 'low')
    gtee_str = "gtee_%s"
    gtee_levels = []
    for level in levels:
        this_level = gtee_str % level if level else "gtee"
        name = level if level else 'normal'
        level_camps = filter(lambda x:x.campaign.campaign_type == this_level, guarantee_campaigns)
        gtee_levels.append(dict(name = name, campaigns = level_camps))
    logging.warning(guarantee_campaigns)
    
    for level in gtee_levels:
        if level['name'] == 'normal' and len(gtee_levels[0]['campaigns']) == 0 and len(gtee_levels[2]['campaigns']) == 0: 
            level['foo'] = True 
        elif len(level['campaigns']) > 0:
            level['foo'] = True 
        else:
            level['foo'] = False 

    logging.warning(gtee_levels)


    network_campaigns = filter(lambda x: x.campaign.campaign_type in ['network'], adgroups)
    network_campaigns = sorted(network_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
    backfill_promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_promo'], adgroups)
    backfill_promo_campaigns = sorted(backfill_promo_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
    adgroups = sorted(adgroups, key=lambda adgroup: adgroup.stats.impression_count, reverse=True)
    
    help_text = None
    if network_campaigns:
      if not (self.account.adsense_pub_id or self.account.admob_pub_id):
        help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

    graph_adgroups = adgroups[0:4]
    if len(adgroups) > 4:
      graph_adgroups[3] = AdGroup(name='Others')
      graph_adgroups[3].all_stats = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[c.all_stats for c in adgroups[3:]])]      

      # gtee = [ {name: 'high', campaigns: what usually goes in gtee } ]

    return render_to_response(self.request, 
      'advertiser/adgroups.html', 
      {'adgroups':adgroups,
       'graph_adgroups': graph_adgroups,
       'start_date': days[0],
       'date_range': self.date_range,
       'apps' : apps,
       'totals': reduce(lambda x, y: x+y.stats, adgroups, SiteStats()),
       'today': reduce(lambda x, y: x+y, [c.all_stats[-1] for c in graph_adgroups], SiteStats()),
       'yesterday': reduce(lambda x, y: x+y, [c.all_stats[-2] for c in graph_adgroups], SiteStats()),
       'gtee': gtee_levels, 
       'promo': promo_campaigns,
       'network': network_campaigns,
       'backfill_promo': backfill_promo_campaigns,
       'account': self.account,
       'helptext':help_text })

@whitelist_login_required     
def adgroups(request,*args,**kwargs):
    return AdGroupIndexHandler()(request,*args,**kwargs)


class CreateCampaignAJAXHander(RequestHandler):
  TEMPLATE  = 'advertiser/forms/campaign_create_form.html'
  def get(self,campaign_form=None,adgroup_form=None,
               campaign=None,adgroup=None):
    if adgroup:           
      campaign = campaign or adgroup.campaign
    campaign_form = campaign_form or CampaignForm(instance=campaign)
    adgroup_form = adgroup_form or AdGroupForm(instance=adgroup)
    networks = [["admob","AdMob",False],["adsense","AdSense",False],["brightroll","BrightRoll",False],["greystripe","GreyStripe",False],\
      ["iAd","iAd",False],["inmobi","InMobi",False],["jumptap","Jumptap",False],["millennial","Millennial Media",False],["mobfox","MobFox",False],['custom', 'Custom Network', False]]
    
    all_adunits = AdUnitQueryManager().get_adunits(account=self.account)
    
    adgroup_form['site_keys'].choices = all_adunits # needed for validation TODO: doesn't actually work
    
    # TODO: Remove this hack to place the bidding info with the rest of campaign
    #Hackish part
    campaign_form.bid  = adgroup_form['bid']
    campaign_form.bid_strategy = adgroup_form['bid_strategy']
    campaign_form.custom_html = adgroup_form['custom_html']

    logging.warning("bid: %s %s"%("campaign_form['bid']",campaign_form.bid.value))

    adunit_keys = adgroup_form['site_keys'].value or []
    adunit_str_keys = [unicode(k) for k in adunit_keys]
    for adunit in all_adunits:
      adunit.checked = unicode(adunit.key()) in adunit_str_keys
    
    if adgroup_form:
      for n in networks:
        if adgroup_form['network_type'].value == n[0]:
          n[2] = True
    elif adgroup:  
      for n in networks:
        if adgroup.network_type == n[0]:
          n[2] = True
    else:
      networks[0][2] = True # select the first by default      
    
    campaign_form.add_context(dict(networks=networks))
    adgroup_form.add_context(dict(all_adunits=all_adunits))
    return self.render(campaign_form=campaign_form,adgroup_form=adgroup_form)

  def render(self,template=None,**kwargs):
    template_name = template or self.TEMPLATE
    return render_to_string(self.request,template_name=template_name,data=kwargs)

  def json_response(self,json_dict):
    return JSONResponse(json_dict)

  def post(self):
    adgroup_key = self.request.POST.get('adgroup_key')
    if adgroup_key:
      adgroup = AdGroupQueryManager().get_by_key(adgroup_key)
      campaign = adgroup.campaign
    else:
      adgroup = None
      campaign = None

    campaign_form = CampaignForm(data=self.request.POST,instance=campaign)
    adgroup_form = AdGroupForm(data=self.request.POST,instance=adgroup)
    
    if adgroup:
      adunits_to_update = set(adgroup.site_keys)
    else:
      adunits_to_update = set()
    
    
    all_adunits = AdUnitQueryManager().get_adunits(account=self.account)
    sk_field = adgroup_form.fields['site_keys']
    sk_field.choices = all_adunits # TODO: doesn't work needed for validation
    
    json_dict = {'success':False,'html':None}
    
    if campaign_form.is_valid():
      campaign = campaign_form.save(commit=False)
      campaign.u = self.account.user
      campaign.account = self.account
      
      if adgroup_form.is_valid():
        adgroup = adgroup_form.save(commit=False)
        adgroup.account = self.account
                
        # TODO: clean this up in case the campaign succeeds and the adgroup fails
        CampaignQueryManager().put_campaigns(campaign)
        adgroup.campaign = campaign
        # TODO: put this in the adgroup form
        if not adgroup.campaign.campaign_type == 'network':
          adgroup.network_type = None
        
       
       #put adgroup so creative can have a reference to it
        AdGroupQueryManager().put_adgroups(adgroup)

       ##Check if creative exists for this network type, if yes
       #update, if no, delete old and create new
        if campaign.campaign_type == "network":
          html_data = None
          if adgroup.network_type == 'custom':
              html_data = adgroup_form['custom_html'].value
          #build default creative with custom_html data if custom or none if anything else
          creative = adgroup.default_creative(html_data)
          if adgroup.net_creative and creative.__class__ == adgroup.net_creative.__class__:
              #if the adgroup has a creative AND the new creative and old creative are the same class, 
              #ignore the new creative and set the variable to point to the old one
              creative = adgroup.net_creative
              if adgroup.network_type == 'custom':
                  #if the network is a custom one, the creative might be the same, but the data might be new, set the old
                  #creative to have the (possibly) new data
                  creative.html_data = html_data
          elif adgroup.net_creative:
              #in this case adgroup.net_creative has evaluated to true BUT the class comparison did NOT.  
              #at this point we know that there was an old creative AND it's different from the old creative so
              
              #Get rid of the old creative's reference to the adgroup (just in case)
              adgroup.net_creative.adgroup = None
              #and delete the old creative
              AdGroupQueryManager().delete_adgroups(adgroup.net_creative)
          #creative should now reference the appropriate creative (new if different, old if the same, updated old if same and custom)
          creative.account = self.account
          #put the creative so we can reference it
          CreativeQueryManager().put_creatives(creative)
          #set adgroup to reference the correct creative
          adgroup.net_creative = creative.key()
          #put the adgroup again with the new (or old) creative reference
          AdGroupQueryManager().put_adgroups(adgroup)
          

        # update cache
        adunits_to_update.update(adgroup.site_keys)
        if adunits_to_update:
          logging.info("adunits to clear: %s"%[str(a) for a in adunits_to_update])
          adunits = AdUnitQueryManager().get_by_key(adunits_to_update)
          logging.info("adunits to clear: %s"%[str(a.key()) for a in adunits if a])
          CachedQueryManager().cache_delete(adunits)
        
        
        # Onboarding: user is done after they set up their first campaign
        if self.account.status == "step4":
          self.account.status = ""
          AccountQueryManager().put_accounts(self.account)
        
        json_dict.update(success=True,new_page=reverse('advertiser_adgroup_show',kwargs={'adgroup_key':str(adgroup.key())}))
        return self.json_response(json_dict)
    logging.warning('adgroup form errors: %s'%adgroup_form.errors) 
    logging.warning('adgroup form bid: %s'%adgroup_form['bid'].value)      
         
    new_html = self.get(campaign_form=campaign_form,
                        adgroup_form=adgroup_form)
    json_dict.update(success=False,html=new_html)    
    return self.json_response(json_dict)  
    
@whitelist_login_required     
def campaign_adgroup_create_ajax(request,*args,**kwargs):
  return CreateCampaignAJAXHander()(request,*args,**kwargs)      


# Wrapper for the AJAX handler
class CreateCampaignHandler(RequestHandler):
  def get(self,campaign_form=None, adgroup_form=None):
    campaign_create_form_fragment = CreateCampaignAJAXHander(self.request).get()
    return render_to_response(self.request,'advertiser/new.html', {"campaign_create_form_fragment": campaign_create_form_fragment})
  
  # TODO: this should not get called  
  # def post(self):
  #   campaign_form = CampaignForm(data=self.request.POST)
  #   adgroup_form = AdGroupForm(data=self.request.POST)
  #   
  #   all_adunits = AdUnitQueryManager().get_adunits(account=self.account)
  #   sk_field = adgroup_form.fields['site_keys']
  #   sk_field.queryset = all_adunits # TODO: doesn't work needed for validation
  #   if campaign_form.is_valid():
  #     campaign = campaign_form.save(commit=False)
  #     campaign.u = self.account.user
  #     
  #     if adgroup_form.is_valid():
  #       adgroup = adgroup_form.save(commit=False)
  #       
  #       # TODO: clean this up in case the campaign succeeds and the adgroup fails
  #       CampaignQueryManager().put_campaigns(campaign)
  #       adgroup.campaign = campaign
  #       AdGroupQueryManager().put_adgroups(adgroup)
  #       if campaign.campaign_type == "network":
  #         creative = adgroup.default_creative()
  #         CreativeQueryManager().put_creatives(creative)
  #       
  #       return HttpResponseRedirect(reverse('advertiser_adgroup_show', kwargs={'adgroup_key':str(adgroup.key())}))
  # 
  #   return self.get(campaign_form,adgroup_form)

@whitelist_login_required     
def campaign_adgroup_create(request,*args,**kwargs):
  return CreateCampaignHandler()(request,*args,**kwargs)      

class CreateAdGroupHandler(RequestHandler):
  def get(self, campaign_key=None, adgroup_key=None, edit=False, title="Create an Ad Group"):
    if campaign_key:
      c = CampaignQueryManager().get_by_key(campaign_key)
      adgroup = AdGroup(name="%s Ad Group" % c.name, campaign=c, bid_strategy="cpm", bid=10.0, percent_users=100.0)
    if adgroup_key:
      adgroup = AdGroupQueryManager().get_by_key(adgroup_key)
      c = adgroup.campaign
      if not adgroup:
        raise Http404("AdGroup does not exist")  
    adgroup.budget = c.budget # take budget from campaign for the time being
    f = AdGroupForm(instance=adgroup)
    adunits = AdUnitQueryManager().get_adunits(account=self.account)
    
    # allow the correct sites to be checked
    for adunit in adunits:
      adunit.checked = adunit.key() in adgroup.site_keys

    # TODO: Clean up this hacked shit 
    networks = [["admob","AdMob",False],["adsense","AdSense",False],["brightroll","BrightRoll",False],["jumptap","Jumptap",False],["greystripe","GreyStripe",False],["iAd","iAd",False],["inmobi","InMobi",False],["millennial","Millennial Media",False],["mobfox","MobFox",False]]
    for n in networks:
      if adgroup.network_type == n[0]:
        n[2] = True

    return render_to_response(self.request,'advertiser/new_adgroup.html', {"f": f, "c": c, "sites": adunits, "title": title, "networks":networks})

  def post(self, campaign_key=None,adgroup_key=None, edit=False, title="Create an Ad Group"):
        
    adgroup = AdGroupQueryManager().get_by_key(adgroup_key)
    campaign = adgroup.campaign
    
    campaign_form = CampaignForm(data=self.request.POST,instance=campaign)
    adgroup_form = AdGroupForm(data=self.request.POST,instance=adgroup)
    
    all_adunits = AdUnitQueryManager().get_adunits(account=self.account)

    if campaign_form.is_valid():
      campaign = campaign_form.save(commit=False)
      campaign.u = self.account.user
      
      if adgroup_form.is_valid():
        adgroup = adgroup_form.save(commit=False)
        # TODO: clean this up in case the campaign succeeds and the adgroup fails
        CampaignQueryManager().put_campaigns(campaign)
        adgroup.campaign = campaign
        AdGroupQueryManager().put_adgroups(adgroup)
        return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':str(adgroup.key())}))
       
@whitelist_login_required     
def campaign_adgroup_new(request,*args,**kwargs):
  return CreateAdGroupHandler()(request,*args,**kwargs)      

@whitelist_login_required
def campaign_adgroup_edit(request,*args,**kwargs):
  kwargs.update(title="Edit Ad Group",edit=True)
  return CreateAdGroupHandler()(request,*args,**kwargs)  
  

class ShowHandler(RequestHandler):          
  def get(self, campaign_key):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    # load the campaign
    campaign = CampaignQueryManager.get_by_key(campaign_key)
    
    # load the adgroups
    bids = AdGroupQueryManager().get_campaigns(campaign=campaign)
    bids.sort(lambda x,y:cmp(x.priority_level, y.priority_level))
    for b in bids:
      b.all_stats = SiteStatsQueryManager.get_sitestats_for_days(owner=b, days=days)      
      b.stats = reduce(lambda x, y: x+y, b.all_stats, SiteStats())

    # no ad groups?
    if len(bids) == 0:
      return HttpResponseRedirect(reverse('advertiser_adgroup_new', kwargs={'campaign_key': campaign.key()}))
    else:
      # compute rollups to display at the top
      today = SiteStats.rollup_for_day(bids, SiteStats.today())
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[b.all_stats for b in bids])]
      
      help_text = None
      if campaign.campaign_type == 'network':
        if not (self.account.adsense_pub_id or self.account.admob_pub_id):
          help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

      
      # write response
      return render_to_response(self.request,'advertiser/show.html', 
                                            {'campaign':campaign, 
                                            'bids': bids,
                                            'today': today,
                                            'user':self.account,
                                            'helptext':help_text})

@whitelist_login_required     
def campaign_show(request,*args,**kwargs):
 return ShowHandler()(request,*args,**kwargs) 

class EditHandler(RequestHandler):
  def get(self,campaign_key):
    c = CampaignQueryManager().get_by_key(campaign_key)
    f = CampaignForm(instance=c)
    return render_to_response(self.request,'advertiser/edit.html', {"f": f, "campaign": c})

  def post(self):
    c = CampaignQueryManager().get_by_key(self.request.POST.get('id'))
    f = CampaignForm(data=self.request.POST, instance=c)
    if c.u == self.account.user:
      f.save(commit=False)
      CampaignQueryManager().put_campaigns(c)
      return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))

@whitelist_login_required  
def campaign_edit(request,*args,**kwargs):
  return EditHandler()(request,*args,**kwargs)

class PauseHandler(RequestHandler):
  def post(self):
    action = self.request.POST.get("action", "pause")
    updated_campaigns = []
    for id_ in self.request.POST.getlist('id') or []:
      c = CampaignQueryManager().get_by_key(id_)
      updated_campaigns.append(c)
      update_objs = []
      if c != None and c.u == self.account.user:
        if action == "pause":
          c.active = False
          c.deleted = False
          update_objs.append(c)
        elif action == "resume":
          c.active = True
          c.deleted = False
          update_objs.append(c)
        elif action == "delete":
          # 'deletes' adgroups and creatives
          c.active = False
          c.deleted = True
          update_objs.append(c)
          for adgroup in c.adgroups:
            adgroup.deleted = True
            update_objs.append(adgroup)
            for creative in adgroup.creatives:
              creative.deleted = True
              update_objs.append(creative)
      if update_objs: 
        db.put(update_objs)   
        adgroups = AdGroupQueryManager().get_adgroups(campaigns=updated_campaigns)
        adunits = []
        for adgroup in adgroups:
          adunits.extend(adgroups.site_keys)
        adunits = AdUnitQueryManager().get_by_key(adunits)  
        CachedQueryManager().put(adunits)
    return HttpResponseRedirect(reverse('advertiser_campaign',kwargs={}))
  
@whitelist_login_required
def campaign_pause(request,*args,**kwargs):
  return PauseHandler()(request,*args,**kwargs)
  
class ShowAdGroupHandler(RequestHandler):
    #TODO This currently doesn't show the locales that were set previously
    #(kinda a problem...)
  def get(self, adgroup_key):
    # Set start date if passed in, otherwise get most recent days
    if self.start_date:
      days = SiteStats.get_days(self.start_date, self.date_range)
    else:
      days = SiteStats.lastdays(self.date_range)

    adgroup = AdGroupQueryManager().get_by_key(adgroup_key)
    adgroup.all_stats = SiteStatsQueryManager().get_sitestats_for_days(owner=adgroup, days=days)
    adgroup.stats = reduce(lambda x, y: x+y, adgroup.all_stats, SiteStats())    
    
    # creatives = Creative.gql('where ad_group = :1 and deleted = :2 and ad_type in :3', adgroup, False, ["text", "image", "html"]).fetch(50)
    creatives = CreativeQueryManager().get_creatives(adgroup=adgroup)
    creatives = list(creatives)
    for c in creatives:
      c.all_stats = SiteStatsQueryManager().get_sitestats_for_days(owner=c, days=days)
      c.stats = reduce(lambda x, y: x+y, c.all_stats, SiteStats())
      if not c.format:
        c.format = "320x50" # TODO: Should fix DB so that format is always there
      c.size = c.format.partition('x')
    
    apps = App.gql("where account = :1 and deleted = :2", self.account, False).fetch(50)
    for a in apps:
      if a.icon:
        a.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(a.icon)
        
    # TODO: use query manager    
    adunits = map(lambda x: Site.get(x), adgroup.site_keys)
    for au in adunits:
      au.all_stats = SiteStatsQueryManager().get_sitestats_for_days(site=au,owner=adgroup, days=days)
      au.stats = reduce(lambda x, y: x+y, au.all_stats, SiteStats())
      au.app = App.get(au.app_key.key())

    adunits = sorted(adunits, key=lambda adunit: adunit.stats.impression_count, reverse=True)

    graph_adunits = adunits[0:4]
      
    if len(adunits) > 4:
      graph_adunits[3] = Site(name='Others')
      graph_adunits[3].all_stats = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[au.all_stats for au in adunits[3:]])]
    
    
    logging.warning("network: type: %s"%(adgroup.network_type))
      
    if not adgroup.network_type:  
      # In order to have add creative
      creative_handler = AddCreativeHandler(self.request)
      creative_fragment = creative_handler.get() # return the creative fragment

      # In order to have each creative be editable
      for c in creatives:
        c.html_fragment = creative_handler.get(creative=c)
    else:
      creative_fragment = None    
    
    # In order to make the edit page
    campaign_create_form_fragment = CreateCampaignAJAXHander(self.request).get(adgroup=adgroup)
    
    return render_to_response(self.request,'advertiser/adgroup.html', 
                              {'campaign': adgroup.campaign,
                              'apps': apps,
                              'adgroup': adgroup, 
                              'creatives': creatives,
                              'totals': reduce(lambda x, y: x+y.stats, adunits, SiteStats()),
                              'today': reduce(lambda x, y: x+y, [a.all_stats[-1] for a in graph_adunits], SiteStats()),
                              'yesterday': reduce(lambda x, y: x+y, [a.all_stats[-2] for a in graph_adunits], SiteStats()),
                              'adunits' : adunits,
                              'graph_adunits': graph_adunits,
                              'start_date': days[0],
                              'creative_fragment':creative_fragment,
                              'campaign_create_form_fragment':campaign_create_form_fragment})
    
@whitelist_login_required   
def campaign_adgroup_show(request,*args,**kwargs):    
  return ShowAdGroupHandler()(request,*args,**kwargs)


class PauseAdGroupHandler(RequestHandler):
  def post(self):
    action = self.request.POST.get("action", "pause")
    adgroups = []
    update_objs = []
    for id_ in self.request.POST.getlist('id') or []:
      a = AdGroupQueryManager().get_by_key(id_)
      adgroups.append(a)
      if a != None and a.campaign.u == self.account.user:
        if action == "pause":
          a.active = False
          a.deleted = False
          update_objs.append(a)
        elif action == "resume":
          a.active = True
          a.deleted = False
          update_objs.append(a)
        elif action == "delete":
          a.active = False
          a.deleted = True
          update_objs.append(a)
          for creative in a.creatives:
            creative.deleted = True
            update_objs.append(creative)
      
    if update_objs:
      AdGroupQueryManager().put_adgroups(update_objs)
      adunits = []
      for adgroup in adgroups:
        adunits.extend(adgroup.site_keys)
        
      adunits = Site.get(adunits)  
      CachedQueryManager().cache_delete(adunits)
         
    return HttpResponseRedirect(reverse('advertiser_campaign', kwargs={}))

@whitelist_login_required
def bid_pause(request,*args,**kwargs):
  return PauseAdGroupHandler()(request,*args,**kwargs)
  
# AJAX Creative Create/Edit
#
class AddCreativeHandler(RequestHandler):
  TEMPLATE  = 'advertiser/forms/creative_form.html'
  def get(self,base_creative_form=None,
               text_creative_form=None,
               image_creative_form=None,
               text_tile_creative_form=None,
               html_creative_form=None,
               creative=None,
               text_creative=None,
               image_creative=None,
               text_tile_creative=None,
               html_creative=None):

    # TODO: Shouldn't I be able to just cast???           
    if creative:
      if creative.ad_type == "text":
        text_creative = TextCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "text_icon":
        text_tile_creative = TextAndTileCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "image":
        image_creative = ImageCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "html":
        html_creative = HtmlCreativeQueryManager().get_by_key(creative.key())      
    
    # NOTE: creative is usually None so the default form is actually unbound           
    base_creative_form = base_creative_form or BaseCreativeForm(instance=creative)
    text_creative_form = text_creative_form or TextCreativeForm(instance=text_creative)
    image_creative_form = image_creative_form or ImageCreativeForm(instance=image_creative)
    text_tile_creative_form = text_tile_creative_form or TextAndTileCreativeForm(instance=text_tile_creative)
    html_creative_form = html_creative_form or HtmlCreativeForm(instance=html_creative)

    return self.render(base_creative_form=base_creative_form,
                  text_creative_form=text_creative_form,
                  image_creative_form=image_creative_form,
                  text_tile_creative_form=text_tile_creative_form,
                  html_creative_form=html_creative_form)
  
  def render(self,template=None,**kwargs):
    template_name = template or self.TEMPLATE
    return render_to_string(self.request,template_name=template_name,data=kwargs)
  
  def json_response(self,json_dict):
    # if not self.request.FILES:
    return JSONResponse(json_dict)
    # else:
    #   logging.info("responding with: %s"%('<textarea>'+simplejson.dumps(json_dict)+'</textarea>'))
    #   return HttpResponse('<textarea>'+simplejson.dumps(json_dict)+'</textarea>',mimetype="text/plain")
      
  def post(self):
    ad_group = AdGroupQueryManager().get_by_key(self.request.POST.get('adgroup_key'))
    creative_key = self.request.POST.get('creative_key')
    if creative_key:
      creative = CreativeQueryManager().get_by_key(creative_key)
    else:
      creative = None

    text_creative = None
    image_creative = None
    text_tile_creative = None
    html_creative = None
      
    # TODO: Shouldn't I be able to just cast???           
    if creative:
      if creative.ad_type == "text":
        text_creative = TextCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "text_icon":
        text_tile_creative = TextAndTileCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "image":
        image_creative = ImageCreativeQueryManager().get_by_key(creative.key())
      elif creative.ad_type == "html":
        html_creative = HtmlCreativeQueryManager().get_by_key(creative.key())      
      
      
    base_creative_form = BaseCreativeForm(data=self.request.POST,instance=creative)
    text_creative_form = TextCreativeForm(data=self.request.POST,instance=text_creative)
    image_creative_form = ImageCreativeForm(data=self.request.POST,files=self.request.FILES,instance=image_creative)
    text_tile_creative_form = TextAndTileCreativeForm(data=self.request.POST,files=self.request.FILES,instance=text_tile_creative)
    html_creative_form = HtmlCreativeForm(data=self.request.POST,instance=html_creative)

    jsonDict = {'success':False,'html':None}
    if base_creative_form.is_valid():
      base_creative = base_creative_form.save(commit=False)
      ad_type = base_creative.ad_type
      if ad_type == "text":
        creative_form = text_creative_form
      elif ad_type == "text_icon":
        creative_form = text_tile_creative_form
      elif ad_type == "image":
        creative_form = image_creative_form
      elif ad_type == "html":
        creative_form = html_creative_form
        
      if creative_form.is_valid():
        creative = creative_form.save(commit=False)
        creative.ad_group = ad_group
        creative.account = self.account
        CreativeQueryManager().put_creatives(creative)    
        # update cache
        adunits = AdUnitQueryManager().get_by_key(ad_group.site_keys,none=True)
        logging.warning("here: %s"%adunits)
        if adunits:
          CachedQueryManager().cache_delete(adunits)
        jsonDict.update(success=True)
        return self.json_response(jsonDict)
    
    new_html = self.get(base_creative_form,text_creative_form,image_creative_form,\
                        text_tile_creative_form,html_creative_form)
    jsonDict.update(success=False,html=new_html)
    return self.json_response(jsonDict)
      
  
@whitelist_login_required
def creative_create(request,*args,**kwargs):
  return AddCreativeHandler()(request,*args,**kwargs)  

class DisplayCreativeHandler(RequestHandler):
  def get(self, creative_key):
    c = CreativeQueryManager().get_by_key(creative_key)
    if c and c.ad_type == "image" and c.image:
      return HttpResponse(c.image,content_type='image/png')
    if c and c.ad_type == "text_icon":
      if c.image:
        c.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
      return render_to_response(self.request, 'advertiser/text_tile.html', {'c':c})
      #return HttpResponse(c.image,content_type='image/png')
    if c and c.ad_type == "html":
      return HttpResponse("<html><body style='margin:0px;'>"+c.html_data+"</body></html");
    return HttpResponse('NOOOOOOOOOOOO IMAGE')
    
class CreativeImageHandler(RequestHandler):
  def get(self,creative_key):
    c = CreativeQueryManager().get_by_key(creative_key)
    if c and c.image:
      return HttpResponse(c.image,content_type='image/png')
    raise Http404

def creative_image(request,*args,**kwargs):
  return DisplayCreativeHandler()(request,*args,**kwargs)

def creative_html(request,*args,**kwargs):
  return DisplayCreativeHandler()(request,*args,**kwargs)

class CreativeManagementHandler(RequestHandler):
  def post(self):
    adgroup_key = self.request.POST.get('adgroup_key')
    keys = self.request.POST.getlist('key')
    action = self.request.POST.get('action','pause')
    update_objs = []
    # TODO: bulk get before for loop
    for creative_key in keys:
      c = CreativeQueryManager().get_by_key(creative_key)
      if c != None and c.ad_group.campaign.u == self.account.user: # TODO: clean up dereferences
        if action == "pause":
          c.deleted = False
          c.active = False
          update_objs.append(c)
        elif action == "resume":
          c.deleted = False
          c.active = True
          update_objs.append(c)
        elif action == "delete":
          c.deleted = True
          c.active = False
          update_objs.append(c)
        
    if update_objs:
      # db.put(update_objs)
      CreativeQueryManager().put_creatives(update_objs)
      
      # update cache
      adunits = AdUnitQueryManager().get_by_key(c.ad_group.site_keys,none=True)
      if adunits:
        try:
          CachedQueryManager().cache_delete([a for a in adunits if a])
        except:
          CachedQueryManager().cache_delete(adunits)
            
        
    return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':adgroup_key}))

@whitelist_login_required  
def creative_manage(request,*args,**kwargs):
  return CreativeManagementHandler()(request,*args,**kwargs)
