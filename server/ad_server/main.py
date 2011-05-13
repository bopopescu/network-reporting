# !/usr/bin/env python
from appengine_django import LoadDjango
LoadDjango()
import os
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None

import wsgiref.handlers
import cgi
import logging
import os
import re
import hashlib
import traceback
import random
import hashlib
import time
import base64, binascii
import urllib
import datetime

urllib.getproxies_macosx_sysconf = lambda: {}

from ad_server.filters.filters import (budget_filter,
                                    active_filter,
                                    kw_filter,
                                    geo_filter,
                                    device_filter,
                                    mega_filter,
                                    format_filter,
                                    exclude_filter,
                                    ecpm_filter,
                                    freq_filter,
                                    all_freq_filter,
                                    lat_lon_filter,
                                   )
from ad_server.adserver_templates import TEMPLATES
                                    
from common.utils import simplejson
from common.utils import helpers
from common.constants import (FULL_NETWORKS,
                              ACCEPTED_MULTI_COUNTRY,
                             )

from string import Template
from urllib import urlencode, unquote
#from datetime import datetime

from google.appengine.api import users, urlfetch, memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from publisher.models import *
from advertiser.models import *
from reporting.models import StatsModel
from userstore.models import CLICK_EVENT_NO_APP_ID

from ad_server.networks.appnexus import AppNexusServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.mobfox import MobFoxServerSide
from ad_server.optimizer import optimizer

from userstore.query_managers import ClickEventManager, AppOpenEventManager
from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR

from mopub_logging import mp_logging
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging

###################
# Import Handlers #
###################
from ad_server.handlers import TestHandler

TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"

# Figure out if we're on a production server
from google.appengine.api import apiproxy_stub_map
have_appserver = bool(apiproxy_stub_map.apiproxy.GetStub('datastore_v3'))
on_production_server = have_appserver and \
    not os.environ.get('SERVER_SOFTWARE', '').lower().startswith('devel')
DEBUG = not on_production_server


############## CONSTANTS ###############


