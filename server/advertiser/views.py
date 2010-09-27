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

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm

from publisher.models import Site, Account
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
        
class IndexHandler(RequestHandler):
  def get(self):
    campaigns = Campaign.gql("where u = :1 and deleted = :2", users.get_current_user(), False).fetch(10)
    for c in campaigns:
      a = SiteStats.stats_for_days(c, SiteStats.lastdays())
      logging.info(a)
      c.stats = reduce(lambda x, y: x+y, a, SiteStats())
    today = SiteStats.rollup_for_day(campaigns, SiteStats.today())
      
    return render_to_response(self.request, 
      'advertiser/index.html', 
      {'campaigns':campaigns, 
       'today': today,
        'gtee': filter(lambda x: x.campaign_type in ['gtee'], campaigns),
        'promo': filter(lambda x: x.campaign_type in ['promo'], campaigns),
        'network': filter(lambda x: x.campaign_type in ['network'], campaigns), })
      
@login_required     
def index(request,*args,**kwargs):
    return IndexHandler()(request,*args,**kwargs)     

class CreateHandler(RequestHandler):
  def get(self):
    f = CampaignForm()
    return render_to_response(self.request,'advertiser/new.html', {"f": f})

  def post(self):
    f = CampaignForm(data=self.request.POST)
    campaign = f.save(commit=False)
    campaign.u = users.get_current_user() 
    campaign.put()
    return HttpResponseRedirect(reverse('campaign_adgroup_new',kwargs={'campaign_key':campaign.key()}))

@login_required     
def campaign_create(request,*args,**kwargs):
  return CreateHandler()(request,*args,**kwargs)      

class CreateAdGroupHandler(RequestHandler):
  def __call__(self,request,campaign_key):
      self.params = request.POST or request.GET
      self.request = request
      if request.method == "GET":
          return self.get(campaign_key)
      elif request.method == "POST":
          return self.post(campaign_key)

  def get(self, campaign_key):
    f = AdGroupForm()
    sites = Site.gql('where account=:1', Account.current_account())    
    return render_to_response(self.request,'advertiser/new_adgroup.html', {"f": f, "c": Campaign.get(campaign_key), "sites": sites})

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
            
       
@login_required     
def campaign_adgroup_new(request,*args,**kwargs):
  return CreateAdGroupHandler()(request,*args,**kwargs)      

class ShowHandler(RequestHandler):
  def __call__(self,request,campaign_key):
      self.params = request.POST or request.GET
      self.request = request
      if request.method == "GET":
          return self.get(campaign_key)
      elif request.method == "POST":
          return self.post()
          
  def get(self, campaign_key):
    # load the campaign
    campaign = Campaign.get(campaign_key)
    campaign.stats = SiteStats.stats_for_day(campaign, SiteStats.today())
    
    # load the adgroups
    bids = AdGroup.gql("where campaign=:1 and deleted = :2", campaign, False).fetch(50)
    bids.sort(lambda x,y:cmp(x.priority_level, y.priority_level))
    for b in bids:
      b.stats = SiteStats.stats_for_day(b, SiteStats.today())
      
    # no ad groups?
    if len(bids) == 0:
      return HttpResponseRedirect(reverse('campaign_adgroup_new', kwargs={'campaign_key': campaign.key()}))
    else:
      # write response
      return render_to_response(self.request,'advertiser/show.html', 
                                            {'campaign':campaign, 
                                            'bids': bids,
                                            'user':users.get_current_user()})

@login_required     
def campaign_show(request,*args,**kwargs):
 return ShowHandler()(request,*args,**kwargs) 

class EditHandler(RequestHandler):
  def get(self):
    c = Campaign.get(self.request.GET.get("id"))
    f = CampaignForm(instance=c)
    return render_to_response(self.request,'advertiser/edit.html', {"f": f, "campaign": c})

  def post(self):
    print self.request.POST
    c = Campaign.get(self.request.POST.get('id'))
    f = CampaignForm(data=self.request.POST, instance=c)
    if c.u == users.get_current_user():
      f.save(commit=False)
      c.put()
      return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))

@login_required  
def campaign_edit(request,*args,**kwargs):
  return EditHandler()(request,*args,**kwargs)

class PauseHandler(RequestHandler):
  def post(self):
    c = Campaign.get(self.request.POST.get('id',self.request.GET.get('id')))
    if c != None and c.u == users.get_current_user():
      c.active = not c.active
      c.deleted = False
      c.put()
      return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))
  
@login_required
def campaign_pause(request,*args,**kwargs):
  return PauseHandler()(request,*args,**kwargs)
  
