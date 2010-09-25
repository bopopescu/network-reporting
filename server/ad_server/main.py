#!/usr/bin/env python
import wsgiref.handlers
import cgi
import logging
import os
import re
import datetime
import hashlib
import traceback
import random
import md5
import time
import base64, binascii
from django.utils import simplejson

from string import Template
from urllib import urlencode

from google.appengine.ext.webapp import template
from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue

from publisher.models import *
from advertiser.models import *
from reporting.models import *

CRAWLERS = ["Mediapartners-Google,gzip(gfe)", "Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'

#
# Ad auction logic
# The core of the whole damn thing
#
class AdAuction(object):
  MAX_ADGROUPS = 30

  # Runs the auction itself.  Returns the winning creative, or None if no creative matched
  @classmethod
  def run(cls, **kw):
    site = kw["site"]

    keywords = kw["q"]
    geo_predicates = AdAuction.geo_predicates_for_rgeocode(kw["addr"])
    device_predicates = AdAuction.device_predicates_for_request(kw["request"])
    format_predicates = AdAuction.format_predicates_for_format(kw["format"])
    logging.debug("keywords=%s, geo_predicates=%s, device_predicates=%s, format_predicates=%s" % (keywords, geo_predicates, device_predicates, format_predicates))

    # Matching strategy: 
    # 1) match all ad groups that match the placement that is in question, sort by priority
    # 2) throw out ad groups owned by campaigns that have exceeded budget or are paused
    # 3) throw out ad groups that restrict by keywords and do not match the keywords
    # 4) throw out ad groups that do not match device and geo predicates
    ad_groups = AdGroup.gql("where site_keys = :1 and active = :2 and deleted = :3", site.key(), True, False).fetch(AdAuction.MAX_ADGROUPS)
    logging.debug("ad groups: %s" % ad_groups)
    
    # campaign exclusions... budget + time
    ad_groups = filter(lambda a: SiteStats.stats_for_day(a.campaign, SiteStats.today()).revenue < a.campaign.budget, ad_groups)
    logging.debug("removed over budget, now: %s" % ad_groups)
    ad_groups = filter(lambda a: a.campaign.active and (a.campaign.start_date >= SiteStats.today() if a.campaign.start_date else True) and (a.campaign.end_date <= SiteStats.today() if a.campaign.end_date else True), ad_groups)
    logging.debug("removed non running campaigns, now: %s" % ad_groups)
    
    # ad group request-based targeting exclusions
    ad_groups = filter(lambda a: len(a.keywords) == 0 or set(keywords).intersection(a.keywords) > set(), ad_groups)
    logging.debug("removed keyword non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(geo_predicates).intersection(a.geo_predicates) > set(), ad_groups)
    logging.debug("removed geo non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(device_predicates).intersection(a.device_predicates) > set(), ad_groups)
    logging.debug("removed device non-matches, now: %s" % ad_groups)
    
    # TODO: frequency capping and other user / request based randomizations
    pass
    
    # if any ad groups were returned, find the creatives that match the requested format in all candidates
    if len(ad_groups) > 0:
      creatives = Creative.gql("where ad_group in :1 and format_predicates in :2 and active = :3 and deleted = :4", 
        map(lambda x: x.key(), ad_groups), format_predicates, True, False).fetch(AdAuction.MAX_ADGROUPS)
      logging.debug("eligible creatives: %s" % creatives)

      if len(creatives) > 0:
        # for each priority_level, perform an auction among the various creatives 
        max_priority = max(c.ad_group.priority_level for c in creatives)
        for p in range(max_priority + 1):
          players = filter(lambda c: c.ad_group.priority_level == p, creatives)
          players.sort(lambda x,y: cmp(y.e_cpm(), x.e_cpm()))
          winning_ecpm = max(c.e_cpm() for c in players) if len(players) > 0 else 0
          logging.debug("auction at priority=%d: %s, max eCPM=%.2f" % (p, players, winning_ecpm))
        
          # if the winning creative exceeds the ad unit's threshold cpm for the
          # priority level, then we have a winner
          if winning_ecpm > site.threshold_cpm(p):
            # retain all creatives with comparable eCPM and randomize among them
            winners = filter(lambda x: x.e_cpm() >= winning_ecpm, players)
            random.shuffle(winners)

            # winner
            winner = winners[0]
            logging.debug("winning creative = %s" % winner)
            return winner
          
    # nothing... failed auction
    logging.debug("auction failed, returning None")

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
    return ["format=%dx%d" % (f[0], f[1]), "format=*"]
      
#
# Primary ad auction handler 
# -- Handles ad request parameters and normalizes for the auction logic
# -- Handles rendering the winning creative into the right HTML
#
class AdHandler(webapp.RequestHandler):
  
  # Format properties: width, height, adsense_format, num_creatives
  FORMAT_SIZES = {
    "300x250_as": (300, 250, "300x250_as", 3),
    "320x50_mb": (320, 50, "320x50_mb", 1),
    "728x90_as": (728, 90, "728x90_as", 2),
    "468x60_as": (468, 60, "468x60_as", 1),
    "300x250": (300, 250, "300x250_as", 3),
    "320x50": (320, 50, "320x50_mb", 1),
    "728x90": (728, 90, "728x90_as", 2),
    "468x60": (468, 60, "468x60_as", 1)
  }
  
  def get(self):
    id = self.request.get("id")
    site = Site.site_by_id(id) if id else None
    
    # the user's site key was not set correctly...
    if site is None:
      self.error(500)
      self.response.out.write("Publisher site key %s not valid" % id)
      return
    
    # get keywords 
    q = [sz.strip() for sz in ("%s\n%s" % (self.request.get("q").lower(), site.keywords)).split("\n")]
    logging.debug("keywords are %s" % q)

    # get format
    f = self.request.get("f") or "320x50"
    format = self.FORMAT_SIZES.get(f)
    logging.debug("format is %s (requested '%s')" % (format, f))
    
    # look up lat/lon
    addr = self.rgeocode(self.request.get("ll")) if self.request.get("ll") else ""      
    logging.debug("geo is %s (requested '%s')" % (addr, self.request.get("ll")))
    
    # get creative exclusions
    excluded_creatives = self.request.get("excl")
    
    # create a unique request id, but only log this line if the user agent is real
    request_id = md5.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
    if str(self.request.headers['User-Agent']) not in CRAWLERS:
      logging.info('OLP ad-request {"request_id": "%s", "remote_addr": "%s", "q": "%s", "user_agent": "%s"}' % (request_id, self.request.remote_addr, self.request.query_string, self.request.headers["User-Agent"]))

    # get winning creative
    c = AdAuction.run(request=self.request, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, request_id=request_id)
    
    # output the request_id and the winning creative_id if an impression happened
    if c:
      logging.info('OLP ad-auction {"id": "%s", "c": "%s", "request_id": "%s"}' % (id, c.key(), request_id))

      # create an ad clickthrough URL
      ad_click_url = "http://www.mopub.com/m/aclk?id=%s&c=%s&req=%s" % (id, c.key(), request_id)
      self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
      
    # render the creative 
    self.response.out.write(self.render_creative(c, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, request_id=request_id))
  
  #
  # Templates
  #
  TEMPLATES = {
    "adsense": Template("""<html> <head><title>$title</title></head> <body style="margin: 0;width:${w}px;height:${h}px;" > <script type="text/javascript">window.googleAfmcRequest = {client: '$client',ad_type: 'text_image', output: 'html', channel: '',format: '$adsense_format',oe: 'utf8',color_border: '336699',color_bg: 'FFFFFF',color_link: '0000FF',color_text: '000000',color_url: '008000',};</script> <script type="text/javascript" src="http://pagead2.googlesyndication.com/pagead/show_afmc_ads.js"></script>  </body> </html> """),
    "admob": Template("admob goes here"),
    "iAd": Template("iAd"),
    "clear": Template(""),
    "text": Template("""<html>\
                        <head><style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}</style></head>\
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">\
                          <div class="creative"><div style="padding: 5px 10px;"><a href="$url" class="creative_headline">$headline</a><br/>$line1 $line2<br/><span class="creative_url"><a href="$url">$display_url</a></span></div></div>\
                        </body> </html> """),
    "image":Template("""<html>\
                        <head><style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 20px;}.creative .creative_url a {color: green;text-decoration: none;}</style></head>\
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">\
                          <a href="$url"><img src="$image_url" width=$w height=$h/></a>
                        </body> </html> """),
    "admob": Template("""<html><head></head><body style="margin: 0;width:${w}px;height:${h}px;padding:0;">
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
                        </body></html>"""),
    "html":Template("<html><head></head><body style=\"margin: 0;padding:0;\">${html_data}</body></html>"),
  }
  def render_creative(self, c, **kwargs):
    if c:
      logging.info("rendering %s" % c.ad_type)
      format = kwargs["format"]

      params = kwargs
      params.update(c.__dict__.get("_entity"))

      if c.ad_type == "adsense":
        params.update({"title": kwargs["q"], "adsense_format": format[2], "w": format[0], "h": format[1], "client": kwargs["site"].account.adsense_pub_id})
      elif c.ad_type == "admob":
        params.update({"w": format[0], "h": format[1], "client": kwargs["site"].account.admob_pub_id})
      elif c.ad_type == "image":
        params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
      elif c.ad_type == "html":
        params.update({"html_data": kwargs["html_data"]})
      
      # indicate to the client the winning creative type, in case it is natively implemented (iad, clear)
      self.response.headers.add_header("X-Backfill", str(c.ad_type))
    
      # render the HTML body
      self.response.out.write(self.TEMPLATES[c.ad_type].safe_substitute(params))
    else:
      self.response.headers.add_header("X-Backfill", "clear")
  
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
  def get(self):
    id = self.request.get("id")
    q = self.request.get("q")
    url = self.request.get("r")
    
    # forward on to the click URL
    self.redirect(url)

def main():
  application = webapp.WSGIApplication([('/m/ad', AdHandler), ('/m/aclk', AdClickHandler)], debug=False)
  wsgiref.handlers.CGIHandler().run(application)

# webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
