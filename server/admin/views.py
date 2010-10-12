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

from account.models import Account

import logging

@login_required
def admin_switch_user(request,*args,**kwargs):
  params = request.POST or request.GET
  url = request.META["HTTP_REFERER"]
  # redirect where the request came from
  response = HttpResponseRedirect(url)
  # drop a cookie of the email is the admin user is trying to impersonate
  if users.is_current_user_admin():
    user_key_name = params.get('user_key',None)
    set_cookie = False
    if user_key_name:
      account = Account.get_by_key_name(user_key_name)
      if account:
        response.set_cookie('account_impersonation',params.get('user_key'))
        set_cookie = True
    if not set_cookie:
      response.delete_cookie('account_impersonation')    
  return response