class DeleteHandler(RequestHandler):
  def post(self):
    c = Campaign.get(self.request.GET.get('id'))
    if c != None and c.u == users.get_current_user():
      c.active = False
      c.deleted = True
      c.put()
      return HttpResponseRedirect(reverse('advertiser_campaign'))

  
@login_required
def campaign_delete(request,*args,**kwargs):
  return DeleteHandler()(request,*args,**kwargs)  
  
  
class RemoveBidHandler(RequestHandler):
  def post(self):
    for id in self.request.get_all('id') or []:
      b = AdGroup.get(id)
      logging.info(b)
      if b != None and b.campaign.u == users.get_current_user():
        b.deleted = True
        b.put()
        return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':b.campaign.key()}))

class PauseBidHandler(RequestHandler):
  def post(self):
    for id in self.request.POST.getlist('id'):
      b = AdGroup.get(id)
      logging.info(b)
      if b != None and b.campaign.u == users.get_current_user():
        b.active = not b.active
        b.deleted = False
        b.put()
        return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':b.key()}))

class ShowAdGroupHandler(RequestHandler):
  def __call__(self,request,adgroup_key):
    self.params = request.POST or request.GET
    self.request = request
    if request.method == "GET":
      return self.get(adgroup_key)
    elif request.method == "POST":
      return self.post()
  
  def get(self, adgroup_key):
    adgroup = AdGroup.get(adgroup_key)
    creatives = Creative.gql('where ad_group = :1 and deleted = :2 and ad_type in :3', adgroup, False, ["text", "image", "html"]).fetch(50)
    for c in creatives:
      c.stats = SiteStats.stats_for_day(c, SiteStats.today())
    sites = map(lambda x: Site.get(x), adgroup.site_keys)
    for s in sites:
      s.stats = SiteStats.stats_for_day_with_qualifier(adgroup, s, SiteStats.today())
    keywords = []
    
    return render_to_response(self.request,'advertiser/adgroup.html', 
                              {'campaign': adgroup.campaign,
                              'adgroup': adgroup, 
                              'sites': sites,
                              'keywords': keywords, 
                              'creatives': creatives})

    
@login_required   
def campaign_adgroup_show(request,*args,**kwargs):    
  return ShowAdGroupHandler()(request,*args,**kwargs)

class EditBidHandler(RequestHandler):
  def get(self):
    a = AdGroup.get(self.request.GET.get("id"))
    f = AdGroupForm(instance=a)
    params = {"f": f, 
    'sites': Site.gql('where account=:1', Account.current_account()).fetch(100),
    "a": a, 
    "campaign": a.campaign,
    "device_choices":[list(c) for c in AdGroup.DEVICE_CHOICES],
    "min_os_choices":[list(c) for c in AdGroup.MIN_OS_CHOICES],
    "user_types":[list(c) for c in AdGroup.USER_TYPES],
    }
    
    ### TODO: CLEAN UP THIS HACK TO GET THE PROPER SELETIONS
    for s in params['sites']:
      s.checked = s.key() in a.site_keys
      logging.info(params)  
      
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
    if a.campaign.u == users.get_current_user():
      logging.info(f)
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
  
@login_required
def campaign_adgroup_edit(request,*args,**kwargs):
  return EditBidHandler()(request,*args,**kwargs)  

class PauseBidHandler(RequestHandler):
  def post(self):
    for id in self.request.GET.getlist('id'):
      b = AdGroup.get(id)
      logging.info(b)
      if b != None and b.campaign.u == users.get_current_user():
        b.active = not b.active
        b.deleted = False
        b.put()
    return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':b.key()}))


@login_required
def bid_pause(request,*args,**kwargs):
  return PauseBidHandler()(request,*args,**kwargs)
  
class RemoveBidHandler(RequestHandler):
  def post(self):
    for id in self.request.GET.getlist('id') or []:
      b = AdGroup.get(id)
      logging.info(b)
      if b != None and b.campaign.u == users.get_current_user():
        b.deleted = True
        b.put()
    return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':b.campaign.key()}))
  
@login_required
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
  
@login_required
def creative_create(request,*args,**kwargs):
  return AddCreativeHandler()(request,*args,**kwargs)  

class DisplayCreativeHandler(RequestHandler):
  def __call__(self,request,creative_key):
    self.params = request.POST or request.GET
    self.request = request
    if request.method == "GET":
      return self.get(creative_key)
    elif request.method == "POST":
      return self.post()

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
      if c != None and c.ad_group.campaign.u == users.get_current_user():
        c.deleted = True
        c.put()
    return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':c.ad_group.key()}))

@login_required  
def creative_delete(request,*args,**kwargs):
  return RemoveCreativeHandler()(request,*args,**kwargs)
