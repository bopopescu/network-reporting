import logging, os, re, datetime, hashlib

from urllib import urlencode

from google.appengine.api import users, memcache, images
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


from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm

from publisher.models import Site, Account
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
        
def gen_graph_url(series, days, title):
  chart_url = "http://chart.apis.google.com/chart?cht=lc&chtt=%s&chs=780x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
    title,
    ','.join(map(lambda x: str(x), series)),
    max(series) * 1.5 if series else 10,
    max(series) * 1.5 if series else 10,
    '|'.join(map(lambda x: x.strftime("%m/%d"), days)))

  return chart_url

class IndexHandler(RequestHandler):
  def get(self):
    days = SiteStats.lastdays(14)
    
    campaigns = Campaign.gql("where u = :1 and deleted = :2", self.account.user, False).fetch(100)
    today = SiteStats()
    for c in campaigns:
      c.all_stats = SiteStats.stats_for_days(c, days)      
      c.stats = reduce(lambda x, y: x+y, c.all_stats, SiteStats())
      today += c.all_stats[-1]
            
    # compute rollups to display at the top
    totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[c.all_stats for c in campaigns])]
    
    chart_urls = {}
    # make a line graph showing impressions
    impressions = [s.impression_count for s in totals]
    chart_urls['imp'] = gen_graph_url(impressions, days, "Total+Daily+Impressions")

    # make a line graph showing clicks
    clicks = [s.click_count for s in totals]
    chart_urls['clk'] = gen_graph_url(clicks, days, "Total+Daily+Clicks")
    
    # make a line graph showing revenue
    revenue = [s.revenue for s in totals]
    chart_urls['rev'] = gen_graph_url(revenue, days, "Total+Revenue")

    promo_campaigns = filter(lambda x: x.campaign_type in ['promo'], campaigns)
    garauntee_campaigns = filter(lambda x: x.campaign_type in ['gtee'], campaigns)
    network_campaigns = filter(lambda x: x.campaign_type in ['network'], campaigns)

    help_text = None
    if network_campaigns:
      if not (self.account.adsense_pub_id or self.account.admob_pub_id):
        help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

    return render_to_response(self.request, 
      'advertiser/index.html', 
      {'campaigns':campaigns, 
       'today': today,
       'chart_urls': chart_urls,
       'gtee': garauntee_campaigns,
       'promo': promo_campaigns,
       'network': network_campaigns,
       'helptext':help_text })
      
@whitelist_login_required     
def index(request,*args,**kwargs):
    return IndexHandler()(request,*args,**kwargs)     

class CreateHandler(RequestHandler):
  def get(self):
    f = CampaignForm()
    return render_to_response(self.request,'advertiser/new.html', {"f": f})

  def post(self):
    f = CampaignForm(data=self.request.POST)
    if f.is_valid():
      campaign = f.save(commit=False)
      campaign.u = self.account.user
      campaign.put()
      return HttpResponseRedirect(reverse('campaign_adgroup_new',kwargs={'campaign_key':campaign.key()}))
    else:
      return render_to_response(self.request,'advertiser/new.html', {"f": f})

@whitelist_login_required     
def campaign_create(request,*args,**kwargs):
  return CreateHandler()(request,*args,**kwargs)      

class CreateAdGroupHandler(RequestHandler):
  def get(self, campaign_key):
    c = Campaign.get(campaign_key)
    adgroup = AdGroup(name="%s Ad Group" % c.name, campaign=c, bid_strategy="cpm", bid=10.0, percent_users=100.0)
    f = AdGroupForm(instance=adgroup)
    sites = Site.gql('where account=:1', self.account)    
    return render_to_response(self.request,'advertiser/new_adgroup.html', {"f": f, "c": c, "sites": sites})

  def post(self, campaign_key):
     c = Campaign.get(campaign_key)
     f = AdGroupForm(data=self.request.POST)
     adgroup = f.save(commit=False)
     adgroup.campaign=c
     adgroup.keywords=filter(lambda k: len(k) > 0, self.request.POST.get('keywords').lower().split('\n'))
     adgroup.site_keys=map(lambda x: db.Key(x), self.request.POST.getlist('sites'))
     adgroup.put()
     
     # if the campaign is a network type, automatically populate the right creative and go back to
     # campaign page
     if c.campaign_type == "network":
       creative = adgroup.default_creative()
       creative.put()
       return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))
     else:
       return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':adgroup.key()}))
            
       
