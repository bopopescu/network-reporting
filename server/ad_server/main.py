# !/usr/bin/env python

# TODO: PLEASE HAVE THIS FIX DJANGO PROBLEMS
# import logging, os, sys
# os.environ["DJANGO_SETTINGS_MODULE"] = "settings"
# 
# from google.appengine.dist import use_library
# use_library("django", "1.1") # or use_library("django", "1.0") if you're using 1.0
# 
# from django.conf import settings
# settings._target = None

from appengine_django import LoadDjango
LoadDjango()
import os
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None

# END TODO: PLEASE HAVE THIS FIX DJANGO PROBLEMS

import wsgiref.handlers
import cgi
import logging
import os
import re
import datetime
import hashlib
import traceback
import random
import hashlib
import time
import base64, binascii
from django.utils import simplejson

from string import Template
from urllib import urlencode, unquote

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache

from publisher.models import *
from advertiser.models import *
from reporting.models import *






CRAWLERS = ["Mediapartners-Google,gzip(gfe)", "Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'
DOMAIN = 'ads.mopub.com'
# DOMAIN = 'localhost:8080'
#
# Ad auction logic
# The core of the whole damn thing
#
def memcache_key(udid,datetime,db_key):
  return '%s:%s:%s'%(udid,datetime.date().strftime('%y%m%d'),db_key)


class AdAuction(object):
  MAX_ADGROUPS = 30

  # Runs the auction itself.  Returns the winning creative, or None if no creative matched
  @classmethod
  def run(cls, **kw):
    now = kw["now"]
    site = kw["site"]

    keywords = kw["q"]
    geo_predicates = AdAuction.geo_predicates_for_rgeocode(kw["addr"])
    device_predicates = AdAuction.device_predicates_for_request(kw["request"])
    format_predicates = AdAuction.format_predicates_for_format(kw["format"])
    exclude_params = kw["excluded_creatives"]
    excluded_predicates = AdAuction.exclude_predicates_params(exclude_params)
    logging.warning("keywords=%s, geo_predicates=%s, device_predicates=%s, format_predicates=%s" % (keywords, geo_predicates, device_predicates, format_predicates))

    # Matching strategy: 
    # 1) match all ad groups that match the placement that is in question, sort by priority
    # 2) throw out ad groups owned by campaigns that have exceeded budget or are paused
    # 3) throw out ad groups that restrict by keywords and do not match the keywords
    # 4) throw out ad groups that do not match device and geo predicates
    ad_groups = AdGroup.gql("where site_keys = :1 and active = :2 and deleted = :3", site.key(), True, False).fetch(AdAuction.MAX_ADGROUPS)
    logging.warning("ad groups: %s" % ad_groups)
    
    # campaign exclusions... budget + time
    ad_groups = [a for a in ad_groups 
                      if a.campaign.budget is None or 
                      SiteStats.stats_for_day(a.campaign, SiteStats.today()).revenue < a.campaign.budget]
    # ad_groups = filter(lambda a: a.campaign.budget is None or SiteStats.stats_for_day(a.campaign, SiteStats.today()).revenue < a.campaign.budget, ad_groups)
    logging.warning("removed over budget, now: %s" % ad_groups)
    ad_groups = [a for a in ad_groups 
                      if a.campaign.active and 
                        (a.campaign.start_date >= SiteStats.today() if a.campaign.start_date else True) 
                        and (a.campaign.end_date <= SiteStats.today() if a.campaign.end_date else True)]
    # ad_groups = filter(lambda a: a.campaign.active and (a.campaign.start_date >= SiteStats.today() if a.campaign.start_date else True) and (a.campaign.end_date <= SiteStats.today() if a.campaign.end_date else True), ad_groups)
    logging.warning("removed non running campaigns, now: %s" % ad_groups)
    
    # ad group request-based targeting exclusions
    ad_groups = [a for a in ad_groups 
                    if not a.keywords or set(keywords).intersection(a.keywords) > set()]
    # filter(lambda a: len(a.keywords) == 0 or set(keywords).intersection(a.keywords) > set(), ad_groups)
    
    logging.warning("removed keyword non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(geo_predicates).intersection(a.geo_predicates) > set(), ad_groups)
    ad_groups = [a for a in ad_groups
                    if set(geo_predicates).intersection(a.geographic_predicates) > set()]
    logging.warning("removed geo non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(device_predicates).intersection(a.device_predicates) > set(), ad_groups)
    logging.warning("removed device non-matches, now: %s" % ad_groups)
    
    # TODO: frequency capping and other user / request based randomizations
    udid = kw["udid"]
        
    # if any ad groups were returned, find the creatives that match the requested format in all candidates
    if len(ad_groups) > 0:
      all_creatives = Creative.gql("where ad_group in :1 and format_predicates in :2 and active = :3 and deleted = :4", 
        map(lambda x: x.key(), ad_groups), format_predicates, True, False).fetch(AdAuction.MAX_ADGROUPS)
      

      if len(all_creatives) > 0:
        # for each priority_level, perform an auction among the various creatives 
        max_priority = max(c.ad_group.priority_level for c in all_creatives)
        for p in range(max_priority + 1):
          players = filter(lambda c: c.ad_group.priority_level == p, all_creatives)
          players.sort(lambda x,y: cmp(y.e_cpm(), x.e_cpm()))
          
          while players:
            winning_ecpm = max(c.e_cpm() for c in players) if len(players) > 0 else 0
            logging.warning("auction at priority=%d: %s, max eCPM=%.2f" % (p, players, winning_ecpm))
      
            # if the winning creative exceeds the ad unit's threshold cpm for the
            # priority level, then we have a winner
            if winning_ecpm >= site.threshold_cpm(p):
              # retain all creatives with comparable eCPM and randomize among them
              winners = filter(lambda x: x.e_cpm() >= winning_ecpm, players)
              logging.warning("%02d winners: %s"%(len(winners),winners))
              
              campaigns = set([c.ad_group.campaign for c in winners if not c.ad_group.deleted and not c.ad_group.campaign.deleted])
              logging.warning("campaigns: %s"%campaigns)
              
              # find out which ad groups are eligible
              ad_groups = set([c.ad_group for c in winners])
              logging.warning("eligible ad_groups: %s" % ad_groups)
                            
              creatives = [c for c in all_creatives if c.ad_group.key() in [a.key() for a in ad_groups]]
            
              # exclude according to the exclude parameter must do this after determining adgroups
              # so that we maintain the correct order for user bucketing
              logging.debug("eligible creatives: %s %s" % (winners,exclude_params))
              winners = [c for c in winners if not (c.ad_type in exclude_params)]  
              logging.debug("eligible creatives after exclusions: %s" % winners)
            
              # calculate the user experiment bucket
              user_bucket = hash(udid+','.join([str(c.ad_group.key()) for ad_group in ad_groups])) % 100 # user gets assigned a number between 0-99 inclusive
              logging.warning("the user bucket is: #%d",user_bucket)
          
              # determine in which ad group the user falls into to
              # otherwise give creatives in the other adgroups a shot
              # TODO: fix the stagger method how do we get 3 ads all at 100%
              # currently we just mod by 100 such that there is wrapping
              start_bucket = 0
              winning_ad_groups = []
              ad_groups = list(ad_groups)
              
              # sort the ad groups by the percent of users desired, this allows us 
              # to do the appropriate wrapping of the number line if they are nicely behaved
              # TODO: finalize this so that we can do things like 90% and 15%. We need to decide
              # what happens in this case, unclear what the intent of this is.
              ad_groups.sort(lambda x,y: cmp(x.percent_users if x.percent_users else 100.0,y.percent_users if y.percent_users else 100.0))
              for ad_group in ad_groups:
                percent_users = ad_group.percent_users if not (ad_group.percent_users is None) else 100.0
                if start_bucket <= user_bucket and user_bucket < (start_bucket + percent_users):
                  winning_ad_groups.append(ad_group)
                start_bucket += percent_users
                start_bucket = start_bucket % 100 
                                
              # TODO: user based frequency caps
              user_keys = []
              for adgroup in winning_ad_groups:
                user_adgroup_daily_key = memcache_key(udid,now,adgroup.key())
                user_keys.append(user_adgroup_daily_key)
              frequency_cap_dict = memcache.get_multi(user_keys)    
              
              winning_ad_groups_new = []
              logging.warning("winning ad groups: %s"%winning_ad_groups)
              for adgroup in winning_ad_groups:
                logging.warning("frequency cap %d"%adgroup.daily_frequency_cap)   
                if adgroup.daily_frequency_cap > 0: # not 0
                  user_adgroup_daily_key = memcache_key(udid,now,adgroup.key())
                  # pull out the impression count from memcache, otherwise its assumed to be 0
                  if user_adgroup_daily_key in frequency_cap_dict:
                    impression_cnt = int(frequency_cap_dict[user_adgroup_daily_key])
                  else:
                    impression_cnt = 0 
                  logging.warning("impression: %d max: %d"%(impression_cnt,adgroup.daily_frequency_cap))   
                  if impression_cnt < adgroup.daily_frequency_cap:
                    winning_ad_groups_new.append(adgroup)
                else:
                  winning_ad_groups_new.append(adgroup)    
              winning_ad_groups = winning_ad_groups_new
              logging.warning("winning ad groups after frequency capping: %s"%winning_ad_groups)

              # if there is a winning/eligible adgroup find the appropriate creative for it
              if winning_ad_groups:
                logging.warning("winner ad_groups: %s"%winning_ad_groups)
              
                if winning_ad_groups:
                  winners = [winner for winner in winners if winner.ad_group in winning_ad_groups]

                if winners:
                  logging.debug('winners %s'%winners)
                  random.shuffle(winners)
                  logging.debug('random winners %s'%winners)
          
                  # winner
                  winner = winners[0]
                  logging.warning("winning creative = %s" % winner)
                  return winner
                else:
                  logging.warning('taking away some players not in %s'%ad_groups)
                  logging.warning('current players: %s'%players)
                  players = [c for c in players if not c.ad_group in ad_groups]  
                  logging.warning('remaining players %s'%players)
                  
              else:
                logging.warning('taking away some players not in %s'%ad_groups)
                logging.warning('current players: %s'%players)
                players = [c for c in players if not c.ad_group in ad_groups]  
                logging.warning('remaining players %s'%players)
                

    # nothing... failed auction
    logging.debug("auction failed, returning None")
    return None
    
  @classmethod
  def geo_predicates_for_rgeocode(c, r):
    if len(r) == 0:
      return ["country_name=*"]
    elif len(r) == 2:
      return ["region_name=%s,country_name=%s" % (r[0], r[1]),
              "country_name=%s" % r[1],
              "country_name=*"]
    elif len(r) == 3:
      return ["city_name=%s,region_name=%s,country_name=%s" % (r[0], r[1], r[2]),
              "region_name=%s,country_name=%s" % (r[1], r[2]),
              "country_name=%s" % r[2],
              "country_name=*"]

  @classmethod
  def device_predicates_for_request(c, req):
    ua = req.headers["User-Agent"]
    if "Android" in ua:
      return ["platform_name=android", "platform_name=*"]
    elif "iPhone" in ua:
      return ["platform_name=iphone", "platform_name=*"]
    else:
      return ["platform_name=*"]

  @classmethod
  def format_predicates_for_format(c, f):
    # TODO: does this always work for any format
    return ["format=%dx%d" % (f[0], f[1]), "format=*"]
  
  @classmethod
  def exclude_predicates_params(c,params):
    return ["exclude=%s"%param for param in params]    
#
# Primary ad auction handler 
# -- Handles ad request parameters and normalizes for the auction logic
# -- Handles rendering the winning creative into the right HTML
#
class AdHandler(webapp.RequestHandler):
  
  # AdSense: Format properties: width, height, adsense_format, num_creatives
  FORMAT_SIZES = {
    "300x250_as": (300, 250, "300x250_as", 3),
    "320x50_mb": (320, 50, "320x50_mb", 1),
    "728x90_as": (728, 90, "728x90_as", 2),
    "468x60_as": (468, 60, "468x60_as", 1),
    "300x250": (300, 250, "300x250_as", 3),
    "320x50": (320, 50, "320x50_mb", 1),
    "728x90": (728, 90, "728x90_as", 2),
    "468x60": (468, 60, "468x60_as", 1),
    "320x480": (320, 480, "300x250_as", 1),
  }
  
  def get(self):
    id = self.request.get("id")
    site = Site.site_by_id(id) if id else None
    now = datetime.datetime.now()
    
    
    # the user's site key was not set correctly...
    if site is None:
      self.error(500)
      self.response.out.write("Publisher site key %s not valid" % id)
      return
    
    # get keywords 
    # q = [sz.strip() for sz in ("%s\n%s" % (self.request.get("q").lower() if self.request.get("q") else '', site.keywords if site.k)).split("\n") if sz.strip()]
    keywords = []
    if site.keywords and site.keywords != 'None':
      keywords += site.keywords.split(',')
    if self.request.get("q"):
      keywords += self.request.get("q").lower().split(',')
    q = keywords
    logging.warning("keywords are %s" % keywords)

    # get format
    f = self.request.get("f") or "320x50"
    format = self.FORMAT_SIZES.get(f)
    logging.debug("format is %s (requested '%s')" % (format, f))
    
    # look up lat/lon
    addr = self.rgeocode(self.request.get("ll")) if self.request.get("ll") else ()      
    logging.warning("geo is %s (requested '%s')" % (addr, self.request.get("ll")))
    
    # get creative exclusions usually used to exclude iAd because it has already failed
    excluded_creatives = self.request.get("exclude")
    
    #get udid we should hash it if its not already hashed
    udid = self.request.get("udid")
    
    # create a unique request id, but only log this line if the user agent is real
    request_id = hashlib.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
    if str(self.request.headers['User-Agent']) not in CRAWLERS:
      logging.info('OLP ad-request {"request_id": "%s", "remote_addr": "%s", "q": "%s", "user_agent": "%s", "udid":"%s" }' % (request_id, self.request.remote_addr, self.request.query_string, self.request.headers["User-Agent"], udid))



    # get winning creative
    c = AdAuction.run(request=self.request, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, udid=udid, request_id=request_id, now=now)
    
    # output the request_id and the winning creative_id if an impression happened
    if c:
      user_adgroup_daily_key = memcache_key(udid,now,c.ad_group.key())
      logging.warning("user_adgroup_daily_key: %s"%user_adgroup_daily_key)
      memcache.incr(user_adgroup_daily_key, delta=1, namespace=None, initial_value=0)
      
      logging.info('OLP ad-auction {"id": "%s", "c": "%s", "request_id": "%s", "udid": "%s"}' % (id, c.key(), request_id, udid))

      # create an ad clickthrough URL
      ad_click_url = "http://%s/m/aclk?id=%s&c=%s&req=%s" % (DOMAIN,id, c.key(), request_id)
      self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
      
      # render the creative 
      self.response.out.write(self.render_creative(c, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, request_id=request_id, v=int(self.request.get('v') or 0)))
    else:
      self.response.out.write(self.render_creative(c, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, request_id=request_id, v=int(self.request.get('v') or 0)))
      
  #
  # Templates
  #
  TEMPLATES = {
    "adsense": Template("""<html>
                            <head>
                              <title>$title</title>
                              $finishLoad
                              <script>
                                function webviewDidClose(){} 
                                function webviewDidAppear(){} 
                              </script>
                            </head>
                            <body style="margin: 0;width:${w}px;height:${h}px;" >
                              <script type="text/javascript">window.googleAfmcRequest = {client: '$client',ad_type: 'text_image', output: 'html', channel: '',format: '$adsense_format',oe: 'utf8',color_border: '336699',color_bg: 'FFFFFF',color_link: '0000FF',color_text: '000000',color_url: '008000',};</script> 
                              <script type="text/javascript" src="http://pagead2.googlesyndication.com/pagead/show_afmc_ads.js"></script>  
                              $trackingPixel
                            </body>
                          </html> """),
    "iAd": Template("iAd"),
    "clear": Template(""),
    "text": Template("""<html>\
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            function webviewDidClose(){} 
                            function webviewDidAppear(){} 
                          </script>
                          <title>$title</title>
                        </head>\
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">\
                          <div class="creative"><div style="padding: 5px 10px;"><a href="$url" class="creative_headline">$headline</a><br/>$line1 $line2<br/><span class="creative_url"><a href="$url">$display_url</a></span></div></div>\
                          $trackingPixel
                        </body> </html> """),
    "image":Template("""<html>\
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 20px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            function webviewDidClose(){} 
                            function webviewDidAppear(){} 
                          </script>
                        </head>
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">\
                          <a href="$url"><img src="$image_url" width=$w height=$h/></a>
                        </body>   $trackingPixel</html> """),
    "admob": Template("""<html><head>
                        $finishLoad
                        <script>
                          function webviewDidClose(){} 
                          function webviewDidAppear(){} 
                        </script>
                        <title>$title</title>
                        </head><body style="margin: 0;padding:0;">
                        <script type="text/javascript">
                        var admob_vars = {
                         pubid: '$client', // publisher id
                         bgcolor: '000000', // background color (hex)
                         text: 'FFFFFF', // font-color (hex)
                         ama: false, 
                         test: false
                        };
                        </script>
                        <script type="text/javascript" src="http://mmv.admob.com/static/iphone/iadmob.js"></script>                        
                        </body>$trackingPixel</html>"""),
    "html":Template("""<html><title>$title</title><head>                    
                        <script>
                          function webviewDidClose(){} 
                          function webviewDidAppear(){} 
                        </script></head>
                        <body style="margin: 0;padding:0;background-color:white">${html_data}$trackingPixel</body></html>"""),
  }
  def render_creative(self, c, **kwargs):
    if c:
      logging.debug("rendering: %s" % c.ad_type)
      format = kwargs["format"]

      params = kwargs
      params.update(c.__dict__.get("_entity"))

      if c.ad_type == "adsense":
        params.update({"title": ','.join(kwargs["q"]), "adsense_format": format[2], "w": format[0], "h": format[1], "client": kwargs["site"].account.adsense_pub_id})
        # self.response.headers.add_header("X-Launchpage","http://googleads.g.doubleclick.net")
      elif c.ad_type == "admob":
        params.update({"title": ','.join(kwargs["q"]), "w": format[0], "h": format[1], "client": kwargs["site"].account.admob_pub_id})
        self.response.headers.add_header("X-Launchpage","http://c.admob.com/")
      elif c.ad_type == "image":
        params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
      elif c.ad_type == "html":
        params.update({"html_data": kwargs["html_data"]})
        
      if kwargs["q"] or kwargs["addr"]:
        params.update(title=','.join(kwargs["q"]+list(kwargs["addr"])))
      else:
        params.update(title='')
        
      if kwargs["v"] >= 2:  
        params.update(finishLoad='<script>function finishLoad(){window.location="mopub://finishLoad";} window.onload = function(){finishLoad();} </script>')
      else:
        params.update(finishLoad='')  
      
      
      if c.tracking_url:
        params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>'%c.tracking_url)
      else:
        params.update(trackingPixel='')  
      
      # indicate to the client the winning creative type, in case it is natively implemented (iad, clear)
      self.response.headers.add_header("X-Adtype", str(c.ad_type))
      self.response.headers.add_header("X-Backfill", str(c.ad_type))
      
      if str(c.ad_type) == "iAd":
        self.response.headers.add_header("X-Failurl",self.request.url+'&exclude='+str(c.ad_type))
      
      # render the HTML body
      self.response.out.write(self.TEMPLATES[c.ad_type].safe_substitute(params))
    else:
      self.response.headers.add_header("X-Adtype", "clear")
      self.response.headers.add_header("X-Backfill", "clear")
    
    # make sure this response is not cached by the client  
    self.response.headers.add_header('Cache-Control','no-cache')  
  
  def rgeocode(self, ll):
    url = "http://maps.google.com/maps/geo?%s" % urlencode({"q": ll, 
      "key": MAPS_API_KEY, 
      "sensor": "false", 
      "output": "json"})
    json = fetch(url).content
    try:
      geocode = simplejson.loads(json)

      if geocode.get("Placemark"):
        for placemark in geocode["Placemark"]:
          if placemark.get("AddressDetails").get("Accuracy") == 8:
            logging.debug("rgeocode Accuracy == 8")
          
            country = placemark.get("AddressDetails").get("Country")
            administrativeArea = country.get("AdministrativeArea") if country else None
            subAdministrativeArea = administrativeArea.get("SubAdministrativeArea") if administrativeArea else None
            locality = (subAdministrativeArea.get("Locality") if subAdministrativeArea else administrativeArea.get("Locality")) if administrativeArea else None
            logging.debug("country=%s, administrativeArea=%s, subAdminArea=%s, locality=%s" % (country, administrativeArea, subAdministrativeArea, locality))
          
            return (locality.get("LocalityName") if locality else "", 
                    administrativeArea.get("AdministrativeAreaName") if administrativeArea else "",
                    country.get("CountryNameCode") if country else "")
        return ()
      else:
        return ()
    except:
      logging.error("rgeocode failed to parse %s" % json)
      return ()
        
class AdClickHandler(webapp.RequestHandler):
  # /m/aclk?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
  def get(self):
    import urllib
    id = self.request.get("id")
    q = self.request.get("q")    
    # BROKEN
    # url = self.request.get("r")
    sz = self.request.query_string
    url = sz[(sz.rfind("r=") + 2):]
    url = unquote(url)
    
    # forward on to the click URL
    self.redirect(url)

# TODO: Process this on the logs processor 
class AppOpenHandler(webapp.RequestHandler):
  # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
  def get(self):
    self.response.out.write("OK") 
    

def main():
  application = webapp.WSGIApplication([('/m/ad', AdHandler), 
                                        ('/m/aclk', AdClickHandler),
                                        ('/m/open',AppOpenHandler)], 
                                        debug=True)
  wsgiref.handlers.CGIHandler().run(application)

# webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
