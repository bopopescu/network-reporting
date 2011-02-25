import logging, os, re, datetime, hashlib

from urllib import urlencode

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

from django.core.mail import send_mail, EmailMessage

def website_root(request,*args,**kwargs):
    return HttpResponseRedirect("/inventory")

def website_welcome(request,*args,**kwargs):
    return HttpResponseRedirect("/inventory")