@whitelist_login_required     
def campaign_adgroup_new(request,*args,**kwargs):
  return CreateAdGroupHandler()(request,*args,**kwargs)      

class ShowHandler(RequestHandler):          
  def get(self, campaign_key):
    days = SiteStats.lastdays(14)

    # load the campaign
    campaign = Campaign.get(campaign_key)
    
    # load the adgroups
    bids = AdGroup.gql("where campaign=:1 and deleted = :2", campaign, False).fetch(100)
    bids.sort(lambda x,y:cmp(x.priority_level, y.priority_level))
    for b in bids:
      b.all_stats = SiteStats.stats_for_days(b, days)      
      b.stats = reduce(lambda x, y: x+y, b.all_stats, SiteStats())

    # no ad groups?
    if len(bids) == 0:
      return HttpResponseRedirect(reverse('campaign_adgroup_new', kwargs={'campaign_key': campaign.key()}))
    else:
      # compute rollups to display at the top
      today = SiteStats.rollup_for_day(bids, SiteStats.today())
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[b.all_stats for b in bids])]

      chart_urls = {}
      # make a line graph showing impressions
      impressions = [s.impression_count for s in totals]
      chart_urls['imp'] = gen_graph_url(impressions, days, "Total+Daily+Impressions")

      # make a line graph showing clicks
      clicks = [s.click_count for s in totals]
      chart_urls['clk'] = gen_graph_url(clicks, days, "Total+Daily+Clicks")
      
      # make a line graph showing revenue
      revenue = [s.revenue for s in totals]
      chart_urls['rev'] = gen_graph_url(revenue, days, "Total+Revenue")
      
      help_text = None
      if campaign.campaign_type == 'network':
        if not (self.account.adsense_pub_id or self.account.admob_pub_id):
          help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

      
      # write response
      return render_to_response(self.request,'advertiser/show.html', 
                                            {'campaign':campaign, 
                                            'bids': bids,
                                            'today': today,
                                            'chart_urls': chart_urls,
                                            'user':self.account,
                                            'helptext':help_text})

@whitelist_login_required     
def campaign_show(request,*args,**kwargs):
 return ShowHandler()(request,*args,**kwargs) 

class EditHandler(RequestHandler):
  def get(self):
    c = Campaign.get(self.request.GET.get("id"))
    f = CampaignForm(instance=c)
    return render_to_response(self.request,'advertiser/edit.html', {"f": f, "campaign": c})

  def post(self):
    c = Campaign.get(self.request.POST.get('id'))
    f = CampaignForm(data=self.request.POST, instance=c)
    if c.u == self.account.user:
      f.save(commit=False)
      c.put()
      return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))

@whitelist_login_required  
def campaign_edit(request,*args,**kwargs):
  return EditHandler()(request,*args,**kwargs)

class PauseHandler(RequestHandler):
  def post(self):
    action = self.request.POST.get("action", "pause")
    for id in self.request.POST.getlist('id') or []:
      c = Campaign.get(id)
      if c != None and c.u == self.account.user:
        if action == "pause":
          c.active = False
          c.deleted = False
        elif action == "resume":
          c.active = True
          c.deleted = False
        elif action == "delete":
          c.active = False
          c.deleted = True
        c.put()
    return HttpResponseRedirect(reverse('advertiser_campaign',kwargs={}))
  
