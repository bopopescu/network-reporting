# !/usr/bin/env python

import os
import random
import datetime
import urllib

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
                                    os_filter,
                                   )
# from ad_server.adserver_templates import TEMPLATES
                                    
from common.utils import simplejson
from common.utils import helpers
from common.utils.marketplace_helpers import build_marketplace_dict
from common.constants import (FULL_NETWORKS,
                              ACCEPTED_MULTI_COUNTRY,
                              CAMPAIGN_LEVELS,
                             )

from string import Template
#from datetime import datetime

from google.appengine.api import users, urlfetch, memcache
from google.appengine.api import taskqueue
from google.appengine.ext import webapp, db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import images

from reporting.models import StatsModel

from ad_server.networks.appnexus import AppNexusServerSide
from ad_server.networks.brightroll import BrightRollServerSide
from ad_server.networks.chartboost import ChartBoostServerSide
from ad_server.networks.ejam import EjamServerSide
from ad_server.networks.greystripe import GreyStripeServerSide
from ad_server.networks.inmobi import InMobiServerSide
from ad_server.networks.jumptap import JumptapServerSide
from ad_server.networks.millennial import MillennialServerSide
from ad_server.networks.mobfox import MobFoxServerSide
from ad_server.optimizer import optimizer

from publisher.query_managers import AdUnitQueryManager, AdUnitContextQueryManager

from ad_server.adunit_context.adunit_context import AdUnitContext

from stats import stats_accumulator
from budget import budget_service
from google.appengine.ext.db import Key

from ad_server.debug_console import trace_logging
from ad_server import memcache_mangler
from ad_server import frequency_capping


############## CONSTANTS ###############

TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"

SERVER_SIDE_DICT = {"millennial":MillennialServerSide,
                    "appnexus":AppNexusServerSide,
                    "inmobi":InMobiServerSide,
                    "brightroll":BrightRollServerSide,
                    "chartboost":ChartBoostServerSide,
                    "ejam":EjamServerSide,
                    "jumptap":JumptapServerSide,
                    "greystripe":GreyStripeServerSide,
                    "mobfox":MobFoxServerSide,}

