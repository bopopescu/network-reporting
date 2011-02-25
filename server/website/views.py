import logging, os, re, datetime, hashlib

from urllib import urlencode
from urllib2 import urlopen
                     

from re import finditer

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
from common.constants import (  MARKET_SEARCH_KEY,
                                MARKET_URL,
                                )
from common.utils.decorators import webdec

from django.core.mail import send_mail, EmailMessage

def website_root(request,*args,**kwargs):
  return HttpResponseRedirect("/inventory")

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
  return HttpResponseRedirect("http://www.mopub.com/thanks")
  
def website_pending(request,*args,**kwargs):
  send_mail("New User","%s has signed up for an account. Someone please activate him if necessary. https://appengine.google.com/datastore/explorer?submitted=1&app_id=mopub-inc&viewby=gql&query=SELECT+*+FROM+Account+order+by+active&namespace=&options=Run+Query"%request.user.email,'olp@mopub.com',['beta@mopub.com'],fail_silently=True)
  return render_to_response(request, 'website/pending.html')

@webdec()
def droid_market_search( qs ): 
    qs = qs.replace( ' ', '+' )
    url = MARKET_URL % qs
    import logging
    logging.warning( url )
    raw = urlopen( url ).read()
    html_tag = "(?i)<\/?\w+((\s+\w+(\s*=\s*(?:\".*?\"|'.*?'|[^'\">\s]+))?)+\s*|\s*)\/?>"  
    want = "buy-link"
    #only want the data-* attrs
    attr_parse = "(?P<attr>data-.*?)=\"(?P<val>.*?)\""
    results = []
    #find all tags
    for tag in finditer( html_tag, raw ):
        #find tags with 'buy-link' class
        if want in tag.group( 0 ):
            #build response dictionary from these <a class="buy-link..>
            resp_dict = dict( description = "This is an Android Market App" )
            for attrval in finditer( attr_parse, tag.group( 0 ) ):
                attr = attrval.group( 'attr' )
                val  = attrval.group( 'val' )
                if attr == 'data-docTitle':
                    resp_dict[ 'trackName' ] = val
                elif attr == 'data-docId':
                    resp_dict[ 'trackViewUrl' ] = val
                elif attr == 'data-docAttribution':
                    resp_dict[ 'artistName' ] = val
                elif attr == 'data-docIconUrl':
                    resp_dict[ 'artworkUrl60' ] = val
            results.append( resp_dict )
    final = dict( resultCount = len( results ),
                  results     = results,
                  )
    return JSONResponse( final ) 



    # a class="buy-link"
    #
    # { resultCount : <blah>, 
    #   results: [
    #               { artworkUrl60 : <blah>, data-docTitle
    #                 trackName:  <blah>, data-docId
    #                 artistName: <blah>, data-docAttribution
    #                 trackViewUrl: <blah>, data-docIconUrl
    #                 description: <blah>, blahhhhh
    #                }, ....
    #            ]
    # }
