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
from google.appengine.api import urlfetch
from google.appengine.api import memcache
from google.appengine.api import users
from google.appengine.api.labs import taskqueue
from google.appengine.api import memcache

from publisher.models import *
from advertiser.models import *
from reporting.models import *

from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.appnexus import AppNexusServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.greystripe import GreyStripeServerSide

from publisher.query_managers import AdServerAdUnitQueryManager, AdUnitQueryManager
from advertiser.query_managers import CampaignStatsCounter


test_mode = "3uoijg2349ic(test_mode)kdkdkg58gjslaf"
CRAWLERS = ["Mediapartners-Google,gzip(gfe)", "Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'
DOMAIN = 'ads.mopub.com'

import urllib
urllib.getproxies_macosx_sysconf = lambda: {}


# TODO: Logging is fucked up with unicode characters

# DOMAIN = 'localhost:8080'
#
# Ad auction logic
# The core of the whole damn thing
#
def memcache_key_for_date(udid,datetime,db_key):
  return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d'),db_key)

def memcache_key_for_hour(udid,datetime,db_key):
  return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d%H'),db_key)

###############################
#FILTERS
#
# --- Each filter function is a function which takes some arguments (or none) necessary 
#       for the filter to work its magic. log_mesg is the message that will be logged 
#       for the associated objects that eval'd to false.
# --- ALL FILTER GENERATOR FUNCTIONS MUST RETURN ( filter_function, log_mesg, [] )
# --- The empty list is the list that will contain all elt's for which the 
#       filter_function returned False
###############################

def budget_filter():
    log_mesg = "Removed due to being over budget: %s"
    def real_filter( a ):
        return not ( a.budget is None or a.campaign.delivery_counter.count < a.budget )
    return ( real_filter, log_mesg, [] )

def active_filter():
    log_mesg = "Removed due to inactivity: %s"
    def real_filter( a ):
        return not ( a.campaign.active and ( a.campaign.start_date  >= SiteStats.today() if a.campaign.start_date else True ) and ( SiteStats.today() <= a.campaign.end_date if a.campaign.end_date else True ) )
    return ( real_filter, log_mesg, [] )

def kw_filter( keywords ):
    log_mesg = "Removed due to keyword mismatch: %s"
    def real_filter( a ):
        return not ( not a.keywords or set( keywords ).intersection( a.keywords ) > set() )
    return ( real_filter, log_mesg, [] )

def geo_filter( geo_preds ):
    log_mesg = "Removed due to geo mismatch: %s"
    def real_filter( a ):
        return not ( set( geo_preds ).intersection( a.geographic_predicates ) > set() )
    return ( real_filter, log_mesg, [] )

def device_filter( dev_preds ):
    log_mesg = "Removed due to device mismatch: %s"
    def real_filter( a ):
        return  not ( set( dev_preds ).intersection( a.device_predicates ) > set() )
    return ( real_filter, log_mesg, [] )


def mega_filter( *filters ): 
    def actual_filter( a ):
        for ( f, msg, lst ) in filters:
            if f( a ):
                lst.append( a )
                return False
        return True
    return actual_filter
###############
# End filters
###############

class AdAuction(object):
  MAX_ADGROUPS = 30

  @classmethod
  def request_third_party_server(cls,request,adunit,adgroups):
    rpcs = []
    for adgroup in adgroups:
      server_side_dict = {"millennial":MillennialServerSide,
                          "appnexus":AppNexusServerSide,
                          "inmobi":InMobiServerSide,
                          "brightroll":BrightRollServerSide,
                          "greystripe":GreyStripeServerSide}
      if adgroup.network_type in server_side_dict:
        KlassServerSide = server_side_dict[adgroup.network_type]
        server_side = KlassServerSide(request, adunit) 
        logging.warning("%s url %s"%(KlassServerSide,server_side.url))

        rpc = urlfetch.create_rpc(2) # maximum delay we are willing to accept is 2000 ms
        payload = server_side.payload
        if payload == None:
          urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
        else:
          urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)
        # attaching the adgroup to the rpc
        rpc.adgroup = adgroup
        rpc.serverside = server_side
        rpcs.append(rpc)
    return rpcs    
      # 
      # # ... do other things ...
      # 
      # try:
      #     result = rpc.get_result()
      #     if result.status_code == 200:
      #         response = mmServerSide.html_for_response(result)
      #         self.response.out.write("%s<br/> %s"%(mmServerSide.url,response))
      # except urlfetch.DownloadError:
      #   self.response.out.write("%s<br/> %s"%(mmServerSide.url,"response not fast enough"))

  # Runs the auction itself.  Returns the winning creative, or None if no creative matched
  @classmethod
  def run(cls, **kw):
    now = kw["now"]
    site = kw["site"]
    manager = kw["manager"]
    request = kw["request"]
    
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
    all_ad_groups = manager.get_adgroups() #AdGroup.gql("where site_keys = :1 and active = :2 and deleted = :3", site.key(), True, False).fetch(AdAuction.MAX_ADGROUPS)
    
    rpcs = AdAuction.request_third_party_server(request,site,all_ad_groups)
    
    logging.warning("ad groups: %s" % all_ad_groups)
    
    # # campaign exclusions... budget + time
    
    
    for a in all_ad_groups:
      logging.info("%s of %s"%(a.campaign.delivery_counter.count,a.budget))
    
    ALL_FILTERS     = ( budget_filter(), 
                        active_filter(), 
                        kw_filter( keywords ), 
                        geo_filter( geo_predicates ), 
                        device_filter( device_predicates ) 
                        ) 

    all_ad_groups = filter( mega_filter( *ALL_FILTERS ), all_ad_groups )

    for ( func, warn, lst ) in ALL_FILTERS:
        logging.warning( warn % lst )

    # NOTE: The budgets are in the adgroup when they should be in the campaign

    # frequency capping and other user / request based randomizations
    udid = kw["udid"]
        
    # if any ad groups were returned, find the creatives that match the requested format in all candidates
    if len(all_ad_groups) > 0:
      logging.warning("ad_group: %s"%all_ad_groups)
      
      all_creatives = manager.get_creatives_for_adgroups(all_ad_groups)
      # all_creatives = Creative.gql("where ad_group in :1 and format_predicates in :2 and active = :3 and deleted = :4", 
      #   map(lambda x: x.key(), ad_groups), format_predicates, True, False).fetch(AdAuction.MAX_ADGROUPS)
      max_priority = max(ad_group.priority_level for ad_group in all_ad_groups)
      
      logging.warning("creatives (max priority: %d): %s"%(max_priority,all_creatives))

      #XXX Why is this here?  It does make sense to bail if there are no creatives, but it seems to be a waste to get all creatives just to verify that there, in fact, creatives after it's been verified that there are ad_groups 

      if len(all_creatives) > 0:
        # for each priority_level, perform an auction among the various creatives 
        for p in range(max_priority + 1):
          # players = filter(lambda c: c.ad_group.priority_level == p, all_creatives)
          logging.warning("priority level: %d"%p)
          eligible_adgroups = [a for a in all_ad_groups if a.priority_level == p]
          logging.warning("eligible_adgroups: %s"%eligible_adgroups)
          players = manager.get_creatives_for_adgroups(eligible_adgroups)
          players.sort(lambda x,y: cmp(y.e_cpm(), x.e_cpm()))
          
          while players:
            logging.warning("players: %s"%players)
            #players is sorted by cpm above, if len( players ) == 0 then the while loop will eval to False and not exec
            winning_ecpm = players[0].e_cpm()
            #winning_ecpm = max(c.e_cpm() for c in players) if len(players) > 0 else 0.0
            logging.warning("auction at priority=%d: %s, max eCPM=%s" % (p, players, winning_ecpm))
      
            # if the winning creative exceeds the ad unit's threshold cpm for the
            # priority level, then we have a winner
            if winning_ecpm >= site.threshold_cpm(p):
              winners = filter(lambda x: x.e_cpm() >= winning_ecpm, players)
              logging.warning("%02d winners: %s"%(len(winners),winners))
              
              # campaigns = set([c.ad_group.campaign for c in winners if not c.ad_group.deleted and not c.ad_group.campaign.deleted])
              # logging.warning("campaigns: %s"%campaigns)
              
              # find out which ad groups are eligible
              ad_groups = set([c.ad_group for c in winners])
              logging.warning("eligible ad_groups: %s" % ad_groups)

              #XXX wat ( this is totally not used anywhere else )             
              creatives = [c for c in all_creatives if c.ad_group.key() in [a.key() for a in ad_groups]]
            
              # exclude according to the exclude parameter must do this after determining adgroups
              # so that we maintain the correct order for user bucketing
              # TODO: we should exclude based on creative id not ad type :)
              logging.warning("eligible creatives: %s %s" % (winners,exclude_params))
              winners = [c for c in winners if not (c.ad_type in exclude_params)]  
              logging.warning("eligible creatives after exclusions: %s" % winners)
              

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
                                
              # TODO: user based frequency caps (need to add other levels)
              user_keys = []
              for adgroup in winning_ad_groups:
                if adgroup.daily_frequency_cap:
                  user_adgroup_daily_key = memcache_key_for_date(udid,now,adgroup.key())
                  user_keys.append(user_adgroup_daily_key)
                if adgroup.hourly_frequency_cap:  
                  user_adgroup_hourly_key = memcache_key_for_hour(udid,now,adgroup.key())
                  user_keys.append(user_adgroup_hourly_key)

              if user_keys:  
                frequency_cap_dict = memcache.get_multi(user_keys)    
              else:
                frequency_cap_dict = {}
              
              winning_ad_groups_new = []
              logging.warning("winning ad groups: %s"%winning_ad_groups)
              for adgroup in winning_ad_groups:
                user_adgroup_daily_key = memcache_key_for_date(udid,now,adgroup.key())
                user_adgroup_hourly_key = memcache_key_for_hour(udid,now,adgroup.key())
                daily_frequency_cap = adgroup.daily_frequency_cap
                hourly_frequency_cap = adgroup.hourly_frequency_cap
                
                
                # pull out the impression count from memcache, otherwise its assumed to be 0
                if daily_frequency_cap and (user_adgroup_daily_key in frequency_cap_dict):
                  daily_impression_cnt = int(frequency_cap_dict[user_adgroup_daily_key])
                else:
                  daily_impression_cnt = 0 
                  
                if hourly_frequency_cap and (user_adgroup_hourly_key in frequency_cap_dict):
                  hourly_impression_cnt = int(frequency_cap_dict[user_adgroup_hourly_key])
                else:
                  hourly_impression_cnt = 0  
                  
                logging.warning("daily imps:%d freq cap: %d"%(daily_impression_cnt,daily_frequency_cap))
                logging.warning("hourly imps:%d freq cap: %d"%(hourly_impression_cnt,hourly_frequency_cap))
                  
                  
                if (not daily_frequency_cap or daily_impression_cnt < daily_frequency_cap) and \
                   (not hourly_frequency_cap or hourly_impression_cnt < hourly_frequency_cap):
                  winning_ad_groups_new.append(adgroup)
                  
              winning_ad_groups = winning_ad_groups_new
              logging.warning("winning ad groups after frequency capping: %s"%winning_ad_groups)

              # if there is a winning/eligible adgroup find the appropriate creative for it
              winning_creative = None
              if winning_ad_groups:
                logging.warning("winner ad_groups: %s"%winning_ad_groups)
              
                if winning_ad_groups:
                  winners = [winner for winner in winners if winner.ad_group in winning_ad_groups]
                
                # Remove wrong formats
                # TODO: clean this up
                logging.warning('c.format: %s s.format: %s'%([c.format for c in winners],site.format))
                logging.warning("winners: %s"%winners)
                winners = [w for w in winners if w.format == site.format]
                logging.warning("winners after formats: %s"%winners)

                if winners:
                  logging.warning('winners %s'%[w.ad_group for w in winners])
                  random.shuffle(winners)
                  logging.warning('random winners %s'%winners)
          
                  # find the actual winner among all the eligble ones
                  actual_winner = None
                  # loop through each of the randomized winners making sure that the data is ready to display
                  for winner in winners:
                    if not rpcs:
                      winning_creative = winner
                      return winning_creative
                    else:
                      rpc = None                      
                      if winner.ad_group.key() in [r.adgroup.key() for r in rpcs]:
                        for rpc in rpcs:
                          if rpc.adgroup.key() == winner.ad_group.key():
                            logging.warning("rpc.adgroup %s"%rpc.adgroup)
                            break # This pulls out the rpc that matters there should be one always

                      # if the winning creative relies on a rpc to get the actual data to display
                      # go out and get the data and paste in the data to the creative      
                      if rpc:      
                        try:
                            result = rpc.get_result()
                            if result.status_code == 200:
                                bid,response = rpc.serverside.bid_and_html_for_response(result)
                                winning_creative = winner
                                winning_creative.html_data = response
                                return winning_creative
                        except Exception,e:
                          import traceback, sys
                          exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
                          logging.error(exception_traceback)
                      else:
                        winning_creative = winner
                        return winning_creative
                        
              #   else:
              #     logging.warning('taking away some players not in %s'%ad_groups)
              #     logging.warning('current players: %s'%players)
              #     players = [c for c in players if not c.ad_group in ad_groups]  
              #     logging.warning('remaining players %s'%players)
              #     
              # else:
              if not winning_creative:
                logging.warning('taking away some players not in %s'%ad_groups)
                logging.warning( 'current ad_groups %s' % [c.ad_group for c in players] )
                logging.warning('current players: %s'%players)
                players = [c for c in players if not c.ad_group in ad_groups]  
                logging.warning('remaining players %s'%players)
             # try at a new priority level   

    # nothing... failed auction
    logging.warning("auction failed, returning None")
    return None
    
  @classmethod
  def geo_predicates_for_rgeocode(c, r):
    # r = [US, CA SF] or []
    # TODO: DEFAULT COUNTRY SHOULD NOT BE US!!!!!!!
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    if len(r) == 0:
      return ["country_name=US","country_name=*"] # ["country_name"=*] or ["country_name=US] ["country_name="CD"]
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
    "320x480": (300, 250, "300x250_as", 1),
  }
  
  def get(self):
    logging.warning(self.request.headers['User-Agent'] )
    id = self.request.get("id")
    
    manager = AdUnitQueryManager(id)
    now = datetime.datetime.now()

    #Testing!
    if self.request.get( 'testing' ) == test_mode:
        manager = AdServerAdUnitQueryManager( id )
        testing = True
        now = datetime.datetime.fromtimestamp( float( self.request.get('dt') ) )
    else:
        testing = False

    # site = manager.get_by_key(key)#Site.site_by_id(id) if id else None
    adunit = manager.get_adunit()
    site = adunit
     
    
    
    # the user's site key was not set correctly...
    if site is None:
      self.error(404)
      self.response.out.write("Publisher adunit key %s not valid" % id)
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
    f = self.request.get("f") or "320x50" # TODO: remove this default
    f = "%dx%d"%(int(site.width),int(site.height))
    format = self.FORMAT_SIZES.get(f)
    # logging.warning("format is %s (requested '%s')" % (format, f))
    
    # look up lat/lon
    addr = self.rgeocode(self.request.get("ll")) if self.request.get("ll") else ()      
    logging.warning("geo is %s (requested '%s')" % (addr, self.request.get("ll")))
    
    # get creative exclusions usually used to exclude iAd because it has already failed
    excluded_creatives = self.request.get_all("exclude")
    logging.info("excluded_creatives: %s"%excluded_creatives)
    
    # TODO: get udid we should hash it if its not already hashed
    udid = self.request.get("udid")
    
    # create a unique request id, but only log this line if the user agent is real
    request_id = hashlib.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
    if str(self.request.headers['User-Agent']) not in CRAWLERS:
      logging.info('OLP ad-request {"request_id": "%s", "remote_addr": "%s", "q": "%s", "user_agent": "%s", "udid":"%s" }' % (request_id, self.request.remote_addr, self.request.query_string, self.request.headers["User-Agent"], udid))

    # get winning creative
    c = AdAuction.run(request=self.request, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, udid=udid, request_id=request_id, now=now,manager=manager)
    
    # output the request_id and the winning creative_id if an impression happened
    if c:
      user_adgroup_daily_key = memcache_key_for_date(udid,now,c.ad_group.key())
      user_adgroup_hourly_key = memcache_key_for_hour(udid,now,c.ad_group.key())
      logging.warning("user_adgroup_daily_key: %s"%user_adgroup_daily_key)
      logging.warning("user_adgroup_hourly_key: %s"%user_adgroup_hourly_key)
      memcache.offset_multi({user_adgroup_daily_key:1,user_adgroup_hourly_key:1}, key_prefix='', namespace=None, initial_value=0)
      
      if str(self.request.headers['User-Agent']) not in CRAWLERS:
        logging.info('OLP ad-auction {"id": "%s", "c": "%s", "request_id": "%s", "udid": "%s"}' % (id, c.key(), request_id, udid))

      # create an ad clickthrough URL
      ad_click_url = "http://%s/m/aclk?id=%s&c=%s&req=%s" % (DOMAIN,id, c.key(), request_id)
      self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
      
      # ad an impression tracker URL
      self.response.headers.add_header("X-Imptracker", "http://%s/m/imp?"%(DOMAIN))
      
      # add to the campaign counter
      logging.info("adding to delivery: %s"%c.ad_group.bid)
      c.ad_group.campaign.delivery_counter.increment(dollars=c.ad_group.bid)
      
      # render the creative 
      self.response.out.write(self.render_creative(c, site=site, format=format, q=q, addr=addr, excluded_creatives=excluded_creatives, request_id=request_id, v=int(self.request.get('v') or 0)))
      if testing:
          return c.key()
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
                              <script type="text/javascript">window.googleAfmcRequest = {client: '$client',ad_type: 'text_image', output: 'html', channel: '$channel_id',format: '$adsense_format',oe: 'utf8',color_border: '336699',color_bg: 'FFFFFF',color_link: '0000FF',color_text: '000000',color_url: '008000',};</script> 
                              <script type="text/javascript" src="http://pagead2.googlesyndication.com/pagead/show_afmc_ads.js"></script>  
                              $trackingPixel
                            </body>
                          </html> """),
    "iAd": Template("iAd"),
    "clear": Template(""),
    "text": Template("""<html>
                        <head>
                          <style type="text/css">.creative {font-size: 12px;font-family: Arial, sans-serif;width: ${w}px;height: ${h}px;}.creative_headline {font-size: 14px;}.creative .creative_url a {color: green;text-decoration: none;}
                          </style>
                          $finishLoad
                          <script>
                            function webviewDidClose(){} 
                            function webviewDidAppear(){} 
                          </script>
                          <title>$title</title>
                        </head>
                        <body style="margin: 0;width:${w}px;height:${h}px;padding:0;">
                          <div class="creative"><div style="padding: 5px 10px;"><a href="$url" class="creative_headline">$headline</a><br/>$line1 $line2<br/><span class="creative_url"><a href="$url">$display_url</a></span></div></div>\
                          $trackingPixel
                        </body> </html> """),
    "text_icon": Template(
"""<html>
  <head>
    $finishLoad
    <script>
      function webviewDidClose(){}
      function webviewDidAppear(){}
    </script>
    <title></title>
  </head>
  <body style="top-margin:0;margin:0;width:320px;padding:0;background-color:#$color;font-size:12px;font-family:Arial,sans-serif;">
  <div id='highlight' style="position:relative;height:50px;background:-webkit-gradient(linear, left top, left bottom, from(rgba(255,255,255,0.35)),
    to(rgba(255,255,255,0.06))); -webkit-background-origin: padding-box; -webkit-background-clip: content-box;">
    <div style="margin:5px;width:40px;height:40px;float:left"><img id="thumb" src="$image_url" style="-webkit-border-radius:6px;-moz-border-radius:6px" width=40 height=40/></div>
    <div style="float:left;width:230">
      <div style="color:white;font-weight:bold;margin:0px 0 0 5px;padding-top:8;">$line1</div>
      <div style="color:white;margin-top:6px;margin:5px 0 0 5px;">$line2</div>
    </div>
    <div style="padding-top:5px;position:absolute;top:0;right:0;"><a href="$url"><img src="/images/$action_icon.png" width=40 height=40/></a></div>
    $trackingPixel
  </div>
  </body>
