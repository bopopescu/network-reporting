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

from advertiser.models import Campaign, AdGroup, Creative
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
      c.stats = SiteStats.stats_for_day(c, SiteStats.today())
    return render_to_response(self.request,'advertiser/index.html', {'campaigns':campaigns, 'user':users.get_current_user()})
      
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
    return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':campaign.key()}))

@login_required     
def campaign_create(request,*args,**kwargs):
  return CreateHandler()(request,*args,**kwargs)      

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
    for b in bids:
      b.stats = SiteStats.stats_for_day(b, SiteStats.today())

    # write response
    return render_to_response(self.request,'advertiser/show.html', 
                                          {'campaign':campaign, 
                                          'bids': bids,
                                          'sites': Site.gql('where account=:1', Account.current_account()),
                                          'user':users.get_current_user()})

@login_required     
def campaign_show(request,*args,**kwargs):
 return ShowHandler()(request,*args,**kwargs) 
  
class AddBidHandler(RequestHandler):
 def post(self):
    c = Campaign.get(self.request.POST.get('id'))
    adgroup = AdGroup(campaign=c,
      name=self.request.POST.get('name'),
      bid=float(self.request.POST.get('bid')),
      keywords=filter(lambda k: len(k) > 0, self.request.POST.get('keywords').lower().split('\n')),
      site_keys=map(lambda x: db.Key(x), self.request.POST.getlist('sites')))
    adgroup.put()
    return HttpResponseRedirect(reverse('advertiser_campaign_show',kwargs={'campaign_key':c.key()}))

@login_required  
def bid_create(request,*args,**kwargs):
  return AddBidHandler()(request,*args,**kwargs)   

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
    creatives = Creative.gql('where ad_group = :1 and deleted = :2', adgroup, False).fetch(50)
    for c in creatives:
      c.stats = SiteStats.stats_for_day(c, SiteStats.today())
    sites = map(lambda x: Site.get(x), adgroup.site_keys)
    for s in sites:
      s.stats = SiteStats.stats_for_day_with_qualifier(adgroup, s.key(), SiteStats.today())
    keywords = map(lambda k: {"keyword": k, "stats": SiteStats.stats_for_day_with_qualifier(adgroup, k, SiteStats.today())}, adgroup.keywords)
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
    "campaign": a.campaign}
    for s in params['sites']:
      s.checked = s.key() in a.site_keys
      logging.info(params)  
    return render_to_response(self.request,'advertiser/adgroup_edit.html', params)

  def post(self):
    key = self.request.GET.get("id")
    a = AdGroup.get(key)
    f = AdGroupForm(data=self.request.POST, instance=a)
    if a.campaign.u == users.get_current_user():
      logging.info(f)
      a.site_keys = map(lambda x:db.Key(x), self.request.POST.getlist("site_keys"))
      a.keywords = filter(lambda k: len(k) > 0, self.request.POST.get('keywords').lower().split('\n'))
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
      creative = Creative(ad_group=ad_group,
      headline=self.request.POST.get('headline'),
      line1=self.request.POST.get('line1'),
      line2=self.request.POST.get('line2'),
      url=self.request.POST.get('url'),
      display_url=self.request.POST.get('display_url'))
      creative.put()
    elif self.request.FILES.get("image"):
      img = images.Image(self.request.FILES.get("image").read())
      fp = Creative.get_format_predicates_for_image(img)
      if fp is not None:
        img.im_feeling_lucky()
        creative = Creative(ad_group=ad_group,
                                  ad_type="image",
                                  format_predicates=fp,
                                  url=self.request.POST.get('url'),
                                  image=db.Blob(img.execute_transforms()),
                                  image_width=img.width,
                                  image_height=img.height)
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