CRAWLERS = ["Mediapartners-Google,gzip(gfe)", "Mediapartners-Google,gzip(gfe),gzip(gfe)"]
MAPS_API_KEY = 'ABQIAAAAgYvfGn4UhlHdbdEB0ZyIFBTJQa0g3IQ9GZqIMmInSLzwtGDKaBRdEi7PnE6cH9_PX7OoeIIr5FjnTA'
FREQ_ATTR = '%s_frequency_cap'
NATIVE_REQUESTS = ['admob','adsense','iAd','custom','custom_native','admob_native','millennial_native']

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
                trace_logging.warning("payload: %s"%payload)
                trace_logging.warning("headers: %s"%server_side.headers)
                if payload == None:
                    urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers)
                else:
                    urlfetch.make_fetch_call(rpc, server_side.url, headers=server_side.headers, method=urlfetch.POST, payload=payload)
                # attaching the adgroup to the rpc
                rpc.adgroup = adgroup
                rpc.serverside = server_side
                rpcs.append(rpc)
        return rpcs if multiple else rpcs[0]    
        

    @classmethod
    def run(cls, request=None,
  		         adunit=None,
  		         keywords=None,
                 country_tuple=[],
  		         excluded_adgroups=[],
  		         udid=None,
  		         ll=None,
  		         request_id=None,
  		         now=datetime.datetime.now(),
  		         user_agent=None,
  		         adunit_context=None,
  		         experimental=None):
        """ Runs the auction to determine the appropriate adunit to display. 
        @returns: [winning_creative, on_fail_exclude_adgroups] """
        # TODO: Clean up variable names
        # TODO: For testability, should not require request


        # SPAM TEH SHIT OUT OF MPX.MOPUB.COM
        # try:
        #     spam_rpc = urlfetch.create_rpc(deadline=.1)
        #     urlfetch.make_fetch_call(spam_rpc, 'http://mpx.mopub.com/req?asdfasdfasdfasdf')
        #     spam_rpc.get_result()
        # except Exception, e:
        #     trace_logging.error("spam error: %s"%e)
        
        geo_predicates = AdAuction.geo_predicates_for_rgeocode(country_tuple)

        #if only one geo_pred (it's a country) check to see if this country has multiple
        #possible codes.  If it does, get all of them and use them all
        if len(country_tuple) == 1 and ACCEPTED_MULTI_COUNTRY.has_key(country_tuple[0]):
            geo_predicates = reduce(lambda x,y: x+y, [AdAuction.geo_predicates_for_rgeocode([country_tupleess]) for country_tupleess in ACCEPTED_MULTI_COUNTRY[country_tuple[0]]])
        
        device_predicates = AdAuction.device_predicates_for_request(request)
        
        trace_logging.warning("keywords=%s, geo_predicates=%s, device_predicates=%s" % (keywords, geo_predicates, device_predicates))
        
        # Matching strategy: 
        # 1) match all ad groups that match the placement that is in question, sort by priority
        # 2) throw out ad groups owned by campaigns that have exceeded budget or are paused
        # 3) throw out ad groups that restrict by keywords and do not match the keywords
        # 4) throw out ad groups that do not match device and geo predicates
        all_ad_groups = adunit_context.adgroups
        
        trace_logging.info("All Campaigns Targeted at this AdUnit: %s"%", ".join([a.name.encode('utf8') for a in all_ad_groups]))
        
        trace_logging.info("##############################")
        trace_logging.info("Excluding Ineligible Campaigns")
        trace_logging.info("##############################")
        
        # We first run filters at the adgroup level
        ALL_FILTERS = (exclude_filter(excluded_adgroups),
                       active_filter(), 
                       lat_lon_filter(ll),
                       kw_filter(keywords), 
                       geo_filter(geo_predicates), 
                       device_filter(device_predicates),
                       os_filter(user_agent),
                       budget_filter()) 
        
        all_ad_groups = filter(mega_filter(*ALL_FILTERS), all_ad_groups)
        for (func, warn, lst) in ALL_FILTERS:
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in lst]))
        
        # TODO: user based frequency caps (need to add other levels)
        # to add a frequency cap, add it here as follows:
        #         ('name',     key_function),
        #   IMPORTANT: The corresponding frequency_cap property of adgroup must match the name as follows:
        #                   (adgroup).<name>_frequency_cap, eg daily_frequency_cap, hourly_frequency_cap
        #                   otherwise the filter will not fetch the appropriate cap
        FREQS = (('daily', frequency_capping.memcache_key_for_date),
                  ('hourly', frequency_capping.memcache_key_for_hour),
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
            trace_logging.info(warn % ", ".join([a.name.encode('utf8') for a in lst]))
            
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
        
        # Initialize on_fail_exclude_adgroups to include all the previously excluded agdgroups
        on_fail_exclude_adgroups = excluded_adgroups
        
        # If any ad groups were returned, find the creatives that match the requested format in all candidates
        if len(all_ad_groups) > 0:
            trace_logging.info("All Eligible Campaigns: %s"%", ".join([a.name.encode('utf8') for a in all_ad_groups]))
            all_creatives = adunit_context.creatives
            if len(all_creatives) > 0:
                # for each priority_level, perform an auction among the various creatives 
                for p in CAMPAIGN_LEVELS: 
                    trace_logging.info("Trying priority level: %s"%p)
                    #XXX maybe optimize? meh
                    eligible_adgroups = [a for a in all_ad_groups if a.campaign.campaign_type == p]
                    trace_logging.info("Campaigns of this priority: %s"%", ".join([a.name.encode('utf8') for a in eligible_adgroups]))
                    if not eligible_adgroups:
                        continue
                    # if we're on marketplace level, do that marketplace shit
                    if p == 'marketplace':
                        # Build a big dict
                        mk_args = build_marketplace_dict(adunit = adunit,
                                                         kws = keywords,
                                                         udid = udid,
                                                         ua = user_agent,
                                                         ll = ll,
                                                         ip = request.remote_addr,
                                                         adunit_context = adunit_context,
                                                         country = helpers.get_country_code(request.headers, default=None))
                        # Turn it into a get query
                        trace_logging.info("\nSending to MPX: %s\n" % mk_args)
                        mpx_url = 'http://mpx.mopub.com/req?' + urllib.urlencode(mk_args)
                        xhtml = None
                        charge_price = None
                        # Try to get a response
                        crtv = adunit_context.get_creatives_for_adgroups(eligible_adgroups)
                        if isinstance(crtv, list):
                            crtv = crtv[0]
                        # set the creative as having done w/e
                        stats_accumulator.log(None, event=stats_accumulator.REQ_EVENT, adunit=adunit, creative=crtv, user_agent=user_agent, headers=request.headers, udid=udid)
                        try:
                            fetched = urlfetch.fetch(mpx_url, deadline=.2)
                            # Make sure it's a good response
                            trace_logging.info('MPX RESPONES CODE:%s'%fetched.status_code)
                            if fetched.status_code == 200:
                                data = simplejson.loads(fetched.content)
                                trace_logging.info('MPX REPSONSE:%s'%data)    
                                # With valid data
                                if data.has_key('xhtml') and data.has_key('charge_price') and data['xhtml']:
                                    xhtml = data['xhtml']
                                    charge_price = data['charge_price']
                                else:
                                    continue
                        except urlfetch.DownloadError, e:
                            pass
                        trace_logging.info('\n\nMPX Charge: %s\nMPX HTML: %s\n' % (charge_price, xhtml))
                        if xhtml:
                            # Should only be one
                            crtv.html_data = xhtml
                            # Should really be the pub's cut
                            crtv.adgroup.bid = charge_price
                            # I think we should log stuff here but I don't know how to do that
                            return [crtv, on_fail_exclude_adgroups]
                        else:
                            continue
                            




                    players = adunit_context.get_creatives_for_adgroups(eligible_adgroups)
                    
                    # For now we only use sampling on the experimental server
                    if experimental:
                        # Construct dict: k=player, v=ecpm
                        player_ecpm_dict = optimizer.get_ecpms(adunit_context.adunit,
                                                               players)
                    else:
                        # Construct dict: k=player, v=ecpm
                        player_ecpm_dict = optimizer.get_ecpms(adunit_context.adunit,
                                                               players,
                                                               sampling_fraction=0.0)

                    players.sort(lambda x,y: cmp(player_ecpm_dict[y], player_ecpm_dict[x]))
                
                    while players:
                        winning_ecpm = player_ecpm_dict[players[0]]
                        trace_logging.info("Trying to get creatives: %s"%", ".join([c.name.encode('utf8').replace("dummy","") if c.name else 'None' for c in players]))
                        trace_logging.warning("auction at priority=%s: %s, max eCPM=%s" % (p, players, winning_ecpm))
                        if True:
        
                            # exclude according to the exclude parameter must do this after determining adgroups
                            # so that we maintain the correct order for user bucketing
                            # TODO: we should exclude based on creative id not ad type :)
        
                            # TODO: move format and exclude above players (right now we're doing the same thing twice)
                            # if the adunit is resizable then its format doesn't really matter
                            # all creatives can target it
                            CRTV_FILTERS = (format_filter(adunit), # remove wrong formats
                                                ecpm_filter(winning_ecpm, player_ecpm_dict), # remove creatives that aren't tied for first (winning ecpm)
                                               )
                            winners = filter(mega_filter(*CRTV_FILTERS), players)
                            for func, warn, lst in CRTV_FILTERS:
                                if lst:
                                    trace_logging.info(warn %", ".join([c.name.encode('utf8').replace("dummy","") if c.name else '' for c in lst]))
        
                            # if there is a winning/eligible adgroup find the appropriate creative for it
                            winning_creative = None
        
                            if winners:
                                trace_logging.warning('winners %s' %", ".join([w.ad_group.name.encode('utf8') for w in winners]))
                                random.shuffle(winners)
                                trace_logging.info('Randomized winning campaigns: %s' % ", ".join([w.ad_group.name.encode('utf8') for w in winners]))
        
                                # find the actual winner among all the eligble ones
                                # loop through each of the randomized winners making sure that the data is ready to display
                                for winner in winners:
                                    # if this adgroup does not requires an RPC
                                    # we can simply return the creative
                                    if not winner.adgroup.network_type in SERVER_SIDE_DICT:
                                        winning_creative = winner
                                        # if native, log native request
                                        if winner.adgroup.network_type in NATIVE_REQUESTS:
                                            stats_accumulator.log(None, event=stats_accumulator.REQ_EVENT, adunit=adunit, creative=winner, user_agent=user_agent, headers=request.headers, udid=udid)
                                        # A native request could potential fail and must be excluded from subsequent requests    
                                        on_fail_exclude_adgroups.append(str(winning_creative.adgroup.key()))
                                        return [winning_creative, on_fail_exclude_adgroups]
                                    # if the adgroup requires an RPC    
                                    else:
                                        trace_logging.info('Attempting ad network request: %s ...'%winner.adgroup.network_type.title())
                                        rpc = AdAuction.request_third_party_server(request, adunit, winner.adgroup)
                                        # log a network "request"
                                        stats_accumulator.log(None, event=stats_accumulator.REQ_EVENT, adunit=adunit, creative=winner, user_agent=user_agent, headers=request.headers, udid=udid)
                                        try:
                                            result = rpc.get_result()
                                            server_tuple = rpc.serverside.bid_and_html_for_response(result)
                                            if server_tuple:
                                                bid = server_tuple[0]
                                                response = server_tuple[1]
                                                winning_creative = winner
                                                
                                                # We set the payload of the creative to be what we get back from the network
                                                winning_creative.html = response
                                            
                                                if len(server_tuple) == 4:
                                                    width = server_tuple[2]
                                                    height = server_tuple[3]
                                                    winning_creative.width = width
                                                    winning_creative.height = height
                                                return [winning_creative, on_fail_exclude_adgroups]
                                        except Exception,e:
                                            import traceback, sys
                                            exception_traceback = ''.join(traceback.format_exception(*sys.exc_info()))
                                            trace_logging.warning(exception_traceback)
                                            
                                        # Network request has failed. We won't try it again
                                        on_fail_exclude_adgroups.append(str(winner.adgroup.key()))
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
        return [None, on_fail_exclude_adgroups]
        
    @classmethod
    def geo_predicates_for_rgeocode(c, r):
        # r = [US, CA SF] or []
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # TODO: DEFAULT COUNTRY SHOULD NOT BE US!!!!!!!
        # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
        
        # I think the idea here is to enumerate the list of geo predicates 
        # that when matched will accept this ad_request
        
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
    
