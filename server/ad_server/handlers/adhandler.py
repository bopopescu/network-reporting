# !/usr/bin/env python
""" The AdHandler takes in all requests to m/ad. It """

import hashlib
import random
import time
import traceback
import datetime
import logging

from common.utils import helpers
from common.utils.helpers import get_country_code


from google.appengine.ext import webapp, db

from publisher.query_managers import AdUnitContextQueryManager

from stats import stats_accumulator

from ad_server.debug_console import trace_logging

from ad_server.renderers.get_renderer import get_renderer_for_creative

# RENDERERS = {
#     "admob": AdMobRenderer,
#     "adsense":AdSenseRenderer,
#     "clear":BaseCreativeRenderer,
#     "html":BaseCreativeRenderer,
#     "html_full":BaseCreativeRenderer,
#     "iAd":BaseCreativeRenderer,
#     "image":BaseCreativeRenderer,
#     "text":BaseCreativeRenderer,
#     "text_icon":TextAndTileRenderer,
#     "admob_native":BaseCreativeRenderer,
#     "custom_native":BaseCreativeRenderer,
#     "millennial_native":BaseCreativeRenderer,
# }

from ad_server.auction import ad_auction

from ad_server.auction.client_context import ClientContext

TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"

# Primary ad auction handler
# -- Handles ad request parameters and normalizes for the auction logic
# -- Handles rendering the winning creative into the right HTML
#


