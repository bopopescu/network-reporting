#!/usr/bin/env python

import code
import getpass
import sys
import traceback

sys.path.append("/home/ubuntu/mopub/server")
sys.path.append("/home/ubuntu/mopub/server/reporting")
sys.path.append("/home/ubuntu/google_appengine")
sys.path.append("/home/ubuntu/google_appengine/lib/django")
sys.path.append("/home/ubuntu/google_appengine/lib/webob")
sys.path.append("/home/ubuntu/google_appengine/lib/yaml/lib")
sys.path.append("/home/ubuntu/google_appengine/lib/fancy_urllib")

sys.path.append("../..")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django_1_2")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")

import wsgiref.handlers, cgi, logging, os, re, datetime, hashlib, traceback, fileinput, urlparse
from django.utils import simplejson
from urllib import urlencode

from properties import Properties

from reporting.models import *
from publisher.models import *
from advertiser.models import *

from google.appengine.api import users
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
            try:
              globals()[proc]().process(logline_dict)
            except Exception, e:
              exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
              print exception_traceback
            
      # if this is an OLP info log
      olp_dict = self.parse_olp(line)
      if olp_dict:
        for proc, regex in props.items():
          if re.compile(regex).match(olp_dict["event"]) != None:
            try:
              globals()[proc]().process(olp_dict)
            except Exception, e:
              exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
              print exception_traceback
  
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

class AdGroupCache(object):
  Klass = AdGroup
  cache = {}

  @classmethod
  def get(cls,keys):
    if not keys.__class__ == list:
      keys = [keys]
    objs = []
    for key in keys:
      if str(key) in cls.cache:
        objs.append(cls.cache.get(str(key)))
        keys.remove(key)
    
    if keys:
      datastore_objs = cls.Klass.get(keys)
      print 'fetching from remote datastore %s'%keys
      # put into local cache
      # we use map since datastore_objs may be None
      for key,obj in zip(keys, datastore_objs):
        cls.cache[str(key)] = obj
      objs += datastore_objs
    if len(objs) > 1:
      return objs
    return objs[0]  

class CreativeCache(AdGroupCache):
  Klass = Creative   
  
class AdUnitCache(AdGroupCache):
  Klass = Site    
      
class StatsCounter(object):
  def get_site_stats(self, site_key, date=datetime.datetime.now().date()):
    try:
      if site_key:
        key = SiteStats.get_key(site_key, None, date)
        s = all_stats.get(key)
        if s is None:
          s = SiteStats(site=db.Key(site_key), date=date, key=key)
          all_stats[key] = s
        return s
      else:
        return None
    except Exception, e:
      print 'StatsCounter.get_site_stats()',e
      return None

  def get_qualifier_stats(self, qualifier_key, date=datetime.datetime.now().date()):
    if qualifier_key:
      key = SiteStats.get_key(None, qualifier_key, date)
      s = all_stats.get(key)
      if s is None:
        s = SiteStats(owner=db.get(qualifier_key), date=date, key=key)
        all_stats[key] = s
      return s
    else:
      return None
  
  def get_site_stats_with_qualifier(self, site_key, qualifier_key, date=datetime.datetime.now().date()):
    try:
      if site_key and qualifier_key:
        key = SiteStats.get_key(site_key, qualifier_key, date)
        s = all_stats.get(key)
        if s is None:
          s = SiteStats(site=db.get(site_key), owner=db.get(qualifier_key), date=date, key=key)
          all_stats[key] = s
        return s
      else:
        return None
    except Exception, e:
      print 'StatsCounter.get_site_stats_with_qualifier()',e
      return None

  def get_user_stats(self, device_id):
    key = device_id
    s = all_stats.get(key)
    if s is None:
      s = UserStats(device_id=device_id, key_name=device_id)
      all_stats[key] = s
    return s

  # should be overridden by subclasses
  def process(self, logline_dict):
    raise NotImplementedError
    
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

## App level processors 

class AppRequestCounter(StatsCounter):
  def process(self, d):
    ad_unit_key_string = self.get_id_for_dict(d)
    if ad_unit_key_string:
      ad_unit_key = db.Key(ad_unit_key_string)
      ad_unit = AdUnitCache.get(ad_unit_key)
      if ad_unit:
        app_key = ad_unit.app_key.key()
        
        stats = self.get_qualifier_stats(app_key)
        if stats:
          stats.request_count += 1
          if 'udid' in d["params"]:
            udid = d["params"]["udid"]
            stats.add_user(udid)