@whitelist_login_required
def campaign_pause(request,*args,**kwargs):
  return PauseHandler()(request,*args,**kwargs)
  
class ShowAdGroupHandler(RequestHandler):
  def get(self, adgroup_key):
    days = SiteStats.lastdays(14)

    adgroup = AdGroup.get(adgroup_key)
    creatives = Creative.gql('where ad_group = :1 and deleted = :2 and ad_type in :3', adgroup, False, ["text", "image", "html"]).fetch(50)
    for c in creatives:
      c.all_stats = SiteStats.stats_for_days(c, days)
      c.stats = reduce(lambda x, y: x+y, c.all_stats, SiteStats())
      
    sites = map(lambda x: Site.get(x), adgroup.site_keys)
    for s in sites:
      s.all_stats = SiteStats.stats_for_days_with_qualifier(adgroup, s, days)
      s.stats = reduce(lambda x, y: x+y, s.all_stats, SiteStats())

    # compute rollups to display at the top
    today = SiteStats.stats_for_day(adgroup, SiteStats.today())
    if len(sites) > 0:
      totals = [reduce(lambda x, y: x+y, stats, SiteStats()) for stats in zip(*[s.all_stats for s in sites])]
    else:
      totals = [SiteStats() for d in days]

    chart_urls = {}
    # make a line graph showing impressions
    impressions = [s.impression_count for s in totals]
    chart_urls['imp'] = gen_graph_url(impressions, days, "Total+Daily+Impressions")

    # make a line graph showing clicks
    clicks = [s.click_count for s in totals]
    chart_urls['clk'] = gen_graph_url(clicks, days, "Total+Daily+Clicks")

    # make a line graph showing revenue
    revenue = [s.revenue for s in totals]
    chart_urls['rev'] = gen_graph_url(revenue, days, "Total+Revenue")

    return render_to_response(self.request,'advertiser/adgroup.html', 
                              {'campaign': adgroup.campaign,
                              'adgroup': adgroup, 
                              'creatives': creatives,
                              'today': today,
                              'totals': totals,
                              'chart_urls': chart_urls,
                              'sites': sites})
    
@whitelist_login_required   
def campaign_adgroup_show(request,*args,**kwargs):    
  return ShowAdGroupHandler()(request,*args,**kwargs)

class EditBidHandler(RequestHandler):
  def get(self):
    a = AdGroup.get(self.request.GET.get("id"))
    f = AdGroupForm(instance=a)
    params = {"f": f, 
    'sites': Site.gql('where account=:1', self.account).fetch(100),
    "a": a, 
    "campaign": a.campaign,
    "device_choices":[list(c) for c in AdGroup.DEVICE_CHOICES],
    "min_os_choices":[list(c) for c in AdGroup.MIN_OS_CHOICES],
    "user_types":[list(c) for c in AdGroup.USER_TYPES],
    }
    
    ### TODO: CLEAN UP THIS HACK TO GET THE PROPER SELETIONS
    for s in params['sites']:
      s.checked = s.key() in a.site_keys
      
    for device in params['device_choices']:
      device.append(device[0] in a.devices)
    for os in params['min_os_choices']:
      os.append(os[0] in a.min_os)
      for device in params['device_choices']:
        device.append(device[0] in a.devices)
    for u in params['user_types']:
      u.append(u[0] in a.active_user)  
    return render_to_response(self.request,'advertiser/adgroup_edit.html', params)

  def post(self):
    key = self.request.GET.get("id")
    a = AdGroup.get(key)
    f = AdGroupForm(data=self.request.POST, instance=a)
    if a.campaign.u == self.account.user:
      a.site_keys = map(lambda x:db.Key(x), self.request.POST.getlist("site_keys"))
      a.keywords = filter(lambda k: len(k) > 0, self.request.POST.get('keywords').lower().split('\n'))
      a.devices = self.request.POST.getlist('devices')
      a.min_os = self.request.POST.getlist('min_os')
      a.country = self.request.POST.get('country',None)
      a.state = self.request.POST.get('state',None)
      a.city = self.request.POST.get('city',None)
      a.active_user = self.request.POST.getlist('active_users')
      a.active_app = self.request.POST.getlist('active_apps')
      f.save(commit=False)
      a.put()
      return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':a.key()}))
  