CRAWLERS = ["Mediapartners-Google,gzip(gfe)", "Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'
FREQ_ATTR = '%s_frequency_cap'
CAMPAIGN_LEVELS = ('gtee_high', 'gtee', 'gtee_low', 'promo', 'network','backfill_promo')
NATIVE_REQUESTS = ['admob','adsense','iAd','custom']

SERVER_SIDE_DICT = {"millennial":MillennialServerSide,
                    "appnexus":AppNexusServerSide,
                    "inmobi":InMobiServerSide,
                    "brightroll":BrightRollServerSide,
                    "jumptap":JumptapServerSide,
                    "greystripe":GreyStripeServerSide,
                    "mobfox":MobFoxServerSide,}

############## HELPER FUNCTIONS ################
def memcache_key_for_date(udid,datetime,db_key):
  return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d'),db_key)

def memcache_key_for_hour(udid,datetime,db_key):
  return '%s:%s:%s'%(udid,datetime.strftime('%y%m%d%H'),db_key)

################### AUCTION ##################

class AdAuction(object):
    MAX_ADGROUPS = 30
    
    @classmethod
    def request_third_party_server(cls,request,adunit,adgroups):
        if not isinstance(adgroups,(list,tuple)):
            multiple = False
            adgroups = [adgroups]
        else:
            multiple = True    
        rpcs = []
        for adgroup in adgroups:
            if adgroup.network_type in SERVER_SIDE_DICT:
                KlassServerSide = SERVER_SIDE_DICT[adgroup.network_type]
                server_side = KlassServerSide(request, adunit) 
                trace_logging.warning("%s url %s"%(KlassServerSide,server_side.url))
                
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
        return rpcs if multiple else rpcs[0]    
        
    # Runs the auction itself.  Returns the winning creative, or None if no creative matched
    @classmethod
    def run(cls, request=None,
  		         site=None,
  		         q=None,
  		         addr=None,
  		         excluded_creatives=None,
  		         udid=None,
  		         ll=None,
  		         request_id=None,
  		         now=None,
  		         testing=None,
  		         user_agent=None,
  		         adunit_context=None,
  		         experimental=None):
        adunit = site
        keywords = q
        geo_predicates = AdAuction.geo_predicates_for_rgeocode(addr)
        exclude_params = excluded_creatives

        #if only one geo_pred (it's a country) check to see if this country has multiple
        #possible codes.  If it does, get all of them and use them all
        if len(addr) == 1 and ACCEPTED_MULTI_COUNTRY.has_key(addr[0]):
            geo_predicates = reduce(lambda x,y: x+y, [AdAuction.geo_predicates_for_rgeocode([address]) for address in ACCEPTED_MULTI_COUNTRY[addr[0]]])
        
        device_predicates = AdAuction.device_predicates_for_request(request)
        
        excluded_predicates = AdAuction.exclude_predicates_params(exclude_params)
        trace_logging.warning("keywords=%s, geo_predicates=%s, device_predicates=%s" % (keywords, geo_predicates, device_predicates))
        
        # Matching strategy: 
        # 1) match all ad groups that match the placement that is in question, sort by priority
        # 2) throw out ad groups owned by campaigns that have exceeded budget or are paused
        # 3) throw out ad groups that restrict by keywords and do not match the keywords
        # 4) throw out ad groups that do not match device and geo predicates
        all_ad_groups = adunit_context.adgroups
        
        trace_logging.info("All Campaigns Targeted at this AdUnit: %s"%[str(a.name) for a in all_ad_groups])
        
        trace_logging.info("##############################")
        trace_logging.info("Excluding Ineligible Campaigns")
        trace_logging.info("##############################")
        
        # # campaign exclusions... budget + time
        ALL_FILTERS     = (budget_filter(),
                            active_filter(), 
        					lat_lon_filter(ll),
                            kw_filter(keywords), 
                            geo_filter(geo_predicates), 
                            device_filter(device_predicates) 
                           ) 
        
        all_ad_groups = filter(mega_filter(*ALL_FILTERS), all_ad_groups)
        for (func, warn, lst) in ALL_FILTERS:
            trace_logging.info(warn % [str(a.name) for a in lst])
        
        # TODO: user based frequency caps (need to add other levels)
        # to add a frequency cap, add it here as follows:
        #         ('name',     key_function),
        #   IMPORTANT: The corresponding frequency_cap property of adgroup must match the name as follows:
        #                   (adgroup).<name>_frequency_cap, eg daily_frequency_cap, hourly_frequency_cap
        #                   otherwise the filter will not fetch the appropriate cap
        FREQS = (('daily',    memcache_key_for_date),
                  ('hourly',   memcache_key_for_hour),
                 )
        
        # Pull ALL keys (Before prioritizing) and batch get. This is slightly (according to test timings) 
        # better than filtering based on priority 
        user_keys = []
        for adgroup in all_ad_groups:
            for type, key_func in FREQS:
                try:
                    # This causes an exception if it fails, the variable is actually never used though.
                    temp = getattr(adgroup, '%s_frequency_cap' % type) 
                    user_keys.append(key_func(udid, now, adgroup.key()))
                except:
                    continue
        if user_keys:  
            frequency_cap_dict = memcache.get_multi(user_keys)    
        else:
            frequency_cap_dict = {}
        #build and apply list of frequency filter functions
        FREQ_FILTERS = [ freq_filter(type, key_func, udid, now, frequency_cap_dict) for (type, key_func) in FREQS ] 
        all_ad_groups = filter(all_freq_filter(*FREQ_FILTERS), all_ad_groups)
        
        for fil in FREQ_FILTERS: 
            func, warn, lst = fil
            trace_logging.info(warn % [str(a.name) for a in lst])
            
        # calculate the user experiment bucket
        user_bucket = hash(udid+','.join([str(ad_group.key()) for ad_group in all_ad_groups])) % 100 # user gets assigned a number between 0-99 inclusive
        trace_logging.warning("the user bucket is: #%d"%user_bucket)
        
    # determine in which ad group the user falls into to
    # otherwise give creatives in the other adgroups a shot
    # TODO: fix the stagger method how do we get 3 ads all at 100%
    # currently we just mod by 100 such that there is wrapping
        start_bucket = 0
        winning_ad_groups = []
      
    # sort the ad groups by the percent of users desired, this allows us 
    # to do the appropriate wrapping of the number line if they are nicely behaved
    # TODO: finalize this so that we can do things like 90% and 15%. We need to decide
    # what happens in this case, unclear what the intent of this is.
        all_ad_groups.sort(lambda x,y: cmp(x.percent_users if x.percent_users else 100.0,y.percent_users if y.percent_users else 100.0))
        for ad_group in all_ad_groups:
            percent_users = ad_group.percent_users if not (ad_group.percent_users is None) else 100.0
            if start_bucket <= user_bucket and user_bucket < (start_bucket + percent_users):
                winning_ad_groups.append(ad_group)
            start_bucket += percent_users
            start_bucket = start_bucket % 100 
        
        all_ad_groups = winning_ad_groups
        trace_logging.info("#####################")
        trace_logging.info(" Beginning Auction")
        trace_logging.info("#####################")
        
        # If any ad groups were returned, find the creatives that match the requested format in all candidates
        if len(all_ad_groups) > 0:
            trace_logging.info("All Eligible Campaigns: %s"%[str(a.name) for a in all_ad_groups])
            all_creatives = adunit_context.creatives
            if len(all_creatives) > 0:
                # for each priority_level, perform an auction among the various creatives 
                for p in CAMPAIGN_LEVELS: 
                    trace_logging.info("Trying priority level: %s"%p)
                    #XXX maybe optimize? meh
                    eligible_adgroups = [a for a in all_ad_groups if a.campaign.campaign_type == p]
                    trace_logging.info("Campaigns of this priority: %s"%[str(a.name) for a in eligible_adgroups])
                    if not eligible_adgroups:
                        continue
                    players = adunit_context.get_creatives_for_adgroups(eligible_adgroups)
                    
                    # For now we only use sampling on the experimental server
                    if experimental:
                        # Construct dict: k=player, v=ecpm
                        player_ecpm_dict = optimizer.get_ecpms(adunit_context,
                                                               players)
                    else:
                        # Construct dict: k=player, v=ecpm
                        player_ecpm_dict = optimizer.get_ecpms(adunit_context,
                                                               players,
                                                               sampling_fraction=0.0)

                    players.sort(lambda x,y: cmp(player_ecpm_dict[y], player_ecpm_dict[x]))
        
                    while players:
                        winning_ecpm = player_ecpm_dict[players[0]]
                        trace_logging.info("Trying to get creatives: %s"%[str(c.name).replace("dummy","") if c.name else c.name for c in players])
                        trace_logging.warning("auction at priority=%s: %s, max eCPM=%s" % (p, players, winning_ecpm))
                        if winning_ecpm >= site.threshold_cpm(p):
        
                            # exclude according to the exclude parameter must do this after determining adgroups
                            # so that we maintain the correct order for user bucketing
                            # TODO: we should exclude based on creative id not ad type :)
        
                            # TODO: move format and exclude above players (right now we're doing the same thing twice)
                            # if the adunit is resizable then its format doesn't really matter
                            # all creatives can target it
                            site_format = None if site.resizable else site.format
                            CRTV_FILTERS = (format_filter(site_format), # remove wrong formats
                                                exclude_filter(exclude_params), # remove exclude parameter
                                                ecpm_filter(winning_ecpm, player_ecpm_dict), # remove creatives that aren't tied for first (winning ecpm)
                                               )
                            winners = filter(mega_filter(*CRTV_FILTERS), players)
                            for func, warn, lst in CRTV_FILTERS:
                                if lst:
                                    trace_logging.info(warn % [str(c.name).replace("dummy","") if c.name else c.name for c in lst])
        
                            # if there is a winning/eligible adgroup find the appropriate creative for it
                            winning_creative = None
        
                            if winners:
                                trace_logging.warning('winners %s' % [str(w.ad_group.name) for w in winners])
                                random.shuffle(winners)
                                trace_logging.info('Randomized winning campaigns: %s' % [str(w.ad_group.name) for w in winners])
        
                                # find the actual winner among all the eligble ones
                                # loop through each of the randomized winners making sure that the data is ready to display
                                for winner in winners:
                                    # if this adgroup does not requires an RPC
                                    # we can simply return the creative
                                    if not winner.adgroup.network_type in SERVER_SIDE_DICT:
                                        winning_creative = winner
                                        # if native, log native request
                                        if winner.ad_type in NATIVE_REQUESTS:
                                            mp_logging.log(None, event=mp_logging.REQ_EVENT, adunit=adunit, creative=winner, user_agent=user_agent, udid=udid)
                                        return winning_creative
                                    # if the adgroup requires an RPC    
                                    else:
                                        trace_logging.info('Attemping ad network request: %s ...'%winner.adgroup.network_type.title())
                                        rpc = AdAuction.request_third_party_server(request,site,winner.adgroup)
                                        # log a network "request"
                                        mp_logging.log(None, event=mp_logging.REQ_EVENT, adunit=adunit, creative=winner, user_agent=user_agent, udid=udid)
                                        try:
                                            result = rpc.get_result()
                                            server_tuple = rpc.serverside.bid_and_html_for_response(result)
                                            if server_tuple:
                                                bid = server_tuple[0]
                                                response = server_tuple[1]
                                                winning_creative = winner
                                                winning_creative.html_data = response
                                            
                                                if len(server_tuple) == 4:
                                                    width = server_tuple[2]
                                                    height = server_tuple[3]
                                                    winning_creative.width = width
                                                    winning_creative.height = height
                                                return winning_creative
                                        except Exception,e:
                                            import traceback, sys
                                            exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
                                            trace_logging.warning(exception_traceback)
                            else:
                                # remove players of the current winning e_cpm
                                trace_logging.warning('current players: %s'%players)
                                players = [ p for p in players if player_ecpm_dict[p] != winning_ecpm ] 
                                trace_logging.warning('remaining players %s'%players)
                            if not winning_creative:
                                #trace_logging.warning('taking away some players not in %s'%ad_groups)
                                #trace_logging.warning('current ad_groups %s' % [c.ad_group for c in players])
                                trace_logging.warning('current players: %s'%players)
                                #players = [c for c in players if not c.ad_group in ad_groups]  
                                players = [ p for p in players if p not in winners ] 
                                trace_logging.warning('remaining players %s'%players)
                 # try at a new priority level   
        
        # nothing... failed auction
        trace_logging.warning("auction failed, returning None")
        return None
        
    @classmethod
    def geo_predicates_for_rgeocode(c, r):
        # r = [US, CA SF] or []
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # TODO: DEFAULT COUNTRY SHOULD NOT BE US!!!!!!!
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if len(r) == 0:
            return ["country_name=US","country_name=*"] # ["country_name"=*] or ["country_name=US] ["country_name="CD"]
        elif len(r) == 1:
            return ["country_name=%s" % r[0], "country_name=*"]
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
        
        if self.request.get('jsonp', '0') == '1':
            jsonp = True
            callback = self.request.get('callback')
        else:
            callback = None
            jsonp = False

        if self.request.get("debug_mode","0") == "1":
            debug = True
        else:
            debug = False
        
        if self.request.get('admin_debug_mode','0') == "1":
            admin_debug_mode = True
            trace_logging.log_levels = [logging.info,logging.debug,logging.warning,
                                        logging.error,logging.critical,]
        else:
            admin_debug_mode = False 

        trace_logging.start()
        trace_logging.response = self.response
        
        id = self.request.get("id")
        experimental = self.request.get("exp")
        now = datetime.datetime.now()
        
        # Get or create all the relevant database information for auction
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(id)
        adunit = adunit_context.adunit
        
        # # Send a fraction of the traffic to the experimental servers
        experimental_fraction = adunit.app_key.experimental_fraction or 0.0
        
        # If we are not already on the experimental server, redirect some fraction
        rand_dec = random.random() # Between 0 and 1
        if (not experimental and rand_dec < experimental_fraction):
            
            # Create new id for alternate server
            experimental_app ="mopub-experimental"
            old_key = db.Key(id)
            new_key = db.Key.from_path(old_key.kind(), old_key.id_or_name(), _app=experimental_app )
            new_id = str(new_key)
            
            query_string = self.request.url.split("/m/ad?")[1] + "&exp=1"
            exp_url = "http://" + experimental_app + ".appspot.com/m/ad?" + query_string
            # exp_url = "http://localhost:8081/m/ad?" + query_string
            
            exp_url = exp_url.replace(id, new_id) # Splice in proper id
            trace_logging.info("Redirected to experimental server: " + exp_url)
            return self.redirect(exp_url)
        
        mp_logging.log(self.request, event=mp_logging.REQ_EVENT, adunit=adunit)  
        
        trace_logging.warning("User Agent: %s"%helpers.get_user_agent(self.request))
        country_re = r'[a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z])'
        countries = re.findall(country_re, helpers.get_user_agent(self.request))
        addr = []
        if len(countries) == 1:
            countries = [c.upper() for c in countries]
            addr = tuple(countries)
        
        site = adunit
        
        if self.request.get('testing') == TEST_MODE:
            # If we are running tests from ad_server_tests, don't use caching
            testing = True
            adunit_context = AdUnitContext.wrap(adunit)
            now = datetime.datetime.fromtimestamp(float(self.request.get('dt')))
        else:
            testing = False
        
        
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
        trace_logging.warning("keywords are %s" % keywords)
        
        # look up lat/lon
        ll = self.request.get('ll') if self.request.get('ll') else None
        
        # Reverse Geocode stuff isn't used atm
        # addr = self.rgeocode(self.request.get("ll")) if self.request.get("ll") else ()      
        # trace_logging.warning("geo is %s (requested '%s')" % (addr, self.request.get("ll")))
        
        # get creative exclusions usually used to exclude iAd because it has already failed
        excluded_creatives = self.request.get_all("exclude")
        if excluded_creatives:
            trace_logging.info("excluded_creatives: %s"%excluded_creatives)
        
        # TODO: get udid we should hash it if its not already hashed
        udid = self.request.get("udid")
        user_agent = helpers.get_user_agent(self.request)
        
        # create a unique request id, but only log this line if the user agent is real
        request_id = hashlib.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
          
        # get winning creative
        c = AdAuction.run(request = self.request,
	    						  site = site,
	    						  q=q, 
	    						  addr=addr, 
	    						  excluded_creatives=excluded_creatives, 
	    						  udid=udid, 
	    						  ll = ll,
	    						  request_id=request_id, 
	    						  now=now,
	    						  testing=testing,
	    						  user_agent=user_agent,
	    						  adunit_context=adunit_context,
	    						  experimental=experimental)
        # output the request_id and the winning creative_id if an impression happened
        if c:
            user_adgroup_daily_key = memcache_key_for_date(udid,now,c.ad_group.key())
            user_adgroup_hourly_key = memcache_key_for_hour(udid,now,c.ad_group.key())
            trace_logging.warning("user_adgroup_daily_key: %s"%user_adgroup_daily_key)
            trace_logging.warning("user_adgroup_hourly_key: %s"%user_adgroup_hourly_key)
            memcache.offset_multi({user_adgroup_daily_key:1,user_adgroup_hourly_key:1}, key_prefix='', namespace=None, initial_value=0)
                  
            # add timer and animations for the ad 
            refresh = adunit.refresh_interval
            # only send to client if there should be a refresh
            if refresh:
                self.response.headers.add_header("X-Refreshtime",str(refresh))
            # animation_type = random.randint(0,6)
            # self.response.headers.add_header("X-Animation",str(animation_type))    
        
        
            # create an ad clickthrough URL
            appid = c.conv_appid or ''
            ad_click_url = "http://%s/m/aclk?id=%s&cid=%s&c=%s&req=%s&udid=%s&appid=%s" % (self.request.host,id, c.key(), c.key(),request_id, udid, appid)
            # ad an impression tracker URL
            track_url = "http://%s/m/imp?id=%s&cid=%s&udid=%s&appid=%s" % (self.request.host, id, c.key(), udid, appid)
            cost_tracker = "&rev=%.07f" 
            if c.adgroup.bid_strategy == 'cpm':
                cost_tracker = cost_tracker % (float(c.adgroup.bid)/1000)
                track_url += cost_tracker
            elif c.adgroup.bid_strategy == 'cpc':
                cost_tracker = cost_tracker % c.adgroup.bid
                ad_click_url += cost_tracker
        
            self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
            self.response.headers.add_header("X-Imptracker", str(track_url))
            
          
            # add creative ID for testing (also prevents that one bad bug from happening)
            self.response.headers.add_header("X-Creativeid", "%s" % c.key())
        else:
            track_url = None  
            ad_click_url = None
          
        # render the creative 
        rendered_creative = self.render_creative(c, 
                                                        site                = site, 
                                                        q                   = q, 
                                                        addr                = addr,
                                                        excluded_creatives  = excluded_creatives, 
                                                        request_id          = request_id, 
                                                        v                   = int(self.request.get('v') or 0),
                                                        track_url           = track_url,
                                                        debug               = debug,
                                                        ) 
                                      
        if jsonp:
            self.response.out.write('%s(%s)' % (callback, dict(ad=str(rendered_creative or ''), click_url = str(ad_click_url))))
        elif not (debug or admin_debug_mode):                                                    
            self.response.out.write(rendered_creative)
        else:
            trace_logging.rendered_creative = rendered_creative
            trace_logging.render()
        
          
    def render_creative(self, c, track_url=None, **kwargs):
        self.TEMPLATES = TEMPLATES
        if c:
            # rename network so its sensical
            if c.adgroup.network_type:
                c.name = c.adgroup.network_type
            
            trace_logging.info("##############################")
            trace_logging.info("##############################")
            trace_logging.info("Winner found, rendering: %s" % str(c.name))
            trace_logging.warning("Creative key: %s" % str(c.key()))
            trace_logging.warning("rendering: %s" % c.ad_type)
            site = kwargs["site"]
            adunit = site
            
            format = adunit.format.split('x')
            network_center = False
            if len(format) < 2:
                ####################################
                # HACK FOR TUNEWIKI
                # TODO: We should make this smarter
                # if the adtype is not html (e.g. image)
                # then we set the orientation to only landscape
                # and the format to 480x320
                ####################################
                if not c.ad_type == "html":
                    if adunit.landscape:
                        self.response.headers.add_header("X-Orientation","l")
                        format = ("480","320")
                    else:
                        format = (320,480)    
                                                
                elif not c.adgroup.network_type or c.adgroup.network_type in FULL_NETWORKS:
                    format = (320,480)
                elif c.adgroup.network_type:
                    #TODO this should be a littttleee bit smarter. This is basically saying default
                    #to 300x250 if the adunit is a full (of some kind) and the creative is from
                    #an ad network that doesn't serve fulls
                    network_center = True
                    format = (300, 250)
          
            template_name = c.ad_type
            #css to center things
            style = "<style type='text/css'> \
                          .network_center { \
                              position: fixed; \
                              top: 50%%; \
                              left: 50%%; \
                              margin-left: -%dpx !important; \
                              margin-top: -%dpx !important; \
                              } \
                      </style>"
            params = kwargs
            params.update(c.__dict__.get("_entity"))
            #centering non-full ads in fullspace
            if network_center:
                params.update({'network_style': style % tuple(a/2 for a in format)})
            else:
                params.update({'network_style':''})
            #success tracking pixel for admob
            #set up an invisible span
            hidden_span = 'var hid_span = document.createElement("span"); hid_span.setAttribute("style", "display:none");'
            #init an image, give it the right src url, pixel size, append to span
            tracking_pix = 'var img%(name)s = document.createElement("img"); \
                            img%(name)s.setAttribute("height", 1); \
                            img%(name)s.setAttribute("width", 1);\
                            img%(name)s.setAttribute("src", "%(src)s");\
                            hid_span.appendChild(img%(name)s);'
          
            # because we send the client the HTML, and THEN send requests to admob for content, just becaues our HTML 
            # (in this case the tracking pixel) works, DOESNT mean that admob has successfully returned a creative.
            # Because of the admob pixel has to be added AFTER the admob ad actually loads, this is done via javascript.
            # It's hella generic and not all clean and jQuery'd because (in theory) this will work on all platforms 
            # that support javascript (blackberry brower bs i'm looking at you)
          
            success = hidden_span
            success += tracking_pix % dict(name = 'first', src = track_url)
            if c.tracking_url:
                success += tracking_pix % dict(name = 'second', src = c.tracking_url) 
                params.update(trackingPixel='<span style="display:none;"><img src="%s"/><img src="%s"/></span>'% (c.tracking_url, track_url))
            else:
                params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>'%track_url)
            success += 'document.body.appendChild(hid_span);'
          
          
            if c.ad_type == "adsense":
                params.update({"title": ','.join(kwargs["q"]), "adsense_format": '300x250_as', "w": format[0], "h": format[1], "client": kwargs["site"].get_pub_id("adsense_pub_id")})
                params.update(channel_id=kwargs["site"].adsense_channel_id or '')
                # self.response.headers.add_header("X-Launchpage","http://googleads.g.doubleclick.net")
            elif c.ad_type == "admob":
                params.update({"title": ','.join(kwargs["q"]), "w": format[0], "h": format[1], "client": kwargs["site"].get_pub_id("admob_pub_id")})
                debug = kwargs["debug"]
                params.update(test_mode='true' if debug else 'false')
                # params.update(test_ad='<a href="http://m.google.com" target="_top"><img src="/images/admob_test.png"/></a>' if debug else '')
                self.response.headers.add_header("X-Launchpage","http://c.admob.com/")
            elif c.ad_type == "text_icon":
                if c.image:
                  params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
                if c.action_icon:
                  params["action_icon_div"] = '<div style="padding-top:5px;position:absolute;top:0;right:0;"><a href="'+c.url+'" target="_top"><img src="/images/'+c.action_icon+'.png" width=40 height=40/></a></div>'
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
                # must pass in parameters to fully render template
                # TODO: NOT SURE WHY I CAN'T USE: html_data = c.html_data % dict(track_pixels=success)
                html_data = c.html_data.replace(r'%(track_pixels)s',success)
                params.update(html_data=html_data)
                self.response.headers.add_header("X-Scrollable","1")
                self.response.headers.add_header("X-Interceptlinks","0")
            elif c.ad_type == "text":  
                self.response.headers.add_header("X-Productid","pixel_001")
              
              
            if kwargs["q"] or kwargs["addr"]:
                params.update(title=','.join(kwargs["q"]+list(kwargs["addr"])))
            else:
                params.update(title='')
           
            if kwargs["v"] >= 2:  
                params.update(finishLoad='<script>function finishLoad(){window.location="mopub://finishLoad";} window.onload = function(){finishLoad();} </script>')
                # extra parameters used only by admob template
                #add in the success tracking pixel
                params.update(admob_finish_load= success + 'window.location = "mopub://finishLoad";')
                params.update(admob_fail_load='window.location = "mopub://failLoad";')
            else:
                # don't use special url hooks because older clients don't understand    
                params.update(finishLoad='')
                # extra parameters used only by admob template
                params.update(admob_finish_load=success)
                params.update(admob_fail_load='')
               
            
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
                
                trace_logging.warning('pub id:%s'%kwargs["site"].get_pub_id("adsense_pub_id"))
                header_dict = {
                  "Gclientid":str(kwargs["site"].get_pub_id("adsense_pub_id")),
                  "Gcompanyname":str(kwargs["site"].account.adsense_company_name),
                  "Gappname":str(kwargs["site"].app_key.adsense_app_name),
                  "Gappid":"0",
                  "Gkeywords":str(kwargs["site"].keywords or ''),
                  "Gtestadrequest":"0",
                  "Gchannelids":str(kwargs["site"].adsense_channel_id or ''),        
                # "Gappwebcontenturl":,
                  "Gadtype":"GADAdSenseTextImageAdType", #GADAdSenseTextAdType,GADAdSenseImageAdType,GADAdSenseTextImageAdType
                  "Gtestadrequest":"0",
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
                self.response.headers.add_header("X-Format",'300x250_as')
               
                self.response.headers.add_header("X-Backgroundcolor","0000FF")
            elif str(c.ad_type) == 'admob':
                self.response.headers.add_header("X-Failurl",self.request.url+'&exclude='+str(c.ad_type))
                self.response.headers.add_header("X-Adtype", str('html'))
            else:  
                self.response.headers.add_header("X-Adtype", str('html'))
              
            if kwargs["q"] or kwargs["addr"]:
                params.update(title=','.join(kwargs["q"]+list(kwargs["addr"])))
            else:
               params.update(title='')
            self.response.headers.add_header("X-Backfill", str('html'))
            
            # pass the creative height and width if they are explicity set
            if c.width and c.height and 'full' not in site.format:
                self.response.headers.add_header("X-Width",str(c.width))
                self.response.headers.add_header("X-Height",str(c.height))
            
            # render the HTML body
            rendered_creative = self.TEMPLATES[template_name].safe_substitute(params)
            rendered_creative.encode('utf-8')
            
            return rendered_creative
            
            # Otherwise, if there was no creative
        if not c:
            trace_logging.info('Auction returning None')
            self.response.headers.add_header("X-Adtype", "clear")
            self.response.headers.add_header("X-Backfill", "clear")
            return None
            
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
                        trace_logging.warning("rgeocode Accuracy == 8")

                        country = placemark.get("AddressDetails").get("Country")
                        administrativeArea = country.get("AdministrativeArea") if country else None
                        subAdministrativeArea = administrativeArea.get("SubAdministrativeArea") if administrativeArea else None
                        locality = (subAdministrativeArea.get("Locality") if subAdministrativeArea else administrativeArea.get("Locality")) if administrativeArea else None
                        trace_logging.warning("country=%s, administrativeArea=%s, subAdminArea=%s, locality=%s" % (country, administrativeArea, subAdministrativeArea, locality))

                        return (locality.get("LocalityName") if locality else "", 
                                        administrativeArea.get("AdministrativeAreaName") if administrativeArea else "",
                                        country.get("CountryNameCode") if country else "")
                return ()
            else:
                return ()
        except:
            trace_logging.error("rgeocode failed to parse %s" % json)
            return ()

# Only exists in order to have data show up in apache logs
# Currently, this is called only by a taskqueue
# response is dummy
class AdRequestHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write("OK")

# /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUY1NsgDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGJvEIAw&udid=4863585ad8c80749
class AdImpressionHandler(webapp.RequestHandler):
    def get(self):
        
        # Update budgeting
        # TODO: cache this
        adunit_key = self.request.get('id')
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)
        creative_id = self.request.get('cid')
        creative = adunit_context.get_creative_by_key(creative_id)
        if creative.ad_group.bid_strategy == 'cpm':
            budget_service.apply_expense(creative.ad_group.campaign, creative.ad_group.bid/1000)
        
        if not self.request.get('testing') == TEST_MODE:
            mp_logging.log(self.request,event=mp_logging.IMP_EVENT,adunit=adunit_context.adunit)  
            
        self.response.out.write("OK")
    
class AdClickHandler(webapp.RequestHandler):
    # /m/aclk?udid=james&appid=angrybirds&id=ahRldmVudHJhY2tlcnNjYWxldGVzdHILCxIEU2l0ZRipRgw&cid=ahRldmVudHJhY2tlcnNjYWxldGVzdHIPCxIIQ3JlYXRpdmUYoh8M
    def get(self):
        
        if not self.request.get('testing') == TEST_MODE:
            mp_logging.log(self.request, event=mp_logging.CLK_EVENT)  
  
        udid = self.request.get('udid')
        mobile_app_id = self.request.get('appid')
        time = datetime.datetime.now()
        adunit_id = self.request.get('id')
        creative_id = self.request.get('cid')

        # Update budgeting
        creative = Creative.get(Key(creative_id))
        if creative.ad_group.bid_strategy == 'cpc':
            budget_service.apply_expense(creative.ad_group.campaign, creative.ad_group.bid/1000)


        # if driving download then we use the user datastore
        if udid and mobile_app_id and mobile_app_id != CLICK_EVENT_NO_APP_ID:
            # TODO: maybe have this section run asynchronously
            ce_manager = ClickEventManager()
            ce = ce_manager.log_click_event(udid, mobile_app_id, time, adunit_id, creative_id)

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
            self.response.out.write("ClickEvent:OK:")

# TODO: Process this on the logs processor 
class AppOpenHandler(webapp.RequestHandler):
    # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA
    def get(self):
        udid = self.request.get('udid')
        mobile_appid = self.request.get('id')
        aoe_manager = AppOpenEventManager()
        aoe, conversion_logged = aoe_manager.log_conversion(udid, mobile_appid, time=datetime.datetime.now())

        if aoe and conversion_logged:
            mp_logging.log(self.request, event=mp_logging.CONV_EVENT, adunit_id=aoe.conversion_adunit, creative_id=aoe.conversion_creative, udid=udid)
            self.response.out.write("ConversionLogged:"+str(conversion_logged)+":"+str(aoe.key())) 
        else:
            self.response.out.write("ConversionLogged:"+str(conversion_logged)) 


class TestHandler(webapp.RequestHandler):
  # /m/open?v=1&udid=26a85bc239152e5fbc221fe5510e6841896dd9f8&q=Hotels:%20Hotel%20Utah%20Saloon%20&id=agltb3B1Yi1pbmNyDAsSBFNpdGUY6ckDDA&r=http://googleads.g.doubleclick.net/aclk?sa=l&ai=BN4FhRH6hTIPcK5TUjQT8o9DTA7qsucAB0vDF6hXAjbcB4KhlEAEYASDgr4IdOABQrJON3ARgyfb4hsijoBmgAbqxif8DsgERYWRzLm1vcHViLWluYy5jb226AQkzMjB4NTBfbWLIAQHaAbwBaHR0cDovL2Fkcy5tb3B1Yi1pbmMuY29tL20vYWQ_dj0xJmY9MzIweDUwJnVkaWQ9MjZhODViYzIzOTE1MmU1ZmJjMjIxZmU1NTEwZTY4NDE4OTZkZDlmOCZsbD0zNy43ODM1NjgsLTEyMi4zOTE3ODcmcT1Ib3RlbHM6JTIwSG90ZWwlMjBVdGFoJTIwU2Fsb29uJTIwJmlkPWFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVk2Y2tEREGAAgGoAwHoA5Ep6AOzAfUDAAAAxA&num=1&sig=AGiWqtx2KR1yHomcTK3f4HJy5kk28bBsNA&client=ca-mb-pub-5592664190023354&adurl=http://www.sanfranciscoluxuryhotels.com/
    def get(self):
        from ad_server.networks.greystripe import GreyStripeServerSide
        from ad_server.networks.millennial import MillennialServerSide
        from ad_server.networks.brightroll import BrightRollServerSide
        from ad_server.networks.jumptap import JumptapServerSide
        from ad_server.networks.mobfox import MobFoxServerSide
        from ad_server.networks.inmobi import InMobiServerSide
        key = self.request.get('id') or 'agltb3B1Yi1pbmNyCgsSBFNpdGUYAgw'
        delay = self.request.get('delay') or '5'
        delay = int(delay)
        adunit = Site.get(key)
        network_name = self.request.get('network','BrightRoll')
        ServerSideKlass = locals()[network_name+"ServerSide"]
        
        
        server_side = ServerSideKlass(self.request,adunit)
        self.response.out.write("URL: %s <br/>PAYLOAD: %s <br/> HEADERS: %s<br/><br/>"%(server_side.url,server_side.payload,server_side.headers))
        
        rpc = urlfetch.create_rpc(delay) # maximum delay we are willing to accept is 1000 ms
        
        payload = server_side.payload
        if payload == None:
            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
        else:
            urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)
        
        
        # ... do other things ...
        
        try:
            result = rpc.get_result()
            if result.status_code == 200:
                server_tuple = server_side.bid_and_html_for_response(result)
                bid = server_tuple[0]
                response = server_tuple[1]
                if len(server_tuple) > 2:
                    width = server_tuple[2]
                    height = server_tuple[3]
                else:
                    width = "UNKOWN"
                    height = "UNKOWN"    
                # self.response.out.write(response)
            self.response.out.write("%s<br/> %s %s %s %s"%(server_side.url+'?'+payload if payload else '',bid,response, width, height))
        except urlfetch.DownloadError:
            self.response.out.write("%s<br/> %s"%(server_side.url,"response not fast enough"))
        except Exception, e:
            self.response.out.write("%s <br/> %s"%(server_side.url, e)) 
          
    def post(self):
        trace_logging.info("%s"%self.request.headers["User-Agent"])  
        self.response.out.write("hello world")
        
# TODO: clears the cache USE WITH FEAR
class ClearHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(memcache.flush_all())
    
class PurchaseHandler(webapp.RequestHandler):
    def post(self):
        trace_logging.info(self.request.get("receipt"))
        trace_logging.info(self.request.get("udid"))
        self.response.out.write("OK")    
        

def main():
    application = webapp.WSGIApplication([('/m/ad', AdHandler), 
                                          ('/m/imp', AdImpressionHandler),
                                          ('/m/aclk', AdClickHandler),
                                          ('/m/open', AppOpenHandler),
                                          ('/m/track', AppOpenHandler),
                                          ('/m/test', TestHandler),
                                          ('/m/clear', ClearHandler),
                                          ('/m/purchase', PurchaseHandler),
                                          ('/m/req',AdRequestHandler),], 
                                          debug=DEBUG)
    run_wsgi_app(application)
    # wsgiref.handlers.CGIHandler().run(application)
    
# webapp.template.register_template_library('filters')
if __name__ == '__main__':
    main()
