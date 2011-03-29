#!/usr/bin/env python
#
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

from google.appengine.dist import use_library
use_library('django', '1.2')

from models import Request

from google.appengine.api import users, mail
import datetime, time, random, logging

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache

template.register_template_library('filters.filters')

URLS = ["/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYwLQgDA&udid=mopubcanary&q=",
        "/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYwLQgDA&udid=mopubcanary&q=keywords",
        "/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYwLQgDA&udid=mopubcanary&q=geo-location&ll=37.0625,-95.677068",
        "/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYrLwgDA&udid=mopubcanary&q=",
        "/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYrLwgDA&udid=mopubcanary&q=keywords",
        "/m/ad?v=3&id=agltb3B1Yi1pbmNyDAsSBFNpdGUYrLwgDA&udid=mopubcanary&q=geo-location&ll=37.0625,-95.677068"]
MAX_REQUESTS = 100
LAST_SUCCESS_THRESHOLD = 3

###
# Shows a simple page that catalogs recent pings and the overall
# health of the ad server.

class IndexHandler(webapp.RequestHandler):
    def get(self):
        last = memcache.get("last-requests") or []
        failure_rate = memcache.get("failure_rate")
        last_success = memcache.get("last_success")
        avg_latency = memcache.get("avg_latency")

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

        self.response.out.write(template.render('index.html',
           {"last": last[:50], 
            "error": error, "warning": warning, "ok": ok,
            "now": now,
            "start": now - datetime.timedelta(minutes=50),
            "failure_rate": failure_rate, 
            "last_success": last_success,         
            "avg": avg_latency, 
            "median": memcache.get("median_latency")}))

###
# Pings the ad server

class PingHandler(webapp.RequestHandler):
    def get(self):
        r = Request(host="ads.mopub.com", url=URLS[int(random.random() * len(URLS))])
        r.go()

        # add this to memcache circular buffer
        last = memcache.get("last-requests") or []
        last.insert(0, r)
        memcache.set("last-requests", last[:MAX_REQUESTS])

###
# Recalculates fun statistics and potentially sends canary emails


class RecalculateHandler(webapp.RequestHandler):
    def get(self):       
        last = memcache.get("last-requests") or []

        # determines overall ad serving status
        failure_rate = sum(0 if x.success else 1 for x in last) / float(len(last))
        last_success = min(i for i, v in enumerate(last) if v.success)
        memcache.set("failure_rate", failure_rate)
        memcache.set("last_success", last_success)

        # if there is a failure alert condition, send an email
        # Yes, this should continue to be sent until the failure condition has been addressed
        if last_success > LAST_SUCCESS_THRESHOLD:
            mail.send_mail(sender='jpayne@mopub.com', 
                           to='support@mopub.com',
                           subject="CODE RED: ad server has been down for several tries", 
                           body="Failure count=%d. See more at http://stats.mopub.com" % last_success)
         
        # recalculate latency median and average
        latencies = [x.request_ms for x in last if x.request_ms is not None]
        latencies.sort()
        if len(latencies) > 0:
            avg_latency = int(sum(latencies) / float(len(latencies)))
            median_latency = latencies[len(latencies)/2] 

            # store latency stats in memcache
            memcache.set("avg_latency", avg_latency)
            memcache.set("median_latency", median_latency)

application = webapp.WSGIApplication([('/', IndexHandler),  # shows a splash page
                  ('/ping', PingHandler),                   # hits a random ad server URL
                  ('/r', RecalculateHandler),               # recalculates overall status
                  ], debug=False)

def main():
    run_wsgi_app(application)

if __name__ == '__main__':
    main()