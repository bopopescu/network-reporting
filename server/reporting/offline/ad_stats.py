#!/usr/bin/env python

import code
import getpass
import sys
sys.path.append("../..")
sys.path.append("..")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib, traceback, fileinput, urlparse
from django.utils import simplejson
from urllib import urlencode

from properties import Properties

import models
import publisher.models
import advertiser.models

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db, webapp

## 
# Performs basic statistical calculations on a mopub logfile
#
# 166.205.139.160 - - [08/Sep/2010:16:08:09 -0700] "GET /m/ad?v=1&f=320x50&udid=4bddad15bd08cbbfb2c804f4561828212d34acc2&ll=19.610787,-155.978178&q=Restaurants:%20Jameson\'s%20By%20the%20Sea%20&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRjpyQMM HTTP/1.1" 200 761 - "nearby-iphone/1.4 CFNetwork/459 Darwin/10.0.0d3,gzip(gfe),gzip(gfe)"
# 97.209.72.66 - - [08/Sep/2010:15:50:34 -0700] "GET /m/ad?v=1&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRiZugMM&udid=22a00000224a3568&q=fine%20dining&ll=33.795244,-117.831168 HTTP/1.1" 200 508 - "Mozilla/5.0 (Linux; U; Android 2.1-update1; en-us; DROIDX Build/VZW) AppleWebKit/530.17 (KHTML, like Gecko) Version/4.0 Mobile Safari/530.17,gzip(gfe),gzip(gfe)"
# 66.249.71.15 - - [08/Sep/2010:15:50:35 -0700] "GET /m/ad?v=1&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRiZugMM&udid=22a00000224a3568&q=fine%20dining&ll=33.795244,-117.831168 HTTP/1.1" 200 508 - "Mediapartners-Google,gzip(gfe),gzip(gfe)"
#
class AdStats:
  COMBINED_LOGLINE_PAT = re.compile(r'(?P<origin>\d+\.\d+\.\d+\.\d+) '
    + r'(?P<identd>-|\w*) (?P<auth>-|\w*) '
    + r'\[(?P<date>[^\[\]:]+):(?P<time>\d+:\d+:\d+) (?P<tz>[\-\+]?\d\d\d\d)\] '
    + r'"(?P<method>\w+) (?P<url>[\S]+) (?P<protocol>[^"]+)" (?P<status>\d+) (?P<bytes>-|\d+) '
    + r'(?P<referrer>-|"[^"]*") (?P<client>"[^"]*")')
    
  OLP_LOGLINE_PAT = re.compile(r'.* OLP (?P<event>[\w\-_]+) (?P<json>\{.*\})')

  CRAWLERS = ["Mediapartners-Google,gzip(gfe),gzip(gfe)"]

  def process(self, f):
    props = Properties()
    props.load(file("ad_stats.properties"))
    
    for line in fileinput.input([f]):
      # if this is an apache style log line
      logline_dict = self.parse_logline(line)
      if logline_dict and str(logline_dict['client']) not in self.CRAWLERS:
        for proc, regex in props.items():
          if re.compile(regex).match(logline_dict["path"]) != None:
            globals()[proc]().process(logline_dict)
            
      # if this is an OLP info log
      olp_dict = self.parse_olp(line)
      if olp_dict:
        for proc, regex in props.items():
          if re.compile(regex).match(olp_dict["event"]) != None:
            globals()[proc]().process(olp_dict)
  
  # takes a log line and parses it, detecting UserAgent, query parameters, origin IP and other information
  #
  # {'origin': '166.205.139.160', 'status': '200', 'tz': '-0700', 'referrer': '-', 'bytes': '761', 'auth': '-', 'identd': '-', 
  # 'client': '"nearby-iphone/1.4 CFNetwork/459 Darwin/10.0.0d3,gzip(gfe),gzip(gfe)"', 'time': '16:08:09', 'date': '08/Sep/2010', 
  # 'protocol': 'HTTP/1.1', 
  # 'path': "/m/ad", 
  # 'qs': "?v=1&f=320x50&udid=4bddad15bd08cbbfb2c804f4561828212d34acc2&ll=19.610787,-155.978178&q=Restaurants:%20Jameson's%20By%20the%20Sea%20&id=ahFoaWdobm90ZS1uZXR3b3Jrc3IMCxIEU2l0ZRjpyQMM",
  # 'params': {"v": ['1'] ... }
  # 'method': 'GET'}
  #
  def parse_logline(self, logline):
    m = self.COMBINED_LOGLINE_PAT.match(logline)
    if m:
      d = m.groupdict()
    
      # also decode the path into a query dict
      d["path"] = urlparse.urlsplit(d.get("url"))[2]
      d["qs"] = urlparse.urlsplit(d.get("url"))[3]
      d["params"] = dict(cgi.parse_qsl(d["qs"]))

      return d
    else:
      return None
    
  def parse_olp(self, logline):
    m = self.OLP_LOGLINE_PAT.match(logline)
    if m:
      d = m.groupdict()
      d["params"] = simplejson.loads(d["json"]) 
      return d
    else:
      return None
    
