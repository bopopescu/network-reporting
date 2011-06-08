# !/usr/bin/env python
import os
import re
import hashlib
import random
import time
import urllib
import datetime

import binascii

from ad_server.adserver_templates import TEMPLATES
                                    
from common.utils import helpers, simplejson
from common.constants import FULL_NETWORKS

from google.appengine.api import users, urlfetch, memcache

from google.appengine.ext import webapp, db
from google.appengine.api import images

from publisher.models import *
from advertiser.models import *

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager
from ad_server.optimizer.adunit_context import AdUnitContext, CreativeCTR

from mopub_logging import mp_logging
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging
from ad_server import memcache_mangler
from ad_server.auction.ad_auction import AdAuction
from ad_server import frequency_capping


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

        ufid = self.request.get('ufid', None)
        
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
        
        trace_logging.warning("User Agent: %s"%helpers.get_user_agent(self.request))
        country_re = r'[a-zA-Z][a-zA-Z][-_](?P<ccode>[a-zA-Z][a-zA-Z])'
        countries = re.findall(country_re, helpers.get_user_agent(self.request))
        country_tuple = []
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
        # country_tuple = self.rgeocode(self.request.get("ll")) if self.request.get("ll") else ()      
        # trace_logging.warning("geo is %s (requested '%s')" % (country_tuple, self.request.get("ll")))
        
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
                                          keywords=q, 
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
        
        # add timer and animations for the ad 
        # only send to client if there should be a refresh
        # animation_type = random.randint(0,6)
        # self.response.headers.add_header("X-Animation",str(animation_type))    
        
        refresh = adunit.refresh_interval
        if refresh:
            self.response.headers.add_header("X-Refreshtime",str(refresh))
        
        # output the request_id and the winning creative_id if an impression happened
        if creative:
            user_adgroup_daily_key = frequency_capping.memcache_key_for_date(udid, now, creative.ad_group.key())
            user_adgroup_hourly_key = frequency_capping.memcache_key_for_hour(udid, now, creative.ad_group.key())
            trace_logging.warning("user_adgroup_daily_key: %s"%user_adgroup_daily_key)
            trace_logging.warning("user_adgroup_hourly_key: %s"%user_adgroup_hourly_key)
            memcache.offset_multi({user_adgroup_daily_key:1,user_adgroup_hourly_key:1}, key_prefix='', namespace=None, initial_value=0)
        
            # create an ad clickthrough URL
            appid = creative.conv_appid or ''
            ad_click_url = "http://%s/m/aclk?id=%s&cid=%s&c=%s&req=%s&udid=%s&appid=%s" % (self.request.host, adunit_id, creative.key(), creative.key(),request_id, udid, appid)
            # ad an impression tracker URL
            track_url = "http://%s/m/imp?id=%s&cid=%s&udid=%s&appid=%s&random=%s" % (self.request.host, adunit_id, creative.key(), udid, appid, random.random())
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
        else:
            track_url = None  
            ad_click_url = None
          
        # render the creative 
        rendered_creative = self.render_creative(creative, 
                                          site = site, 
                                          keywords = q, 
                                          country_tuple = country_tuple,
                                          request_id = request_id, 
                                          version_number = int(self.request.get('v') or 0),
                                          track_url = track_url,
                                          debug = debug,
                                          on_fail_exclude_adgroups = on_fail_exclude_adgroups) 
                                      
        if jsonp:
            self.response.out.write('%s(%s)' % (callback, dict(ad=str(rendered_creative or ''), click_url = str(ad_click_url), ufid=str(ufid))))
        elif not (debug or admin_debug_mode):                                                    
            self.response.out.write(rendered_creative)
        else:
            trace_logging.rendered_creative = rendered_creative
            trace_logging.render()

    def render_creative(self, creative, 
                      site = None, 
                      keywords = None, 
                      country_tuple = None,
                      request_id = None, 
                      version_number = None,
                      track_url = None,
                      debug = False,
                      on_fail_exclude_adgroups = None):
        """ Returns a rendered HTML creative """
        self.TEMPLATES = TEMPLATES
        if creative:
            # rename network so its sensical
            if creative.adgroup.network_type:
                creative.name = creative.adgroup.network_type
            
            trace_logging.info("##############################")
            trace_logging.info("##############################")
            trace_logging.info("Winner found, rendering: %s" % str(creative.name))
            trace_logging.warning("Creative key: %s" % str(creative.key()))
            trace_logging.warning("rendering: %s" % creative.ad_type)

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
                if not creative.ad_type == "html":
                    if adunit.landscape:
                        self.response.headers.add_header("X-Orientation","l")
                        format = ("480","320")
                    else:
                        self.response.headers.add_header("X-Orientation","p")
                        format = (320,480)    
                                                
                elif not creative.adgroup.network_type or creative.adgroup.network_type in FULL_NETWORKS:
                    format = (320,480)
                elif creative.adgroup.network_type:
                    #TODO this should be a littttleee bit smarter. This is basically saying default
                    #to 300x250 if the adunit is a full (of some kind) and the creative is from
                    #an ad network that doesn't serve fulls
                    network_center = True
                    format = (300, 250)
          
            template_name = creative.ad_type
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
                      
            # TOMTODO: Fix this
            # params = kwargs
            params = {}
            
            params.update(creative.__dict__.get("_entity"))
            #Line1/2 None check biznass 
            if params.has_key('line1'):
                if params['line1'] is None:
                    params['line1'] = ''
            if params.has_key('line2'):
                if params['line2'] is None:
                    params['line2'] = ''
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

            success = hidden_span
            success += tracking_pix % dict(name = 'first', src = track_url)
            if creative.tracking_url:
                creative.tracking_url += '&random=%s'%random.random()
                success += tracking_pix % dict(name = 'second', src = creative.tracking_url) 
                params.update(trackingPixel='<span style="display:none;"><img src="%s"/><img src="%s"/></span>'% (creative.tracking_url, track_url))
            else:
                params.update(trackingPixel='<span style="display:none;"><img src="%s"/></span>' % track_url)
            success += 'document.body.appendChild(hid_span);'
          
            if creative.ad_type == "adsense":
                params.update({"title": ','.join(keywords), "adsense_format": '320x50_mb', "w": format[0], "h": format[1], "client": site.get_pub_id("adsense_pub_id")})
                params.update(channel_id=site.adsense_channel_id or '')
                # self.response.headers.add_header("X-Launchpage","http://googleads.g.doubleclick.net")
            elif creative.ad_type == "admob":
                params.update({"title": ','.join(keywords), "w": format[0], "h": format[1], "client": site.get_pub_id("admob_pub_id")})
                params.update(test_mode='true' if debug else 'false')
                # params.update(test_ad='<a href="http://m.google.com" target="_top"><img src="/images/admob_test.png"/></a>' if debug else '')
                self.response.headers.add_header("X-Launchpage","http://c.admob.com/")
            elif creative.ad_type == "text_icon":
                if creative.image:
                    params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(creative.image)
                if creative.action_icon:
                    #c.url can be undefined, don't want it to break
                    icon_div = '<div style="padding-top:5px;position:absolute;top:0;right:0;"><a href="'+(creative.url or '#')+'" target="_top">'
                    if creative.action_icon:
                        icon_div += '<img src="http://' + self.request.host + '/images/' + creative.action_icon+'.png" width=40 height=40/></a></div>'
                    params["action_icon_div"] = icon_div 
                else:
                    params['action_icon_div'] = ''
                # self.response.headers.add_header("X-Adtype", str('html'))
            elif creative.ad_type == "greystripe":
                params.update({"html_data": creative.html_data, "w": format[0], "h": format[1]})
                self.response.headers.add_header("X-Launchpage","http://adsx.greystripe.com/openx/www/delivery/ck.php")
                template_name = "html"
            elif creative.ad_type == "image":
                img = images.Image(creative.image)
                if creative.image_blob:
                    img = images.Image(blob_key=creative.image_blob)
                    params["image_url"] = images.get_serving_url(creative.image_blob)
                else:      
                    params["image_url"] = "data:image/png;base64,%s" % binascii.b2a_base64(creative.image)
                
                # if full screen we don't need to center
                if (not "full" in adunit.format) or ((img.width == 480.0 and img.height == 320.0 ) or (img.width == 320.0 and img.height == 480.0)):
                    css_class = ""
                else:
                    css_class = "center"    
                
                params.update({"w": img.width, "h": img.height, "w2":img.width/2.0, "h2":img.height/2.0, "class":css_class})
            elif creative.ad_type == "html":
                params.update({"html_data": creative.html_data, "w": format[0], "h": format[1]})
                # add the launchpage header for inmobi in case they have dynamic ads that use
                # window.location = 'http://some.thing/asdf'
                if creative.adgroup.network_type == "inmobi":
                    self.response.headers.add_header("X-Launchpage","http://c.w.mkhoj.com")

                
            elif creative.ad_type == "html_full":
                # must pass in parameters to fully render template
                # TODO: NOT SURE WHY I CAN'T USE: html_data = c.html_data % dict(track_pixels=success)
                html_data = creative.html_data.replace(r'%(track_pixels)s',success)
                params.update(html_data=html_data)
                self.response.headers.add_header("X-Scrollable","1")
                self.response.headers.add_header("X-Interceptlinks","0")
            elif creative.ad_type == "text":  
                self.response.headers.add_header("X-Productid","pixel_001")
              
              
            if version_number >= 2:  
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
            
            if str(creative.ad_type) == "iAd":
                # self.response.headers.add_header("X-Adtype","custom")
                # self.response.headers.add_header("X-Backfill","alert")
                # self.response.headers.add_header("X-Nativeparams",'{"title":"MoPub Alert View","cancelButtonTitle":"No Thanks","message":"We\'ve noticed you\'ve enjoyed playing Angry Birds.","otherButtonTitle":"Rank","clickURL":"mopub://inapp?id=pixel_001"}')
                # self.response.headers.add_header("X-Customselector","customEventTest")
                
                self.response.headers.add_header("X-Adtype", str(creative.ad_type))
                self.response.headers.add_header("X-Backfill", str(creative.ad_type))
                self.response.headers.add_header("X-Failurl", _build_fail_url(self.request.url, on_fail_exclude_adgroups))

            elif str(creative.ad_type) == "admob_native":
                if "full" in adunit.format:
                    self.response.headers.add_header("X-Adtype", "interstitial")
                    self.response.headers.add_header("X-Fulladtype", "admob_full")
                else:
                    self.response.headers.add_header("X-Adtype", str(creative.ad_type))
                    self.response.headers.add_header("X-Backfill", str(creative.ad_type))
                self.response.headers.add_header("X-Failurl", _build_fail_url(self.request.url, on_fail_exclude_adgroups))
                self.response.headers.add_header("X-Nativeparams", '{"adUnitID":"'+adunit.get_pub_id("admob_pub_id")+'"}')

            elif str(creative.ad_type) == "millennial_native":
                if "full" in adunit.format:
                    self.response.headers.add_header("X-Adtype", "interstitial")
                    self.response.headers.add_header("X-Fulladtype", "millennial_full")
                else:
                    self.response.headers.add_header("X-Adtype", str(creative.ad_type))
                    self.response.headers.add_header("X-Backfill", str(creative.ad_type))
                self.response.headers.add_header("X-Failurl", _build_fail_url(self.request.url, on_fail_exclude_adgroups))
                nativeparams_dict = {
                    "adUnitID":adunit.get_pub_id("millennial_pub_id"),
                    "adWidth":adunit.get_width(),
                    "adHeight":adunit.get_height()
                }
                self.response.headers.add_header("X-Nativeparams", simplejson.dumps(nativeparams_dict))
                
            elif str(creative.ad_type) == "adsense":
                self.response.headers.add_header("X-Adtype", str(creative.ad_type))
                self.response.headers.add_header("X-Backfill", str(creative.ad_type))
                
                trace_logging.warning('pub id:%s' % site.get_pub_id("adsense_pub_id"))
                header_dict = {
                  "Gclientid":str(site.get_pub_id("adsense_pub_id")),
                  "Gcompanyname":str(site.account.adsense_company_name),
                  "Gappname":str(site.app_key.adsense_app_name),
                  "Gappid":"0",
                  "Gkeywords":str(site.keywords or ''),
                  "Gtestadrequest":"0",
                  "Gchannelids":str(site.adsense_channel_id or ''),        
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
                    json_string_pairs.append('"%s":"%s"'%(key, value))
                json_string = '{'+','.join(json_string_pairs)+'}'
                self.response.headers.add_header("X-Nativeparams", json_string)
                
                # add some extra  
                self.response.headers.add_header("X-Failurl", _build_fail_url(self.request.url, on_fail_exclude_adgroups))
                self.response.headers.add_header("X-Format",'300x250_as')
               
                self.response.headers.add_header("X-Backgroundcolor","0000FF")
            elif creative.ad_type == "custom_native":
                creative.html_data = creative.html_data.rstrip(":")
                params.update({"method": creative.html_data})
                self.response.headers.add_header("X-Adtype", "custom")
                self.response.headers.add_header("X-Customselector",creative.html_data)

            elif str(creative.ad_type) == 'admob':
                self.response.headers.add_header("X-Failurl", _build_fail_url(self.request.url, on_fail_exclude_adgroups))
                self.response.headers.add_header("X-Adtype", str('html'))
            else:  
                self.response.headers.add_header("X-Adtype", str('html'))
              
            
            # pass the creative height and width if they are explicity set
            trace_logging.warning("creative size:%s"%creative.format)
            if creative.width and creative.height and 'full' not in site.format:
                self.response.headers.add_header("X-Width", str(creative.width))
                self.response.headers.add_header("X-Height", str(creative.height))
            
            # render the HTML body
            rendered_creative = self.TEMPLATES[template_name].safe_substitute(params)
            rendered_creative.encode('utf-8')
            
            return rendered_creative
            
            # Otherwise, if there was no creative
        if not creative:
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
        
########### HELPER FUNCTIONS ############
def _build_fail_url(original_url, on_fail_exclude_adgroups):
    """ Remove all the old &exclude= substrings and replace them with our new ones """
    clean_url = re.sub("&exclude=[^&]*", "", original_url)
    
    if not on_fail_exclude_adgroups:
        return clean_url
    else:
        return clean_url + '&exclude=' + '&exclude='.join(on_fail_exclude_adgroups)
    
    
    
