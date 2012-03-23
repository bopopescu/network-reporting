import logging, os, re, datetime, hashlib

from urllib import urlencode
from urllib2 import urlopen

from re import finditer

from google.appengine.api import users
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
# from google.appengine.ext.db import djangoforms
#from common.utils import djangoforms
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse
from common.constants import (  MARKET_SEARCH_KEY,
                                MARKET_URL,
                                )

from django.core.mail import send_mail, EmailMessage

def website_root(request,*args,**kwargs):
    return HttpResponseRedirect("/inventory")
 

def mobile_web_test(request):
    context =  {}

    return render_to_response(request,'website/mobile_web_test.html', context)
    

def droid_market_search(request, qs):
    qs = qs.replace(' ', '+')
    url = MARKET_URL % qs
    import logging
    logging.warning(url)
    raw = urlopen(url).read()
    html_tag = "(?i)<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?>"  
    want = "buy-link"
    #only want the data-* attrs
    attr_parse = "(?P<attr>data-.*?)=\"(?P<val>.*?)\""
    results = []
    #find all tags
    for tag in finditer(html_tag, raw):
        #find tags with 'buy-link' class
        if want in tag.group(0):
            #build response dictionary from these <a class="buy-link..>
            resp_dict = dict(description = "This is an Android Market App")
            for attrval in finditer(attr_parse, tag.group(0)):
                attr = attrval.group('attr')
                val  = attrval.group('val')
                if attr == 'data-docTitle':
                    resp_dict['trackName'] = val
                elif attr == 'data-docId':
                    resp_dict['trackViewUrl'] = val
                elif attr == 'data-docAttribution':
                    resp_dict['artistName'] = val
                elif attr == 'data-docIconUrl':
                    resp_dict['artworkUrl60'] = val
            results.append(resp_dict)
    final = dict(resultCount = len(results),
                 results     = results,
                 )
    return JSONResponse(final)

def website_welcome(request,*args,**kwargs):
    return HttpResponseRedirect("/inventory")
