#!/usr/bin/env python
#
import datetime, time, logging

from google.appengine.ext import db
from google.appengine.api import urlfetch

#
# Request
#
# this memorializes the fact that we hit the ad server
# it records sundry items about the fetch that we did.
#
# This is a db.Model in case you wanted to store it in the datastore,
# but we currently do not do this (for scale and reliability).
#

class Request(db.Model):
    host = db.StringProperty()
    url = db.StringProperty()
    success = db.BooleanProperty()
    status_code = db.IntegerProperty()
    status_message = db.StringProperty()
    request_ms = db.IntegerProperty()
    response_size = db.IntegerProperty()
    t = db.DateTimeProperty()

    def go(self):
        self.t = datetime.datetime.now()
        clock = time.time()
        try:
            resp = urlfetch.fetch("http://%s%s" % (self.host, self.url))
            self.request_ms = int((time.time() - clock) * 1000.0)
            self.success = resp.status_code == 200
            if self.success:
                logging.info("Ping successful: "+self.url)
            else:
                logging.error("Error (response = "+str(resp.status_code)+"): "+self.url)
            self.status_code = resp.status_code
            self.status_message = ""
            self.response_size = len(resp.content)
        except urlfetch.DownloadError:
            logging.error("Download Error (probably timeout): "+self.url)
            self.request_ms = int((time.time() - clock) * 1000.0)
            self.success = False
            self.status_message = "Failed"

class AdTest(db.Model):
	adunit_app_name = db.StringProperty()
	adunit_name = db.StringProperty()
	adunit_id = db.StringProperty(required=True)  
	active = db.BooleanProperty(default=False)      
