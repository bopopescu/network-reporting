import logging, os, re, datetime, hashlib

from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse

from common.utils.decorators import whitelist_login_required
from common.utils.cachedquerymanager import CachedQueryManager
# from common.ragendja.auth.decorators import google_login_required as login_required

from account.models import Account
from account.forms import AccountForm
from publisher.models import Site

from account.query_managers import AccountQueryManager
from publisher.query_managers import AdUnitQueryManager

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


class AccountHandler(RequestHandler):
  def get(self,account_form=None):
    if self.params.get("skip"):
      self.account.status = "step4"
      AccountQueryManager().put_accounts(self.account)
      return HttpResponseRedirect(reverse('advertiser_campaign'))

    account_form = account_form or AccountForm(instance=self.account)
    return render_to_response(self.request,'account/account.html', {'account': self.account,
                                                                    'account_form': account_form})

  def post(self):
    account_form = AccountForm(data=self.request.POST, instance=self.account)

    if account_form.is_valid():
      account = account_form.save(commit=False)
      AccountQueryManager().put_accounts(account)
      adunits = AdUnitQueryManager().get_adunits(account=account)
      CachedQueryManager().cache_delete(adunits)
      
      if self.account.status == "step3":
        self.account.status = "step4"
        AccountQueryManager().put_accounts(self.account)
        return HttpResponseRedirect(reverse('advertiser_campaign'))
    
    return self.get(account_form=account_form)    
    # return render_to_response(self.request,'account/account.html', {'account': self.account})

@whitelist_login_required     
def index(request,*args,**kwargs):
  return AccountHandler()(request,*args,**kwargs)     
  

class AccountEditHandler(RequestHandler):
  def get(self,account_form=None):
    account_form = account_form or AccountForm(instance=self.account)
    return render_to_response(self.request,'account/new_account.html',{'account': self.account,
                                                               'account_form' : account_form })
  def post(self):
    account_form = AccountForm(data=self.request.POST,instance=self.account)
    if account_form.is_valid():
      account = account_form.save(commit=False)
      AccountQueryManager().put_accounts(account)
      return HttpResponseRedirect(reverse('publisher_app_create'))
    return self.get(account_form=account_form)  
  
@whitelist_login_required  
def new(request,*args,**kwargs):
  return AccountEditHandler()(request,*args,**kwargs)  

class LogoutHandler(RequestHandler):
  def get(self):
    return HttpResponseRedirect(users.create_logout_url('/main/'))
    
def logout(request,*args,**kwargs):
  return LogoutHandler()(request,*args,**kwargs)
  
def test(request,*args,**kwargs):
  from common.utils.cachedquerymanager import CachedQueryManager
  key = request.GET.get('key')
  response = CachedQueryManager().get([key])
  return response

def test2(request,*args,**kwargs):
  from publisher.query_managers import AdUnitQueryManager
  key = request.GET.get('key')
  manager = AdUnitQueryManager(key)
  adunit = manager.get_adunit()
  adgroups = manager.get_adgroups()

  adgroups = [a for a in adgroups 
                    if a.campaign.active and 
                      (a.campaign.start_date >= SiteStats.today() if a.campaign.start_date else True) 
                      and (a.campaign.end_date <= SiteStats.today() if a.campaign.end_date else True)]
  
  creatives = manager.get_creatives_for_adgroups(adgroups)
  
  return HttpResponse("adgroups: %s <br>creatives: %s"%(adgroups,creatives))
  
  
  
  
# <script> function  finishLoad(){window.location="mopub://finishLoad";} window.onload =  function(){ finishLoad(); }  </script> <script type="text/javascript">  function webviewDidClose(){var img  = new Image();  img.src="/hellothereimclosing/"}  function  webviewDidAppear(){var  img  =  new   Image();  img.src="/hellothereimopening/"}  function  showImage(){var  img  =  document.createElement("img"); img.setAttribute('src','/images/yelp.png'); document.body.appendChild(img);} setTimeout("showImage()",100); function  close(){window.location = "mopub://done"}; //setTimeout("close()",10000); </script>