class AdHandler(webapp.RequestHandler):

    def get(self):
        if self.request.get('admin_debug_mode', '0') == "1":
            try:
                self._get()
            except Exception, e:
                import sys
                self.response.out.write("Exception: %s<br/>" % e)
                self.response.out.write('TB2: %s' % '<br/>'.join(traceback.format_exception(*sys.exc_info())))
        else:
            self._get()

    def _get(self):
        ufid = self.request.get('ufid', None)

        # Do we need json padding?
        if self.request.get('jsonp', '0') == '1':
            jsonp = True
            callback = self.request.get('callback')
            failure_callback = self.request.get('failure_callback', None)
        else:
            callback = None
            failure_callback = None
            jsonp = False

        debug = False
        # For web tester, only shows logging.info
        # Internal web tester, shows all levels of logging
        if self.request.get('admin_debug_mode', '0') == "1":
            trace_logging.log_levels = [logging.info, logging.debug, logging.warning,
                                        logging.error, logging.critical]
            debug = True
        elif self.request.get("debug_mode", "0") == "1":
            # Not sure what the use of debug_mode is, deprecating it for now
            trace_logging.error("debug mode is deprecated")
            debug = True

        # For trace logger
        if self.request.get('log_to_console', '0') == '1':
            log_to_console = True
        else:
            log_to_console = False

        trace_logging.start(log_to_console=log_to_console)
        trace_logging.response = self.response

        trace_logging.info("Requesting URL:")
        trace_logging.info(str(self.request.url))

        adunit_id = self.request.get("id") or 'agltb3B1Yi1pbmNyDAsSBFNpdGUYkaoMDA'
        adunit_id = adunit_id.replace(' ', '')  # remove empty spaces
        experimental = self.request.get("exp")
        now = datetime.datetime.now()

        # Get or create all the relevant database information for auction
        adunit_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_id)
        creative = None
        adunit = None
        if adunit_context:
            adunit = adunit_context.adunit
            # # Send a fraction of the traffic to the experimental servers
            experimental_fraction = 1.0  # adunit.app_key.experimental_fraction or 0.0

            # If we are not already on the experimental server, redirect some fraction
            rand_dec = random.random()  # Between 0 and 1
            if (not experimental and rand_dec < experimental_fraction):
                return self._redirect_to_experimental("mopub-hrd", adunit_id)

            stats_accumulator.log(self.request, event=stats_accumulator.REQ_EVENT, adunit=adunit)

            trace_logging.warning("User Agent: %s" % helpers.get_user_agent(self.request))

            # We can get country_code from one of two places. It is a 2 character string
            country_code = self.request.get('country') or get_country_code(self.request.headers)

            if self.request.get('testing') == TEST_MODE:
                # If we are running tests from ad_server_tests, don't use caching
                now = datetime.datetime.fromtimestamp(float(self.request.get('dt')))

            # the user's adunit key was not set correctly...
            if adunit is None:
                self.error(404)
                self.response.out.write("Publisher adunit key %s not valid" % adunit_id)
                return

            # Prepare Keywords
            keywords = []
            if adunit.keywords and adunit.keywords != 'None':
                keywords += adunit.keywords.split(',')
            if self.request.get("q"):
                keywords += self.request.get("q").lower().split(',')

            trace_logging.warning("keywords are %s" % keywords)

            raw_udid = self.request.get("udid")

            # create a unique request id, but only log this line if the user agent is real
            request_id = hashlib.md5("%s:%s" % (self.request.query_string, time.time())).hexdigest()

            client_context = ClientContext(adunit=adunit,
                                    keywords=keywords,
                                    excluded_adgroup_keys=self.request.get_all("exclude"),
                                    raw_udid=raw_udid,
                                    mopub_id=helpers.make_mopub_id(raw_udid),
                                    ll=self.request.get('ll'),
                                    request_id=request_id,
                                    now=now,
                                    user_agent=helpers.get_user_agent(self.request),
                                    country_code=country_code,
                                    experimental=experimental,
                                    client_ip=helpers.get_client_ip(self.request))

            # Run the ad auction to get the creative to display
            ad_auction_results = ad_auction.run(client_context, adunit_context)

            # Unpack the results of the AdAuction
            creative, on_fail_exclude_adgroups = ad_auction_results

        # add timer and animations for the ad
        # only send to client if there should be a refresh
        # animation_type = random.randint(0,6)
        # self.response.headers.add_header("X-Animation",str(animation_type))

        if not creative:
            # TODO: We should have a no response "Renderer"
            trace_logging.info('Auction returning None')
            self.response.headers.add_header("X-Adtype", "clear")
            self.response.headers.add_header("X-Backfill", "clear")
            # We must add refresh always because if one given request
            # does not return an ad, the client should continue trying
            # again.
            refresh = adunit.refresh_interval if adunit else 30
            if refresh:
                self.response.headers.add_header("X-Refreshtime", str(refresh))
            rendered_creative = None

        else:
        #     # Output the request_id and the winning creative_id if an impression happened
        #     request_time = time.mktime(now.timetuple())
        #
        #     # Create an ad clickthrough URL
        #     appid = creative.conv_appid or ''
        #     ad_click_url = "http://%s/m/aclk?id=%s&cid=%s&c=%s&req=%s&reqt=%s&udid=%s&appid=%s" % (self.request.host, adunit_id, creative.key(), creative.key(),request_id, request_time, raw_udid, appid)
        #     # Add an impression tracker URL
        #     track_url = "http://%s/m/imp?id=%s&cid=%s&udid=%s&appid=%s&req=%s&reqt=%s&random=%s" % (self.request.host, adunit_id, creative.key(), raw_udid, appid, request_id, request_time, random.random())
        #     cost_tracker = "&rev=%.07f"
        #     if creative.adgroup.bid_strategy == 'cpm':
        #         cost_tracker = cost_tracker % (float(creative.adgroup.bid)/1000)
        #         track_url += cost_tracker
        #     elif creative.adgroup.bid_strategy == 'cpc':
        #         cost_tracker = cost_tracker % creative.adgroup.bid
        #         ad_click_url += cost_tracker

            creative.Renderer = get_renderer_for_creative(creative)
            creative_renderer = creative.Renderer(creative=creative,
                                         adunit=adunit,
                                         udid=raw_udid,
                                         client_context=client_context,
                                         now=now,
                                         request_host=self.request.host,
                                         request_url=self.request.url,
                                         request_id=request_id,
                                         version=int(self.request.get('v', '0')),
                                         on_fail_exclude_adgroups=on_fail_exclude_adgroups,
                                         keywords=keywords)

            rendered_creative, header_context = creative_renderer.render()
            # Add header context values to response.headers
            for key, value in header_context.items():
                self.response.headers.add_header(key, value)

        if jsonp:
            try:
                click_url = creative_renderer.click_url
            except UnboundLocalError:
                click_url = ''
            if rendered_creative:
                self.response.out.write('%s(%s)' % (callback,
                    dict(ad=str(rendered_creative),
                         click_url=str(click_url),
                         ufid=str(ufid))))
            else:
                self.response.out.write('%s()' % (failure_callback or callback))
        elif not (debug):
            self.response.out.write(rendered_creative)
        else:
            trace_logging.rendered_creative = rendered_creative
            trace_logging.render()

    def _redirect_to_experimental(self, experimental_app_name, adunit_id):
        # Create new id for alternate server
        old_key = db.Key(adunit_id)
#        new_key = db.Key.from_path(old_key.kind(), old_key.id_or_name(), _app=experimental_app_name)
        new_id = str(old_key)

        query_string = self.request.url.split("/m/ad?")[1] + "&exp=1"
        # exp_url = "http://" + experimental_app_name + ".appspot.com/m/ad?" + query_string
        exp_url = "http://adserver.mopub.com/m/ad?" + query_string
        # exp_url = "http://localhost:8081/m/ad?" + query_string

        exp_url = exp_url.replace(adunit_id, new_id)  # Splice in proper id
        trace_logging.info("Redirected to experimental server: " + exp_url)
        return self.redirect(exp_url)
