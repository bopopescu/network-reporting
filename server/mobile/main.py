#!/usr/bin/env python
import wsgiref.handlers
import cgi
import logging
import os
import re
import datetime
import hashlib
import traceback
import models
import random
import md5
import time

from django.utils import simplejson

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

CRAWLERS = ["Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'
#
# Format properties: width, height, adsense_format, num_creatives
#
FORMAT_SIZES = {
  "300x250_as": [300, 250, "300x250_as", 3],
  "320x50_mb": [320, 50, "320x50_mb", 1],
  "728x90_as": [728, 90, "728x90_as", 2],
  "468x60_as": [468, 60, "468x60_as", 1],
  "300x250": [300, 250, "300x250_as", 3],
  "320x50": [320, 50, "320x50_mb", 1],
  "728x90": [728, 90, "728x90_as", 2],
  "468x60": [468, 60, "468x60_as", 1]
}
  
class AdHandler(webapp.RequestHandler):
  def get(self):
    id = self.request.get("id")
    
    # create a unique request id
    request_id = md5.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
    logging.info('OLP ad-request {"request_id": "%s", "remote_addr": "%s", "q": "%s", "user_agent": "%s"}' % (request_id, self.request.remote_addr, self.request.query_string, self.request.headers["User-Agent"]))

    # enqueue impression tracking iff referer is not a crawler bot
    if str(self.request.headers['User-Agent']) not in CRAWLERS:
      taskqueue.add(url='/m/track/i', params={'id': id})    
    
    # look up parameters for this pub id via memcache
    h = memcache.get("ad2:%s" % id)
    if h is None:
      site = models.Site.site_by_id(id)
      if site is None:
        # the user's site key was not set correctly...
        self.error(500)
        self.response.out.write("Publisher site key %s not valid" % id)
        return
        
      # create a hash and store in memcache
      h = {"site_key": str(site.key()),
         "default_keywords": site.keywords,
         "backfill": site.backfill,
         "backfill_threshold_cpm": site.backfill_threshold_cpm,
         "adsense_pub_id": site.account.adsense_pub_id}
      memcache.set("ad:%s" % id, h, 600)
      
    # get keywords 
    q = self.request.get("q") or ""   
    if len(q) == 0:
      q = h["default_keywords"]
    logging.debug("keywords are %s" % q)

    # get format
    f = self.request.get("f")
    format = FORMAT_SIZES.get(f)
    if f is None or len(f) == 0 or format is None:
      f = "320x50"
      format = FORMAT_SIZES.get("320x50")
    logging.debug("format is %s (%s)" % (f, format))
      
    # look up lat/lon
    addr = ''
    ll = self.request.get("ll")
    if ll:
      addr = self.rgeocode(ll)      
      logging.debug("resolved %s to %s" % (ll, addr))
      
    # get creatives that match
    creatives = AdHandler.get_creatives(h, self.request, q, addr, f)
    c = creatives[0] if len(creatives) > 0 else None
    
    # should we show a creative or use our backfill strategy?
    html = None
    if c and c.e_cpm() >= h["backfill_threshold_cpm"]:
      # ok show our ad
      logging.debug("eCPM exceeded threshold, showing ad")
      html = "internal%dx%d.html" % (format[0], format[1])
      
      # output the request_id and the winning creative_id 
      logging.info('OLP ad-auction {"id": "%s", "c": "%s", "request_id": "%s"}' % (id, c.key(), request_id))

      # enqueue impression tracking iff referer is not a crawler bot
      if str(self.request.headers['User-Agent']) not in CRAWLERS:
        taskqueue.add(url='/m/track/ai', params={'c': c.key(), 'q': q, 'id': id})   
    elif h["backfill"] == "fail":
      # never mind, we should fail
      logging.debug("eCPM did not exceed threshold, failing")
      html = None
    else:
      # never mind, we should use a backfill strategy
      logging.debug("eCPM did not exceed threshold, using backfill: %s" % h["backfill"])
      self.response.headers.add_header("X-Backfill", str(h["backfill"]))
      html = "%s.html" % h["backfill"]

    # create an ad click URL
    ad_click_url = "http://www.mopub.com/m/aclk?id=%s&c=%s&req=%s" % (id, str(c.key()) if c else '', request_id)
    self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
        
    # write it out
    if html:
      self.response.out.write(template.render(html, {"title": q, 
        "c": c,
        "f": f, 
        "adsense_format": format[2],
        "w": format[0], 
        "h": format[1],
        "url": c.url if c else "",
        "addr": " ".join(addr),
        "client": h["adsense_pub_id"]}))
    else:
      self.error(404)
  
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

  @classmethod
  def get_creatives(c, h, request, q, rgeocode, format):
    MAX_ADGROUPS = 30
    keywords = (q or "").split("\n")
    site_key = h.get("site_key")      # the site key
    logging.debug("keywords=%s site_key=%s" % (keywords, site_key))
    
    geo_predicates = AdHandler.geo_predicates_for_rgeocode(rgeocode)
    device_predicates = AdHandler.device_predicates_for_request(request)
    format_predicates = AdHandler.format_predicates_for_format(format)
    logging.debug("geo_predicates=%s, device_predicates=%s, format_predicates=%s" % (geo_predicates, device_predicates, format_predicates))
    
    # Matching strategy: 1) match all ad groups that match the placement that is in question
    # 2) throw out ad groups owned by campaigns that have exceeded budget
    # 3) throw out ad groups that restrict by keywords and do not match the keywords
    # 4) throw out ad groups that do not match device and geo predicates
    ad_groups = models.AdGroup.gql("where site_keys = :1 and active = :2 and deleted = :3 order by bid desc", db.Key(site_key), True, False).fetch(MAX_ADGROUPS)
    logging.debug("ad groups: %s" % ad_groups)
    ad_groups = filter(lambda a: models.SiteStats.stats_for_day(a.campaign, models.SiteStats.today()).revenue < a.campaign.budget, ad_groups)
    logging.debug("removed over budget, now: %s" % ad_groups)
    ad_groups = filter(lambda a: len(a.keywords) == 0 or set(keywords).intersection(a.keywords) > set(), ad_groups)
    logging.debug("removed keyword non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(geo_predicates).intersection(a.campaign.geo_predicates) > set(), ad_groups)
    logging.debug("removed geo non-matches, now: %s" % ad_groups)
    ad_groups = filter(lambda a: set(device_predicates).intersection(a.campaign.device_predicates) > set(), ad_groups)
    logging.debug("removed device non-matches, now: %s" % ad_groups)

    # if any ad groups were returned, reduce the creatives into a single list
    #
    if len(ad_groups) > 0:
      creatives = models.Creative.gql("where ad_group in :1 and format_predicates in :2 and active = :3 and deleted = :4", 
        map(lambda x: x.key(), ad_groups), format_predicates, True, False).fetch(MAX_ADGROUPS)
      logging.debug(creatives)
    
      # perform an auction among the creatives to select the winner
      creatives.sort(lambda x,y: cmp(y.e_cpm(), x.e_cpm()))
    
      # retain all creatives with comparable eCPM and randomize among them
      winning_ecpm = creatives[0].e_cpm() if len(creatives) > 0 else 0
      creatives = filter(lambda x: x.e_cpm() >= winning_ecpm, creatives)
      random.shuffle(creatives)
    
      logging.debug("returned %d creatives, winning eCPM=%.2f" % (len(creatives), winning_ecpm))
      return creatives
    else:
      return []
      
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
    return ["format=%s" % f, "format=*"]
    
    
class AdClickHandler(webapp.RequestHandler):
  def get(self):
    id = self.request.get("id")
    q = self.request.get("q")
    url = self.request.get("r")
    
    # enqueue click tracking
    taskqueue.add(url='/m/track/c', params={'id': id, 'q': q})

    # forward on to the click URL
    self.redirect(url)

# 
# Tracks an impression on the publisher side.  Accrues an impression
# to the Site
#   
class TrackImpression(webapp.RequestHandler):
  def post(self):
    try:
      s = models.Site.site_by_id(self.request.get("id"))
      stats = models.SiteStats.sitestats_for_today(s)     
      db.run_in_transaction(stats.add_impression)
    except:
      logging.error("failed to track site impression %s" % self.request.get("id"))
      
#     
# Tracks an advertiser impression
#
class TrackAdvertiserImpression(webapp.RequestHandler):
  def post(self):
    try:
      creative = models.Creative.get(self.request.get("c"))
      d = models.SiteStats.today()
      
      db.run_in_transaction(models.SiteStats.stats_for_day(creative, d).add_impression)
      db.run_in_transaction(models.SiteStats.stats_for_day(creative.ad_group, d).add_impression)
      db.run_in_transaction(models.SiteStats.stats_for_day(creative.ad_group.campaign, d).add_impression)

      # add for the ad group sliced by keyword and by placement
      db.run_in_transaction(models.SiteStats.stats_for_day_with_qualifier(creative.ad_group, self.request.get('q'), d).add_impression)
      db.run_in_transaction(models.SiteStats.stats_for_day_with_qualifier(creative.ad_group, self.request.get('id'), d).add_impression)

    except:
      logging.error("failed to track creative impression %s" % self.request.get("id"))
      
#
# Publisher side click tracking... accrues to a Site
#
class TrackClick(webapp.RequestHandler):
  def post(self):
    try:
      s = models.Site.site_by_id(self.request.get("id"))
      stats = models.SiteStats.sitestats_for_today(s)
      db.run_in_transaction(stats.add_click)
    except:
      logging.error("failed to track click for id %s" % self.request.get("id"))
    
#     
# Advertiser side click tracking... accrues to a Creative, AdGroup and Campaign
# Also has budgetary impacts, by accruing the creative's Bid to the total cost of these various
# elements.
#
class TrackAdvertiserClick(webapp.RequestHandler):
  def post(self):
    try:
      creative = models.Creative.get(self.request.get("c"))
      d = models.SiteStats.today()

      db.run_in_transaction(models.SiteStats.stats_for_day(creative, d).add_click_with_revenue, creative.ad_group.bid)
      db.run_in_transaction(models.SiteStats.stats_for_day(creative.ad_group, d).add_click_with_revenue, creative.ad_group.bid)
      db.run_in_transaction(models.SiteStats.stats_for_day(creative.ad_group.campaign, d).add_click_with_revenue, creative.ad_group.bid)

      # add for the ad group sliced by keyword and by placement
      db.run_in_transaction(models.SiteStats.stats_for_day_with_qualifier(creative.ad_group, self.request.get('q'), d).add_click_with_revenue, creative.ad_group.bid)
      db.run_in_transaction(models.SiteStats.stats_for_day_with_qualifier(creative.ad_group, self.request.get('id'), d).add_click_with_revenue, creative.ad_group.bid)

    except:
      logging.error("failed to track creative click for %s" % self.request.get("id"))
                  
def main():
  application = webapp.WSGIApplication([('/m/ad', AdHandler),
                    ('/m/aclk', AdClickHandler),
                    ('/m/track/i', TrackImpression),
                    ('/m/track/ai', TrackAdvertiserImpression),
                    ('/m/track/c', TrackClick),
                    ('/m/track/ac', TrackAdvertiserClick)], debug=True)
  wsgiref.handlers.CGIHandler().run(application)

webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
