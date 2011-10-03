#!/usr/bin/env python
#
import os
import sys
import simplejson
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
for k in [k for k in sys.modules if k.startswith('django')]: 
    del sys.modules[k]
use_library('django', '1.2')

from models import *

from google.appengine.api import users, mail
import datetime, time, random, logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache

from google.appengine.api import urlfetch
from google.appengine.ext import db

template.register_template_library('filters.filters')

#makes changes required for local testing / production servers
IS_PRODUCTION = True
if not IS_PRODUCTION:
    from load_adunits import *
    AdTest(adunit_app_name="", adunit_name="", adunit_id="agltb3B1Yi1pbmNyDAsSBFNpdGUYrLwgDA", active=True).put()

URLS = ["&udid=mopubcanary&q=",
        "&udid=mopubcanary&q=keywords",
        "&udid=mopubcanary&q=geo-location&ll=37.0625,-95.677068"]

MAX_REQUESTS = 100
LAST_SUCCESS_THRESHOLD = 3

###
# Shows a simple page that catalogs recent pings and the overall
# health of all the ad servers.

class PerformanceHandler(webapp.RequestHandler):
    def get(self):
        aggregate_requests = memcache.get("aggregate_requests") or []
        failure_rate = memcache.get("failure_rate")
        last_success = memcache.get("last_success")
        avg_latency = memcache.get("avg_latency")
        
        averages = [m for m, r in aggregate_requests]
        last = [r for m, r in aggregate_requests]

        # determine overall health
        if averages and avg_latency:
            error = failure_rate > 0.10 and last_success >= LAST_SUCCESS_THRESHOLD
            warning = (failure_rate > 0.01 or avg_latency > 400) and not error
            ok = failure_rate <= 0.01 and avg_latency <= 400 and not error and not warning
            logging.info("we should have something")
        else:
            error = False
            warning = False
            ok = False
            logging.info("Nope, don't got it")
            
        now = datetime.datetime.now()

        self.response.out.write(template.render('aggregatePerformance.html',
                     {"averages": averages[:50],
                      "last": last[:50],
                      "error": error, "warning": warning, "ok": ok,
                      "now": now,
                      "start": now - datetime.timedelta(minutes=50),
                      "failure_rate": failure_rate, 
                      "last_success": last_success,         
                      "avg": avg_latency, 
                      "median": memcache.get("median_latency")}))

###
# Shows a simple page that catalogs recent pings and the overall
# health of the ad server with the given id.
            
class PerformanceIdHandler(webapp.RequestHandler):
    def get(self, id='agltb3B1Yi1pbmNyDAsSBFNpdGUYrLwgDA'):
        last = memcache.get("%s-last-requests" % id) or []
        failure_rate = memcache.get("%s-failure_rate" % id)
        last_success = memcache.get("%s-last_success" % id)
        avg_latency = memcache.get("%s-avg_latency" % id)

        # determine overall health
        if last and avg_latency:
            error = failure_rate > 0.10 and last_success >= LAST_SUCCESS_THRESHOLD
            warning = (failure_rate > 0.01 or avg_latency > 400) and not error
            ok = failure_rate <= 0.01 and avg_latency <= 400 and not error and not warning
            logging.info("we should have something")
        else:
            error = False
            warning = False
            ok = False
            logging.info("Nope, don't got it")

        now = datetime.datetime.now()

        self.response.out.write(template.render('idPerformance.html',
           {"last": last[:50], 
            "error": error, "warning": warning, "ok": ok,
            "now": now,
            "start": now - datetime.timedelta(minutes=50),
            "failure_rate": failure_rate, 
            "last_success": last_success,         
            "avg": avg_latency, 
            "median": memcache.get("%s-median_latency" % id)}))

###
# Pings all ad ids

class PingHandler(webapp.RequestHandler):
    def get(self):
        # ping all ad ids asynchronously
        rpcs = []
        ad_tests = AdTest.all()
        for ad_test in ad_tests:
            if ad_test.active:
                rpc = urlfetch.create_rpc()
                if IS_PRODUCTION:
                    urlfetch.make_fetch_call(rpc, 'http://mopub-canary.appspot.com/ping/%s' % ad_test.adunit_id)
                else:
                    urlfetch.make_fetch_call(rpc, 'http://%s/ping/%s' % (self.request.host.replace('8080','8081'), ad_test.adunit_id))
                rpcs.append(rpc)
        
        # calculate average latency
        latency_sum = 0
        latency_count = 0
        for rpc in rpcs:
            # try to wait for result of ping request if it's timing out pass
            try:
                latency_sum += simplejson.loads(rpc.get_result().content)['request_ms']
            except:
                pass
            latency_count += 1
        
        # pick a random request
        request_dict = simplejson.loads(rpcs[int(random.random() * len(rpcs))].get_result().content)
        now = datetime.datetime.now()
        r = Request(host=request_dict['host'], url=request_dict['url'], success=request_dict['success'], status_code=request_dict['status_code'],
        status_message=request_dict['status_message'], request_ms=request_dict['request_ms'], response_size=request_dict['response_size'],
        t=now)
        
        aggregate_requests = memcache.get("aggregate_requests") or []
        aggregate_requests.insert(0, (latency_sum / latency_count, r))
        memcache.set("aggregate_requests", aggregate_requests)