#
# Generic base class for stats counters
#
all_stats = {}
class StatsCounter(object):
  def get_site_stats(self, site_key, date=datetime.datetime.now().date()):
    try:
      if site_key:
        key = models.SiteStats.get_key(site_key, None, date)
        s = all_stats.get(key)
        if s is None:
          s = models.SiteStats(site=db.get(site_key), date=date, key=key)
          all_stats[key] = s
        return s
      else:
        return None
    except:
      return None

  def get_qualifier_stats(self, qualifier_key, date=datetime.datetime.now().date()):
    if qualifier_key:
      key = models.SiteStats.get_key(None, qualifier_key, date)
      s = all_stats.get(key)
      if s is None:
        s = models.SiteStats(owner=db.get(qualifier_key), date=date, key=key)
        all_stats[key] = s
      return s
    else:
      return None
  
  def get_site_stats_with_qualifier(self, site_key, qualifier_key, date=datetime.datetime.now().date()):
    try:
      if site_key and qualifier_key:
        key = models.SiteStats.get_key(site_key, qualifier_key, date)
        s = all_stats.get(key)
        if s is None:
          s = models.SiteStats(site=db.get(site_key), owner=db.get(qualifier_key), date=date, key=key)
          all_stats[key] = s
        return s
      else:
        return None
    except:
      return None

  def get_user_stats(self, device_id):
    key = device_id
    s = all_stats.get(key)
    if s is None:
      s = models.UserStats(device_id=device_id, key_name=device_id)
      all_stats[key] = s
    return s

  # should be overridden by subclasses
  def process(self, logline_dict):
    pass
    
  # convenience method to return the right "id" parameter
  def get_id_for_dict(self, d):
    x = d["params"].get("id")
    if x:
      return x[0] if type(x) == type([]) else x
    else:
      return None
      
  # return all_stats object
  @classmethod
  def all_stats(clz):
    return all_stats

#
# PubRequestCounter - counts reqs on publisher ad units
#
class PubRequestCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.request_count += 1
  
# 
# PubImpressionCounter - counts impressions  on pub ad units
# 1:1284681678.531128 OLP ad-auction agltb3B1Yi1pbmNyDAsSBFNpdGUYudkDDA agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGJGQBAw 9093a6dd16c74324a64d3edf388f62ae
#
class PubImpressionCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.impression_count += 1

#
# PubLegacyImpressionCounter - counts imprs on publisher ad units
#
class PubLegacyImpressionCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.impression_count += 1

  
#
# PubClickCounter - counts clicks
#
class PubClickCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.click_count += 1

#
# CampaignImpressionCounter - counts impressions and accrues them to creatives, adgroups and campaigns
#
class CampaignImpressionCounter(StatsCounter):
  def process(self, d):
    if d["params"].get("c") and db.get(d["params"].get("c")):
      stats = self.get_qualifier_stats(d["params"].get("c"))
      adgroup_stats = self.get_qualifier_stats(stats.owner.ad_group.key())
      campaign_stats = self.get_qualifier_stats(stats.owner.ad_group.campaign.key())
      
      stats.impression_count += 1
      adgroup_stats.impression_count += 1
      campaign_stats.impression_count += 1

      site_key = d["params"].get("id")
      stats_q = self.get_site_stats_with_qualifier(site_key, stats.owner.key())
      adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_stats.owner.key())
      campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_stats.owner.key())
      
      stats_q.impression_count += 1
      adgroup_stats_q.impression_count += 1
      campaign_stats_q.impression_count += 1

#
# CampaignClickCounter - counts clicks and accrues them to creatives, adgroups and campaigns
#
class CampaignClickCounter(StatsCounter):
  def process(self, d):
    # accrue this click to a particular creative, campaign and ad group
    if d["params"].get("c") and db.get(d["params"].get("c")):
      stats = self.get_qualifier_stats(d["params"].get("c"))
      adgroup_stats = self.get_qualifier_stats(stats.owner.ad_group.key())
      campaign_stats = self.get_qualifier_stats(stats.owner.ad_group.campaign.key())

      stats.click_count += 1
      adgroup_stats.click_count += 1
      campaign_stats.click_count += 1

      site_key = d["params"].get("id")
      stats_q = self.get_site_stats_with_qualifier(site_key, stats.owner.key())
      adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_stats.owner.key())
      campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_stats.owner.key())
      
      stats_q.click_count += 1
      adgroup_stats_q.click_count += 1
      campaign_stats_q.click_count += 1

#
# UserInfoAccumulator - accumulates information about a user based on requests
#
class UserInfoAccumulator(StatsCounter):
  def process(self, d):
    stats = self.get_user_stats(d["params"]["udid"])
    if stats:
      if d["params"].get("ll"):
        stats.ll = d["params"]["ll"]
      if d["params"].get("q") and len(d["params"].get("q")) > 0:
        stats.keywords.append(d["params"]["q"])


####
# main()
def auth_func():
  return "jimepayne", getpass.getpass('Password:')

if __name__ == '__main__':
  if len(sys.argv) < 3:
      print "Usage: %s [logfile] [host]" % (sys.argv[0],)
  app_id = "mopub-inc"
  host = sys.argv[2] if len(sys.argv) > 2 else ('%s.appspot.com' % app_id)
  logfile = sys.argv[1] if len(sys.argv) > 1 else "/tmp/logfile"

  # connect to google datastore
  remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

  # process the logfile .... 
  AdStats().process(logfile)
  for s in StatsCounter.all_stats().values():
    print repr(s)
    
  # store into database
  db.put(StatsCounter.all_stats().values())

