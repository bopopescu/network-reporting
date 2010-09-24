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

from django.core.mail import send_mail

def website_splash(request,*args,**kwargs):
  logging.info("hi")
  return render_to_response(request, 'splash.html', {'m': request.GET.get("m") or ""})

def website_join(request,*args,**kwargs):
  send_mail('Mailing list', request.POST.get("email_address"), 'olp@mopub.com', ['beta@mopub.com'], fail_silently=False)  
  return HttpResponseRedirect("/?m=Thanks, we will let you know when an invitation is ready for you.")