class AppImpressionCounter(StatsCounter):          
  def process(self, d):
    ad_unit_key_string = self.get_id_for_dict(d)
    if ad_unit_key_string:
      ad_unit_key = db.Key(ad_unit_key_string)
      ad_unit = AdUnitCache.get(ad_unit_key)
      if ad_unit:
        app_key = ad_unit.app_key.key()
        
        stats = self.get_qualifier_stats(app_key)
        if stats:
          stats.impression_count += 1
          
class AppClickCounter(StatsCounter):
  def process(self, d):
    ad_unit_key_string = self.get_id_for_dict(d)
    if ad_unit_key_string:
      ad_unit_key = db.Key(ad_unit_key_string)
      ad_unit = AdUnitCache.get(ad_unit_key)
      if ad_unit:
        app_key = ad_unit.app_key.key()
        
        stats = self.get_qualifier_stats(app_key)
        if stats:
          stats.click_count += 1
#
# PubRequestCounter - counts reqs on publisher ad units
#
class PubRequestCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.request_count += 1

class PubGeoRequestCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    country_code = None
    if stats:
      pat = re.compile(r'Mac OS X; ([^\)]{5})') # Match the first 5 characters that aren't the ending parenthesis
      match = pat.search(d['client'])
      if match:
        try:
          country_code = match.group(1).split('_')[1].lower()
        except:
          pass
      else:
        pat = re.compile(r'Android.*; (.*?);')
        match = pat.search(d['client'])
        if match:
          try:
            country_code = match.group(1).split('-')[1].lower()
          except:
            pass

    if not country_code:
      country_code = "unknown"        
    if country_code: 
      stats.geo_request_dict.update({country_code:stats.geo_request_dict.get(country_code,0)+1})
        
class PubUniqueUserCounter(StatsCounter):
   def process(self,d):
     stats = self.get_site_stats(self.get_id_for_dict(d))  
     if stats:
       if 'udid' in d["params"]:
         udid = d["params"]["udid"]
         stats.add_user(udid)

# PubImpressionCounter - counts impressions  on pub ad units
# 1:1284681678.531128 OLP ad-auction agltb3B1Yi1pbmNyDAsSBFNpdGUYudkDDA agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGJGQBAw 9093a6dd16c74324a64d3edf388f62ae
#
class PubImpressionCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      stats.impression_count += 1     
      
class PubRevenueCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)

      # TODO: Have a parent-child relationship such that the key name already tells us the parent key
      creative = CreativeCache.get(creative_key)
      if not creative:
        return
      adgroup_key = creative.ad_group.key()
      adgroup = AdGroupCache.get(adgroup_key)

      if stats:
        # increment revenue if the bid strategy is cpm
        if adgroup.bid_strategy == 'cpm':
          stats.revenue += adgroup.bid*1.0/1000.0               

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
      
# #
# # PubClickRevenueCounter - counts clicks
# #
class PubClickRevenueCounter(StatsCounter):
  def process(self, d):
    stats = self.get_site_stats(self.get_id_for_dict(d))
    if stats:
      creative_key_string = d["params"].get("c",None)
      if creative_key_string:
        creative_key = db.Key(creative_key_string)

        # TODO: Have a parent-child relationship such that the key name already tells us the parent key
        creative = CreativeCache.get(creative_key)
        if not creative:
          return
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)

        # update the revenue if the adgroup is cpc based payment
        if adgroup.bid_strategy == 'cpc':
          stats.revenue += adgroup.bid

#
# CampaignImpressionCounter - counts impressions and accrues them to creatives, adgroups and campaigns
#
class CampaignImpressionCounter(StatsCounter):
  def process(self, d):
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)
      creative = CreativeCache.get(creative_key)
      if creative:
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)
        campaign_key = adgroup.campaign.key()

        stats = self.get_qualifier_stats(creative_key)
        adgroup_stats = self.get_qualifier_stats(adgroup_key)
        campaign_stats = self.get_qualifier_stats(campaign_key)
      
        stats.impression_count += 1
        adgroup_stats.impression_count += 1
        campaign_stats.impression_count += 1
        
        site_key_string = d["params"].get("id")
        site_key = db.Key(site_key_string)
        stats_q = self.get_site_stats_with_qualifier(site_key, creative_key)
        adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_key)
        campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_key)
      
        stats_q.impression_count += 1
        adgroup_stats_q.impression_count += 1
        campaign_stats_q.impression_count += 1

