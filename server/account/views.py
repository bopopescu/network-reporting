import logging, os, re, datetime, hashlib

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

from account.models import Account

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

class AccountHandler(RequestHandler):
  def get(self):
    return render_to_response(self.request,'account/account.html', {'account': Account.current_account()})

  def post(self):
    a = Account.current_account()
    a.adsense_pub_id = self.request.POST.get("adsense_pub_id")
    a.admob_pub_id = self.request.POST.get("admob_pub_id")
    a.put()
    return HttpResponseRedirect("/account")

@login_required     
def index(request,*args,**kwargs):
  return AccountHandler()(request,*args,**kwargs)     

class LogoutHandler(RequestHandler):
  def get(self):
    return HttpResponseRedirect(users.create_logout_url('/main/'))
    
def logout(request,*args,**kwargs):
  return LogoutHandler()(request,*args,**kwargs)