</html>"""),
    "image":Template("""<html>
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
                        <script type="text/javascript">
                          function webviewDidClose(){} 
                          function webviewDidAppear(){} 
                          window.innerWidth = $w;
                          window.innerHeight = $h;
                        </script>
                        <title>$title</title>
                        </head><body style="margin: 0;width:${w}px;height:${h}px;padding:0;">
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
    "html":Template("""<html><head><title>$title</title>
                        $finishLoad                  
                        <script type="text/javascript">
                          function webviewDidClose(){} 
                          function webviewDidAppear(){} 
                        </script></head>
                        <body style="margin:0;padding:0;width:${w}px;background:white">${html_data}$trackingPixel</body></html>"""),
    "html_full":Template("$html_data")
  }
  def render_creative(self, c, **kwargs):
    if c:
      logging.warning("rendering: %s" % c.ad_type)
      format = kwargs["format"]
      site = kwargs["site"]

      template_name = c.ad_type
      
      params = kwargs
      params.update(c.__dict__.get("_entity"))
      if c.ad_type == "adsense":
        params.update({"title": ','.join(kwargs["q"]), "adsense_format": format[2], "w": format[0], "h": format[1], "client": kwargs["site"].account.adsense_pub_id})
        params.update(channel_id=kwargs["site"].adsense_channel_id or '')
        # self.response.headers.add_header("X-Launchpage","http://googleads.g.doubleclick.net")
      elif c.ad_type == "admob":
        params.update({"title": ','.join(kwargs["q"]), "w": format[0], "h": format[1], "client": kwargs["site"].account.admob_pub_id})
        self.response.headers.add_header("X-Launchpage","http://c.admob.com/")
      elif c.ad_type == "text_icon":
        if c.image:
          params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
        # self.response.headers.add_header("X-Adtype", str('html'))
      elif c.ad_type == "greystripe":
        params.update(html_data=c.html_data)
        # TODO: Why is html data here twice?
        params.update({"html_data": kwargs["html_data"], "w": format[0], "h": format[1]})
        self.response.headers.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
        template_name = "html"
      elif c.ad_type == "image":
        params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
        params.update({"w": format[0], "h": format[1]})
      elif c.ad_type == "html":
        params.update(html_data=c.html_data)
        params.update({"html_data": kwargs["html_data"], "w": format[0], "h": format[1]})
        
        # HACK FOR RUSSEL's INTERSTITIAL
        # if str(c.key()) == "agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGPmNGAw":
        #   self.response.headers.add_header("X-Closebutton","None")
        
      elif c.ad_type == "html_full":
        params.update(html_data=c.html_data)
        params.update({"html_data": kwargs["html_data"]})
        self.response.headers.add_header("X-Scrollable","1")
        self.response.headers.add_header("X-Interceptlinks","0")
      elif c.ad_type == "text":  
        self.response.headers.add_header("X-Productid","pixel_001")
        
        
      if kwargs["q"] or kwargs["addr"]:
        params.update(title=','.join(kwargs["q"]+list(kwargs["addr"])))
      else:
        params.update(title='')
        
      if kwargs["v"] >= 2 and not "Android" in self.request.headers["User-Agent"]:  
        params.update(finishLoad='<script>function finishLoad(){window.location="mopub://finishLoad";} window.onload = function(){finishLoad();} </script>')
      else:
        params.update(finishLoad='')  
      
      
      if c.tracking_url:
        params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>'%c.tracking_url)
      else:
        params.update(trackingPixel='')  
      
      # indicate to the client the winning creative type, in case it is natively implemented (iad, clear)
      
      if str(c.ad_type) == "iAd":
        # self.response.headers.add_header("X-Adtype","custom")
        # self.response.headers.add_header("X-Backfill","alert")
        # self.response.headers.add_header("X-Nativeparams",'{"title":"MoPub Alert View","cancelButtonTitle":"No Thanks","message":"We\'ve noticed you\'ve enjoyed playing Angry Birds.","otherButtonTitle":"Rank","clickURL":"mopub://inapp?id=pixel_001"}')
        # self.response.headers.add_header("X-Customselector","customEventTest")
        
        self.response.headers.add_header("X-Adtype", str(c.ad_type))
        self.response.headers.add_header("X-Backfill", str(c.ad_type))        
        self.response.headers.add_header("X-Failurl",self.request.url+'&exclude='+str(c.ad_type))
        
      elif str(c.ad_type) == "adsense":
        self.response.headers.add_header("X-Adtype", str(c.ad_type))
        self.response.headers.add_header("X-Backfill", str(c.ad_type))
        
        logging.warning('pub id:%s'%kwargs["site"].account.adsense_pub_id)
        header_dict = {
          "Gclientid":str(kwargs["site"].account.adsense_pub_id),
          "Gcompanyname":str(kwargs["site"].account.adsense_company_name),
          "Gappname":str(kwargs["site"].app_key.adsense_app_name),
          "Gappid":"0",
          "Gkeywords":str(kwargs["site"].keywords or ''),
          "Gtestadrequest":"0",
          "Gchannelids":str(kwargs["site"].adsense_channel_id or ''),        
        # "Gappwebcontenturl":,
          "Gadtype":"GADAdSenseTextImageAdType", #GADAdSenseTextAdType,GADAdSenseImageAdType,GADAdSenseTextImageAdType
          "Gtestadrequest":"1" if site.account.adsense_test_mode else "0",
        # "Ghostid":,
        # "Gbackgroundcolor":"00FF00",
        # "Gadtopbackgroundcolor":"FF0000",
        # "Gadbordercolor":"0000FF",
        # "Gadlinkcolor":,
        # "Gadtextcolor":,
        # "Gadurlolor":,
        # "Gexpandirection":,
        # "Galternateadcolor":,
        # "Galternateadurl":, # This could be interesting we can know if Adsense 'fails' and is about to show a PSA.
        # "Gallowadsafemedium":,
        }
        json_string_pairs = []
        for key,value in header_dict.iteritems():
          json_string_pairs.append('"%s":"%s"'%(key,value))
        json_string = '{'+','.join(json_string_pairs)+'}'
        self.response.headers.add_header("X-Nativeparams",json_string)
        
        # add some extra  
        self.response.headers.add_header("X-Failurl",self.request.url+'&exclude='+str(c.ad_type))
        self.response.headers.add_header("X-Format",format[2])
        self.response.headers.add_header("X-Width",str(format[0]))
        self.response.headers.add_header("X-Height",str(format[1]))
      
        self.response.headers.add_header("X-Backgroundcolor","0000FF")
      else:  
        self.response.headers.add_header("X-Adtype", str('html'))
        
      if kwargs["q"] or kwargs["addr"]:
        params.update(title=','.join(kwargs["q"]+list(kwargs["addr"])))
      else:
        params.update(title='')
      
      if kwargs["v"] >= 2 and not "Android" in self.request.headers["User-Agent"]:  
        params.update(finishLoad='<script>function finishLoad(){window.location="mopub://finishLoad";} window.onload = function(){finishLoad();} </script>')
      else:
        params.update(finishLoad='')

      if c.tracking_url:
        params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>'%c.tracking_url)
      else:
        params.update(trackingPixel='')

      self.response.headers.add_header("X-Backfill", str('html'))

      # render the HTML body
      self.response.out.write(self.TEMPLATES[template_name].safe_substitute(params))
    else:
      self.response.headers.add_header("X-Adtype", "clear")
      self.response.headers.add_header("X-Backfill", "clear")
    
    # make sure this response is not cached by the client  
    # self.response.headers.add_header('Cache-Control','no-cache')  
  
  def rgeocode(self, ll):
    url = "http://maps.google.com/maps/geo?%s" % urlencode({"q": ll, 
      "key": MAPS_API_KEY, 
      "sensor": "false", 
      "output": "json"})
    json = urlfetch.fetch(url).content
    try:
      geocode = simplejson.loads(json)

      if geocode.get("Placemark"):
        for placemark in geocode["Placemark"]:
          if placemark.get("AddressDetails").get("Accuracy") == 8:
            logging.warning("rgeocode Accuracy == 8")
          
            country = placemark.get("AddressDetails").get("Country")
            administrativeArea = country.get("AdministrativeArea") if country else None
            subAdministrativeArea = administrativeArea.get("SubAdministrativeArea") if administrativeArea else None
            locality = (subAdministrativeArea.get("Locality") if subAdministrativeArea else administrativeArea.get("Locality")) if administrativeArea else None
            logging.warning("country=%s, administrativeArea=%s, subAdminArea=%s, locality=%s" % (country, administrativeArea, subAdministrativeArea, locality))
          
            return (locality.get("LocalityName") if locality else "", 
                    administrativeArea.get("AdministrativeAreaName") if administrativeArea else "",
                    country.get("CountryNameCode") if country else "")
        return ()
      else:
        return ()
    except:
      logging.error("rgeocode failed to parse %s" % json)
      return ()

class AdImpressionHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write("OK")
        
class AdClickHandler(webapp.RequestHandler):
  # /m/aclk?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
  def get(self):
    import urllib
    id = self.request.get("id")
    q = self.request.get("q")    
    # BROKEN
    # url = self.request.get("r")
    sz = self.request.query_string
    r = sz.rfind("&r=")
    if r > 0:
      url = sz[(r + 3):]
      url = unquote(url)
      # forward on to the click URL
      self.redirect(url)
    else:
      self.response.out.write("OK")

# TODO: Process this on the logs processor 
class AppOpenHandler(webapp.RequestHandler):
  # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
  def get(self):
    self.response.out.write("OK") 

class TestHandler(webapp.RequestHandler):
  # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
  def get(self):
    from ad_server.networks.greystripe import GreyStripeServerSide
    from ad_server.networks.millennial import MillennialServerSide
    from ad_server.networks.brightroll import BrightRollServerSide
    
    #server_side = BrightRollServerSide(self.request,357)
    #server_side = MillennialServerSide(self.request,357)
    server_side = InMobiServerSide(self.request)
    logging.warning("%s, %s"%(server_side.url,server_side.payload))
    
    rpc = urlfetch.create_rpc(5) # maximum delay we are willing to accept is 1000 ms

    payload = server_side.payload
    if payload == None:
      urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
    else:
      urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)


    # ... do other things ...

    try:
        result = rpc.get_result()
        if result.status_code == 200:
            bid,response = server_side.bid_and_html_for_response(result)
            self.response.out.write("%s<br/> %s %s"%(server_side.url+'?'+payload if payload else '',bid,response))
    except urlfetch.DownloadError:
      self.response.out.write("%s<br/> %s"%(server_side.url,"response not fast enough"))
      
  def post(self):
    logging.info("%s"%self.request.headers["User-Agent"])  
    self.response.out.write("hello world")

# TODO: clears the cache USE WITH FEAR
class ClearHandler(webapp.RequestHandler):
  def get(self):
    self.response.out.write(memcache.flush_all())
    
class PurchaseHandler(webapp.RequestHandler):
  def post(self):
    logging.info(self.request.get("receipt"))
    logging.info(self.request.get("udid"))
    self.response.out.write("OK")    
    

def main():
  application = webapp.WSGIApplication([('/m/ad', AdHandler), 
                                        ('/m/imp', AdImpressionHandler),
                                        ('/m/aclk', AdClickHandler),
                                        ('/m/open', AppOpenHandler),
                                        ('/m/test', TestHandler),
                                        ('/m/clear', ClearHandler),
                                        ('/m/purchase', PurchaseHandler)], 
                                        debug=True)
  run_wsgi_app(application)
  # wsgiref.handlers.CGIHandler().run(application)

# webapp.template.register_template_library('filters')
if __name__ == '__main__':
  main()
