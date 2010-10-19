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

from django.core.mail import send_mail, EmailMessage

def website_splash(request,*args,**kwargs):
  return render_to_response(request, 'website/splash.html', {'m': request.GET.get("m") or ""})

def website_splash2(request,*args,**kwargs):
  return render_to_response(request, 'website/splash2.html', {'m': request.GET.get("m") or ""})

def website_join(request,*args,**kwargs):
  email = request.POST.get("email_address")
  
  # send a note to beta@mopub.com with the guy's signup
  send_mail('Mailing list', "email=%s" % email, 'olp@mopub.com', ['beta@mopub.com'], fail_silently=True)  
  
  # send a reply
  msg = EmailMessage('Thank you for your interest in MoPub', '''Hello from MoPub!

Thanks again for signing up for MoPub's private beta.  We will get back to you ASAP with 
instructions on how to join. 

Thanks,
The MoPub Team
''', 'MoPub Team <olp@mopub.com>', [email], headers = {'Reply-To': 'beta@mopub.com'})
  msg.send(fail_silently=True)
  return HttpResponseRedirect("/?m=Thanks, we will let you know when an invitation is ready for you.")
  
def website_pending(request,*args,**kwargs):
  send_mail("New User","%s has signed up for an account. Someone please activate him if necessary. https://appengine.google.com/datastore/explorer?submitted=1&app_id=mopub-inc&viewby=gql&query=SELECT+*+FROM+Account+order+by+active&namespace=&options=Run+Query"%request.user.email,'olp@mopub.com',['beta@mopub.com'],fail_silently=True)
  return render_to_response(request, 'website/pending.html')