class CampaignUniqueUserCounter(StatsCounter):
  def process(self, d):
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)
      creative = CreativeCache.get(creative_key)
      if creative:
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)
        campaign_key = adgroup.campaign.key()

        stats = self.get_qualifier_stats(creative_key)
        adgroup_stats = self.get_qualifier_stats(adgroup_key)
        campaign_stats = self.get_qualifier_stats(campaign_key)

        site_key_string = d["params"].get("id")
        site_key = db.Key(site_key_string)
        stats_q = self.get_site_stats_with_qualifier(site_key, creative_key)
        adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_key)
        campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_key)
  
        # tallies up the unique users for each particular stat
        for stat in [stats,adgroup_stats,campaign_stats,stats_q,adgroup_stats_q,campaign_stats_q]:
          if 'udid' in d["params"]:
            udid = d["params"]["udid"]
            stat.add_user(udid)

class CampaignImpressionSpendCounter(StatsCounter):
  def process(self, d):
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)
      creative = CreativeCache.get(creative_key)
      if creative:
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)
        campaign_key = adgroup.campaign.key()

        stats = self.get_qualifier_stats(creative_key)
        adgroup_stats = self.get_qualifier_stats(adgroup_key)
        campaign_stats = self.get_qualifier_stats(campaign_key)
              
        site_key_string = d["params"].get("id")
        site_key = db.Key(site_key_string)
        stats_q = self.get_site_stats_with_qualifier(site_key, creative_key)
        adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_key)
        campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_key)
            
        if adgroup.bid_strategy == 'cpm':
          revenue_increment = adgroup.bid*1.0/1000.0
          stats.revenue += revenue_increment
          adgroup_stats.revenue += revenue_increment
          campaign_stats.revenue += revenue_increment
          stats_q.revenue += revenue_increment
          adgroup_stats_q.revenue += revenue_increment
          campaign_stats_q.revenue += revenue_increment
        
#
# CampaignClickCounter - counts clicks and accrues them to creatives, adgroups and campaigns
#
class CampaignClickCounter(StatsCounter):
  def process(self, d):
    # accrue this click to a particular creative, campaign and ad group
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)
      creative = CreativeCache.get(creative_key)
      if creative:
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)
        campaign_key = adgroup.campaign.key()
        
        
        stats = self.get_qualifier_stats(creative_key)
        adgroup_stats = self.get_qualifier_stats(adgroup_key)
        campaign_stats = self.get_qualifier_stats(campaign_key)

        stats.click_count += 1
        adgroup_stats.click_count += 1
        campaign_stats.click_count += 1

        site_key = d["params"].get("id")
        stats_q = self.get_site_stats_with_qualifier(site_key, creative_key)
        adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_key)
        campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_key)
      
        stats_q.click_count += 1
        adgroup_stats_q.click_count += 1
        campaign_stats_q.click_count += 1
            
class CampaignClickSpendCounter(StatsCounter):
  def process(self, d):
    creative_key_string = d["params"].get("c",None)
    if creative_key_string:
      creative_key = db.Key(creative_key_string)
      creative = CreativeCache.get(creative_key)
      if creative:
        adgroup_key = creative.ad_group.key()
        adgroup = AdGroupCache.get(adgroup_key)
        campaign_key = adgroup.campaign.key()
      
        stats = self.get_qualifier_stats(creative_key)
        adgroup_stats = self.get_qualifier_stats(adgroup_key)
        campaign_stats = self.get_qualifier_stats(campaign_key)

        site_key = d["params"].get("id")
        stats_q = self.get_site_stats_with_qualifier(site_key, creative_key)
        adgroup_stats_q = self.get_site_stats_with_qualifier(site_key, adgroup_key)
        campaign_stats_q = self.get_site_stats_with_qualifier(site_key, campaign_key)
    
        if adgroup.bid_strategy == 'cpc':
          revenue_increment = adgroup.bid
          stats.revenue += revenue_increment
          adgroup_stats.revenue += revenue_increment
          campaign_stats.revenue += revenue_increment
          stats_q.revenue += revenue_increment
          adgroup_stats_q.revenue += revenue_increment
          campaign_stats_q.revenue += revenue_increment
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
  return "olp@mopub.com", "N47935N47935"

def main(logfile="/tmp/logfile",app_id="mopub-inc",host="mopub-inc.appspot.com"):

  # connect to google datastore
  remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

  # process the logfile .... 
  AdStats().process(logfile)
  
  print 'DONE PROCESSING, writing %d stats values' % len(StatsCounter.all_stats().values())   
  
  for s in StatsCounter.all_stats().values():
    print repr(s)
    try:
      db.put(s)
    except Exception, e:
      print e


if __name__ == '__main__':
  if len(sys.argv) < 3:
      print "Usage: %s [logfile] [host]" % (sys.argv[0],)
  app_id = "mopub-inc"
  host = sys.argv[2] if len(sys.argv) > 2 else ('%s.appspot.com' % app_id)
  logfile = sys.argv[1] if len(sys.argv) > 1 else "/tmp/logfile"
  
  main(logfile)  
