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
  email = request.POST.get("email_address")
  send_mail('Mailing list', email, 'olp@mopub.com', ['beta@mopub.com'], fail_silently=False)  
  send_mail('Thank you for your interest in MoPub', '''
Dear user,
Thanks again for signing up for MoPub's private beta.  Please help us out by replying to this email
with some additional information about your apps and your mobile business.  Particularly, we'd be
interested in the following:
  
  - Your apps (names, URLs, etc.) 
  - Platforms you develop for (iPhone, Android, etc.)
  - Approximate traffic 
  - Special advertising needs or ideas
  
This will help us prioritize your request in the queue.  

Thanks,
The MoPub Team
''', 'MoPub Team <olp@mopub.com>', ['beta@mopub.com'], fail_silently=False)
  return HttpResponseRedirect("/?m=Thanks, we will let you know when an invitation is ready for you.")