import logging, os, re, datetime, hashlib

import urllib
urllib.getproxies_macosx_sysconf = lambda: {}
from urllib import urlencode
from operator import itemgetter

from google.appengine.api import users
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

from publisher.models import Account, App
from advertiser.models import Campaign, AdGroup, Creative, TextAndTileCreative, ImageCreative

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

class IndexHandler(RequestHandler):
  def get(self):
    return render_to_response(self.request,'exchange/index.html', {})

@whitelist_login_required     
def index(request,*args,**kwargs):
  return IndexHandler()(request,*args,**kwargs)     

class ScheduleHandler(RequestHandler):
  def get(self):
    apps = App.gql("where account = :1 and deleted = :2", self.account, False).fetch(50)
    #TODO: Error handling when no app exists (user shouldn't be on this page)
    for a in apps:
      try:
        a.creative = Creative.get(a.exchange_creative.key())
      except:
        None
    
    return render_to_response(self.request,'exchange/schedule.html',
      {'apps': apps,
      'app': apps[0]})

  def post(self):
    if self.request.POST.get('cancel'):
      return HttpResponseRedirect(reverse('exchange_index',kwargs={}))
      
    app = App.get(self.request.POST.get('id'))
    creative = None
    if self.request.POST.get("line1"):
      creative = TextAndTileCreative(
      line1=self.request.POST.get('line1'),
      line2=self.request.POST.get('line2'))
      creative.put()
      
    if creative != None:
      try:
        old_creative = Creative.get(app.exchange_creative.key())
        old_creative.delete()
      except:
        None
      app.exchange_creative = creative
      app.put()
    return HttpResponseRedirect(reverse('exchange_index',kwargs={}))
    

@whitelist_login_required     
def schedule(request,*args,**kwargs):
  return ScheduleHandler()(request,*args,**kwargs)     

