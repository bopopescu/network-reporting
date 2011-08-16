# !/usr/bin/env python 
""" The AdHandler takes in all requests to m/ad. It """

import os
import re
import hashlib
import random
import time
import traceback
import urllib
import datetime

import binascii
                                    
from common.utils import helpers, simplejson
from common.constants import FULL_NETWORKS

from google.appengine.api import users, urlfetch, memcache

from google.appengine.ext import webapp, db
from google.appengine.api import images

from publisher.models import *
from advertiser.models import *

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from ad_server.adunit_context.adunit_context import AdUnitContext, CreativeCTR

from mopub_logging import mp_logging
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging
from ad_server import memcache_mangler
from ad_server.auction.ad_auction import AdAuction
from ad_server import frequency_capping            

from google.appengine.api.images import InvalidBlobKeyError
            
from ad_server.networks.rendering import CreativeRenderer

TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"


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
        if self.request.get('admin_debug_mode','0') == "1":
            try:
                self._get()
            except Exception, e:
                import sys
                self.response.out.write("Exception: %s<br/>"%e)
                self.response.out.write('TB2: %s' % '<br/>'.join(traceback.format_exception(*sys.exc_info())))
        else:
            self._get()        
    
    def _get(self):
        ufid = self.request.get('ufid', None)     
        
        if self.request.get('jsonp', '0') == '1':
            jsonp = True
            callback = self.request.get('callback')
        else:
            callback = None
            jsonp = False

        if self.request.get("debug_mode","0") == "1":   
            # Not sure what the use of debug_mode is, deprecating it for now
            trace_logging.error("debug mode is deprecated")
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
        
        adunit_id = self.request.get("id")
        experimental = self.request.get("exp")
        now = datetime.datetime.now()
        
        # Get or create all the relevant database information for auction
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)
        adunit = adunit_context.adunit
        
        # # Send a fraction of the traffic to the experimental servers
        experimental_fraction = adunit.app_key.experimental_fraction or 0.0
        
        # If we are not already on the experimental server, redirect some fraction
        rand_dec = random.random() # Between 0 and 1
        if (not experimental and rand_dec < experimental_fraction):
            return self._redirect_to_experimental("mopub-experimental", adunit_id)
        
        mp_logging.log(self.request, event=mp_logging.REQ_EVENT, adunit=adunit)  
        
        trace_logging.warning("User Agent: %s" % helpers.get_user_agent(self.request))

        countries = [helpers.get_country_code(headers = self.request.headers)]
        if len(countries) == 1:
            countries = [c.upper() for c in countries]
            country_tuple = tuple(countries)
        
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
            self.response.out.write("Publisher adunit key %s not valid" % adunit_id)
            return
        
        # Prepare Keywords
        keywords = []
        if site.keywords and site.keywords != 'None':
            keywords += site.keywords.split(',')
        if self.request.get("q"):
            keywords += self.request.get("q").lower().split(',')
        trace_logging.warning("keywords are %s" % keywords)
        
        # look up lat/lon
        ll = self.request.get('ll') if self.request.get('ll') else None
        
        # get creative exclusions usually used to exclude iAd because it has already failed
        excluded_adgroups = self.request.get_all("exclude")
        if excluded_adgroups:
            trace_logging.info("Excluded Adgroups: %s" % excluded_adgroups)
        
        # TODO: get udid we should hash it if its not already hashed
        udid = self.request.get("udid")
        user_agent = helpers.get_user_agent(self.request)
        
        # create a unique request id, but only log this line if the user agent is real
        request_id = hashlib.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()
         

          
        # Run the ad auction to get the creative to display
        ad_auction_results = AdAuction.run(request = self.request,
                                           adunit = site,
                                           keywords=keywords, 
                                           excluded_adgroups=excluded_adgroups, 
                                           udid=udid, 
                                           ll = ll,
                                           request_id=request_id, 
                                           now=now,
                                           user_agent=user_agent,
                                           adunit_context=adunit_context,
                                           country_tuple=country_tuple, 
                                           experimental=experimental)
        
        # Unpack the results of the AdAuction
        creative, on_fail_exclude_adgroups = ad_auction_results
        
        # Attach various headers   
        refresh = adunit.refresh_interval
        if refresh:
            self.response.headers.add_header("X-Refreshtime",str(refresh))
        
        if not creative:
            trace_logging.info('Auction returning None')
            self.response.headers.add_header("X-Adtype", "clear")
            self.response.headers.add_header("X-Backfill", "clear") 
            track_url = None  
            ad_click_url = None
            rendered_creative = None 
        
        else:    
            # Output the request_id and the winning creative_id if an impression happened

            user_adgroup_daily_key = frequency_capping.memcache_key_for_date(udid, now, creative.ad_group.key())
            user_adgroup_hourly_key = frequency_capping.memcache_key_for_hour(udid, now, creative.ad_group.key())
            trace_logging.warning("user_adgroup_daily_key: %s"%user_adgroup_daily_key)
            trace_logging.warning("user_adgroup_hourly_key: %s"%user_adgroup_hourly_key)
            memcache.offset_multi({user_adgroup_daily_key:1,user_adgroup_hourly_key:1}, key_prefix='', namespace=None, initial_value=0)

            request_time = time.mktime(now.timetuple())
    
            # Create an ad clickthrough URL
            appid = creative.conv_appid or ''
            ad_click_url = "http://%s/m/aclk?id=%s&cid=%s&c=%s&req=%s&reqt=%s&udid=%s&appid=%s" % (self.request.host, adunit_id, creative.key(), creative.key(),request_id, request_time, udid, appid)
            # Add an impression tracker URL
            track_url = "http://%s/m/imp?id=%s&cid=%s&udid=%s&appid=%s&req=%s&reqt=%s&random=%s" % (self.request.host, adunit_id, creative.key(), udid, appid, request_id, request_time, random.random())
            cost_tracker = "&rev=%.07f" 
            if creative.adgroup.bid_strategy == 'cpm':
                cost_tracker = cost_tracker % (float(creative.adgroup.bid)/1000)
                track_url += cost_tracker
            elif creative.adgroup.bid_strategy == 'cpc':
                cost_tracker = cost_tracker % creative.adgroup.bid
                ad_click_url += cost_tracker
        
            self.response.headers.add_header("X-Clickthrough", str(ad_click_url))
            self.response.headers.add_header("X-Imptracker", str(track_url))
        
      
            # add creative ID for testing (also prevents that one bad bug from happening)
            self.response.headers.add_header("X-Creativeid", "%s" % creative.key())
                                                         
           
            ### Determine which creative to use:
            # template_name = creative.ad_type
          
            # Render the creative
            # TODO: we shouldn't need to pass response to this. 
            # TODO: headers should be handled separately
            rendered_creative = CreativeRenderer.render(self.response,   
                                           creative=creative,
                                           adunit=site, 
                                           keywords=keywords, 
                                           request_host=self.request.host, # Needed for serving static files
                                           request_url=self.request.url, # Needed for onfail urls  
                                           version_number = int(self.request.get('v') or 0),
                                           track_url = track_url,   
                                           on_fail_exclude_adgroups = on_fail_exclude_adgroups)       
                                      
        if jsonp:
            self.response.out.write('%s(%s)' % (callback, dict(ad=str(rendered_creative or ''), click_url = str(ad_click_url), ufid=str(ufid))))
        elif not (debug or admin_debug_mode):                                                    
            self.response.out.write(rendered_creative)
        else:
            trace_logging.rendered_creative = rendered_creative
            trace_logging.render()
    
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
            
    def _redirect_to_experimental(self, experimental_app_name, adunit_id):
        # Create new id for alternate server
        old_key = db.Key(adunit_id)
        new_key = db.Key.from_path(old_key.kind(), old_key.id_or_name(), _app=experimental_app_name )
        new_id = str(new_key)

        query_string = self.request.url.split("/m/ad?")[1] + "&exp=1"
        exp_url = "http://" + experimental_app_name + ".appspot.com/m/ad?" + query_string
        # exp_url = "http://localhost:8081/m/ad?" + query_string

        exp_url = exp_url.replace(adunit_id, new_id) # Splice in proper id
        trace_logging.info("Redirected to experimental server: " + exp_url)
        return self.redirect(exp_url)
        

    