@whitelist_login_required
def campaign_adgroup_edit(request,*args,**kwargs):
  return EditBidHandler()(request,*args,**kwargs)  

class PauseBidHandler(RequestHandler):
  def post(self):
    action = self.request.POST.get("action", "pause")
    for id in self.request.POST.getlist('id') or []:
      c = AdGroup.get(id)
      if c != None and c.campaign.u == self.account.user:
        if action == "pause":
          c.active = False
          c.deleted = False
        elif action == "resume":
          c.active = True
          c.deleted = False
        elif action == "delete":
          c.active = False
          c.deleted = True
        c.put()
    return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.campaign.key()}))


@whitelist_login_required
def bid_pause(request,*args,**kwargs):
  return PauseBidHandler()(request,*args,**kwargs)
  
class RemoveBidHandler(RequestHandler):
  def post(self):
    c = None
    for id in self.request.POST.getlist('id') or []:
      b = AdGroup.get(id)
      c = b.campaign
      if b != None and b.campaign.u == self.account.user:
        b.deleted = True
        b.put()
    return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))
  
@whitelist_login_required
def bid_delete(request,*args,**kwargs):
  return RemoveBidHandler()(request,*args,**kwargs)

#
# Creative management
#
class AddCreativeHandler(RequestHandler):
  def post(self):
    ad_group = AdGroup.get(self.request.POST.get('id'))
    if self.request.POST.get("headline"):
      creative = TextCreative(ad_group=ad_group,
      headline=self.request.POST.get('headline'),
      line1=self.request.POST.get('line1'),
      line2=self.request.POST.get('line2'),
      url=self.request.POST.get('url'),
      display_url=self.request.POST.get('display_url'))
      creative.put()
    elif self.request.FILES.get("image"):
      img = images.Image(self.request.FILES.get("image").read())
      fp = ImageCreative.get_format_predicates_for_image(img)
      if fp is not None:
        img.im_feeling_lucky()
        creative = ImageCreative(ad_group=ad_group,
                                  ad_type="image",
                                  format_predicates=fp,
                                  url=self.request.POST.get('url'),
                                  image=db.Blob(img.execute_transforms()),
                                  image_width=img.width,
                                  image_height=img.height)
        creative.put()
    elif self.request.POST.get("html_name"):
      creative = HtmlCreative(ad_group=ad_group,
        ad_type="html",
        html_name=self.request.POST.get('html_name'),
        html_data=self.request.POST.get('html_data'))
      creative.put()
    return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':ad_group.key()}))
  
@whitelist_login_required
def creative_create(request,*args,**kwargs):
  return AddCreativeHandler()(request,*args,**kwargs)  

class DisplayCreativeHandler(RequestHandler):
  def get(self, creative_key):
    c = Creative.get(creative_key)
    if c and c.ad_type == "image" and c.image:
      return HttpResponse(c.image,content_type='image/png')
    return HttpResponse('NOOOOOOOOOOOO IMAGE')

def creative_image(request,*args,**kwargs):
  return DisplayCreativeHandler()(request,*args,**kwargs)

class RemoveCreativeHandler(RequestHandler):
  def post(self):
    ids = self.request.POST.getlist('id')
    for creative_key in ids:
      c = Creative.get(creative_key)
      if c != None and c.ad_group.campaign.u == self.account.user:
        c.deleted = True
        c.put()
    return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':c.ad_group.key()}))

@whitelist_login_required  
def creative_delete(request,*args,**kwargs):
  return RemoveCreativeHandler()(request,*args,**kwargs)