###
# Pings ad server URL for the id

class PingIdHandler(webapp.RequestHandler):
    def get(self, id):
        r = Request(host="ads.mopub.com", url="/m/ad?v=3&id=" + id + URLS[int(random.random() * len(URLS))])
        r.go()

        # add this to memcache circular buffer
        id_last = memcache.get("%s-last-requests" % id) or []
        id_last.insert(0, r)
        memcache.set("%s-last-requests" % id, id_last[:MAX_REQUESTS])
        
        # write out JSON response to return to PingHandler
        d = {'host': r.host, 'url': r.url, 'success': r.success, 'status_code': r.status_code, 'status_message': r.status_message,
        'request_ms': r.request_ms, 'response_size': r.response_size}
        self.response.out.write(simplejson.dumps(d))
	    
###
# Recalculates fun statistics for all ads and potentially sends canary email
	    
class RecalculateHandler(webapp.RequestHandler):
    def get(self):
        failure_sum = 0
        request_count = 0
        last_successes = []
        latencies = []
        
        ad_tests = AdTest.all()
        for ad_test in ad_tests:
            if ad_test.active:
                # recalculate statistics for all ad ids asynchronously
                rpc = urlfetch.create_rpc()
                if IS_PRODUCTION:
                    urlfetch.make_fetch_call(rpc, 'http://mopub-canary.appspot.com/r/%s' % ad_test.adunit_id)
                else:
                    urlfetch.make_fetch_call(rpc, 'http://%s/r/%s' % (self.request.host.replace('8080','8081'), ad_test.adunit_id))
            
                id_last = memcache.get("%s-last-requests" % ad_test.adunit_id) or []

                # update running totals for statistics
                failure_sum += sum(0 if x.success else 1 for x in id_last)
                request_count += len(id_last)
                id_last_successes = [i for i, v in enumerate(id_last) if v.success]
                if len(id_last_successes) > 0:
                    last_successes.append(min(id_last_successes))
                latencies.extend([x.request_ms for x in id_last if x.request_ms is not None])
        
        logging.info("request_count = %d" % request_count)
        # determine aggregate ad serving status    
        if request_count > 0:
            failure_rate = failure_sum / float(request_count);
            last_success = min(last_successes)
            memcache.set("failure_rate", failure_rate)
            memcache.set("last_success", last_success)
        
            latencies.sort()
            if len(latencies) > 0:
                avg_latency = int(sum(latencies) / float(len(latencies)))
                median_latency = latencies[len(latencies)/2] 

                # store latency stats in memcache
                memcache.set("avg_latency", avg_latency)
                memcache.set("median_latency", median_latency)
        
###
# Recalculates fun statistics

class RecalculateIdHandler(webapp.RequestHandler):
    def get(self, id):       
        last = memcache.get("%s-last-requests" % id) or []

        # determines ad serving status for the given id
        success_sum = sum([1 for x in last if x.success])
        failure_rate = success_sum / float(len(last)) if success_sum != 0 else float('NaN')
        last_success = min(i for i, v in enumerate(last) if v.success)
        memcache.set("%s-failure_rate" % id, failure_rate)
        memcache.set("%s-last_success" % id, last_success)
         
        # if there is a failure alert condition, send an email
        # Yes, this should continue to be sent until the failure condition has been addressed
        if last_success > LAST_SUCCESS_THRESHOLD:
	    logging.error("Last success has exceeded the threshold")
            mail.send_mail(sender='olp@mopub.com', 
                           to='eng@mopub.com',
                           subject="CODE RED: ad server has been down for several tries", 
                           body="Failure count=%d. See more at http://stats.mopub.com" % last_success)

        # recalculate latency median and average
        latencies = [x.request_ms for x in last if x.request_ms is not None]
        latencies.sort()
        if len(latencies) > 0:
            avg_latency = int(sum(latencies) / float(len(latencies)))
            median_latency = latencies[len(latencies)/2] 

            # store latency stats in memcache
            memcache.set("%s-avg_latency" % id, avg_latency)
            memcache.set("%s-median_latency" % id, median_latency)
            
class LinksHandler(webapp.RequestHandler):
    def get(self):
        adunits = [(ad_test.adunit_name, ad_test.adunit_id) for ad_test in AdTest.all() if ad_test.active]
        logging.info("ad_test.adunit_name " + adunits[0][0])
        logging.info("ad_test.adunit_id " + adunits[0][1])
        self.response.out.write(template.render('links.html',
                     {"adunits": adunits
                     }))       

application = webapp.WSGIApplication([
                  ('/', PerformanceIdHandler),                    # shows a splash page containing performance data for a fast ad id
                  ('/performance', PerformanceHandler),           # shows a splash page containing aggregate performance data
                  ('/performance/(.*)', PerformanceIdHandler),    # shows a splash page containing performance data for ad id
		  ('/ping', PingHandler),                         # pings all ad ids
                  ('/ping/(.*)', PingIdHandler),                  # pings ad server URL for ad id
                  ('/r', RecalculateHandler),                     # recalculates overall status
                  ('/r/(.*)', RecalculateIdHandler),              # recalculates status for ad id
                  ('/links', LinksHandler),                       # shows links to all ad id performance pages
                  ], debug=True)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()
