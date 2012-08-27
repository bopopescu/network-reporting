#!/usr/bin/env python
#
#
from google.appengine.ext import webapp
from google.appengine.ext import deferred
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail, urlfetch, taskqueue

from hive_job_launcher import launch_monthly_mpx_rev_hivejob, get_jobflow_state, get_output_data

import logging, email
import datetime, time, calendar
import csv
import StringIO
import sys
import os
import json

import boto
from boto.s3.connection import S3Connection
from boto.s3.key import Key

# access to AWS billing information
ACCESS_KEY_ID = 'AKIAJKOJXDCZA3VYXP3Q'
SECRET_ACCESS_KEY = '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'
S3_CONN = S3Connection(ACCESS_KEY_ID, SECRET_ACCESS_KEY)
S3_BUCKET = S3_CONN.get_bucket('mopub-aws-billing')

# where to send things 
SENDER="jim@mopub.com"
RCPT="billing@mopub.com"
RCPT_BCC="revforce@mopub.com"
MPX_URL="http://mpx.mopub.com/spent?api_key=asf803kljsdflkjasdf&start=%s&end=%s"
ADS_URL="http://read.mongostats.mopub.com/stats?pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY497jEww&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYnsnlEww&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eDlEww&hybrid=False&offline=False&start_date=%s&end_date=%s"
ADS_KEY="agltb3B1Yi1pbmNyDQsSBFNpdGUY497jEww||agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYnsnlEww||agltb3B1Yi1pbmNyEAsSB0FjY291bnQY1eDlEww"

class MainHandler(webapp.RequestHandler):
    def get(self):
        self.response.out.write(
            """<html><head></head>\
                <body align='center'>
                    <h1>John Chen Automator</h1>
                    <p><img src='/images/jfc.jpeg'></img></p>
                    <form method='post' action='/generate'>
                        <select name='m'><option value='1'>Jan</option>
                                         <option value='2'>Feb</option>
                                         <option value='3'>Mar</option>
                                         <option value='4'>Apr</option>
                                         <option value='5'>May</option>
                                         <option value='6'>Jun</option>
                                         <option value='7'>Jul</option>
                                         <option value='8'>Aug</option>
                                         <option value='9'>Sep</option>
                                         <option value='10'>Oct</option>
                                         <option value='11'>Nov</option>
                                         <option value='12'>Dec</option></select>
                        <select name='y'><option>2011</option><option selected>2012</option><option>2013</option><option>2014</option></select>
                        <input type='submit' value='Generate'></input>
                    </form>
                </body>
               </html>""")


class GenerateHandler(webapp.RequestHandler):
    def post(self):
        # fire off reporting API request
        m = int(self.request.get('m'))
        y = int(self.request.get('y'))
        jobId, s3_dir = launch_monthly_mpx_rev_hivejob(y, m)

        # initiates a task queue item that checks to see if this job has completed
        taskqueue.add(url="/check", params={"id": jobId, "s3_dir": s3_dir, "m": m, "y": y}, queue_name='jobcheck', countdown=60)
        
        # send a thank you email
        mail.send_mail(sender=SENDER,
                          to=RCPT,
                          bcc=RCPT_BCC,
                          subject="Your report request %s has been received" % jobId,
                          body="""Sir- Many machines have been provisioned to process your request. To check the status of your job, visit http://mopub-billing.appspot.com/check/%s. Yours, Automated John Chen""" % jobId)

        # play robot movie for user
        self.response.out.write(
            """<html><head>
                    <script type='text/javascript' src='/images/jwplayer.js'></script>
                </head>
                <body align='center'>
                    <h1>Automated John Chen</h1>
                    <center><p id="mediaplayer"></p></center>
                    <script type="text/javascript">
                      jwplayer('mediaplayer').setup({
                        'flashplayer': '/images/player.swf',
                        'id': 'playerID',
                        'width': '600',
                        'repeat': 'always',
                        'stretching': 'fill',
                        'autostart': 'true',
                        'controlbar': 'none',
                        'mute': 'true',
                        'file': '/images/robot.m4v'
                      });
                    </script>
                    <h1>Is Generating Your Report... Job ID is <a href="/check/%s">%s</a></h1>
                    <form method='get' action='/'>
                        <input type='submit' value='Thank You'></input>
                    </form>
                </body>
               </html>""" % (jobId, jobId))

class CheckHandler(webapp.RequestHandler):
    # Returns True if the job has completed, False if still running
    def _is_job_complete(self, jobId):
        state = get_jobflow_state(jobId)
        logging.info('%s\tjob %s state: %s' % (time.strftime('%b %d %Y %H:%M:%S'), jobId, state))
        if state in ['COMPLETED', 'WAITING']:
            return True, True   # done and successful
        if state in ['FAILED', 'TERMINATED']:
            return True, False  # done but failed
        return False, False   # still running

    # User visible status for a given job
    def get(self, jobId):
        done, successful = self._is_job_complete(jobId)
        if not done:
            message = "Is Still Working on Your Report... Hold Tight!"
        else:
            if successful:
                message = "Is Done!"
            else:
                message = "Has Failed :("
                
        self.response.out.write("""<html><head>
            </head>
            <body align='center'>
                <h1>Automated John Chen</h1>
                <p><img src='/images/jfc-cash.jpg'></img></p>
                <h1>%s</h1>
                <form method='get' action='/'>
                    <input type='submit' value='Thank You'></input>
                </form>
            </body>
           </html>""" % message)

    # Checks the S3 job - notifies user on failure
    # handles completed jobs by defering into a task q for later
    def post(self):
        jobId = self.request.get('id')
        s3_dir = self.request.get('s3_dir')
        done, successful = self._is_job_complete(jobId)

        if done and successful:
            # OK go iterate through this directory
            self.collect_job_output(jobId, s3_dir, int(self.request.get('m')), int(self.request.get('y')))
            return
        elif done and not successful:
            # This failed so we send a note indicating failure
            mail.send_mail(sender=SENDER,
                              to=RCPT,
                              subject="Your report %s could not be completed" % jobId,
                              body="""Sir- Sorry, I couldn't get it done. Apologies, Automated John Chen""")
        else:
            # Not complete yet so we fail this task and retry
            logging.info("JobID %s is not ready, retrying" % jobId)
            raise Exception("job not ready - retrying")

    def collect_job_output(self, jobId, s3_dir, m, y):
        logging.info(s3_dir)

        # grab the results... should look like:
        # """2-Person Studio (2personstudio@gmail.com)  Spit  6589  2475.147999999959
        # 8tracks (mopub@8tracks.com) 8tracks Android 49227 50386.09100000719
        # 8tracks (mopub@8tracks.com) 8tracks Radio 274 338.28749999999974
        # """
        sz = get_output_data(s3_dir)
        out = [[x[0].strip(), x[1].strip(), int(x[2]), "%.2f" % float(x[3])] for x in [l.split('\t') for l in sz.splitlines()] if len(x) == 4]

        # scrub list: sort tuples by account
        out.sort(lambda x,y: cmp(x[0], y[0]))

        # generate content
        output = StringIO.StringIO()
        output.write("Account,App,Impressions,Revenue\n")
        outputWriter = csv.writer(output, dialect='excel')
        for o in out:
            outputWriter.writerow(o)

        # create outbound email
        logging.info("Sending the report:\n%s" % output.getvalue())
        mail.send_mail(sender=SENDER,
                          to=RCPT,
                          bcc=RCPT_BCC,
                          subject="Your revenue report for %02d-%04d is attached (ID: %s)" % (m, y, jobId),
                          body="""SIR-\nGood times. Attached is your report. Sincerely, Automated John Chen""",
                          attachments=[("%s-%02d-%04d.csv" % (jobId, m, y), output.getvalue())])


class MpxReportHandler(webapp.RequestHandler):
    def ads_total(self, start, end):
        ads = json.loads(urlfetch.fetch(ADS_URL % (start.strftime("%y%m%d"), end.strftime("%y%m%d"))).content)
        return int(ads["all_stats"][ADS_KEY]["sum"]["request_count"])
        
    def mpx_total(self, start, end):
        # total spend
        mpx = json.loads(urlfetch.fetch(MPX_URL % (start.strftime("%m-%d-%Y"), end.strftime("%m-%d-%Y")), deadline=30).content)
        total = sum([x["spent"] for x in mpx.values()])

        # spend by DSP
        a=[(x["bidder_name"], x["spent"]) for x in mpx.values() if x["spent"] > 0]
        a.sort(lambda x,y: cmp(y[1],x[1]))
        
        return (total, a)
        
    def mpx_cleared(self, start, end):
        # total cleared impressions
        mpx = json.loads(urlfetch.fetch(MPX_URL % (start.strftime("%m-%d-%Y"), end.strftime("%m-%d-%Y")), deadline=30).content)
        total = sum([x["imp"] for x in mpx.values()])
        
        return total

        
    def cost_total(self, end):
        BANDWIDTH = ["AWS Data Transfer"]
        CPU = ["Amazon Elastic Compute Cloud", "Amazon Simple Notification Service", "Amazon Simple Queue Service", "Amazon SimpleDB", "Amazon Elastic MapReduce"]
        STORAGE = ["Amazon Simple Storage Service", "Amazon CloudFront"]
        
        # figure out the month involved and find in S3
        cost_key_name = "345840704531-aws-billing-csv-%s.csv" % end.strftime("%Y-%m")
        billing_data = S3_BUCKET.get_key(cost_key_name)
        
        if billing_data:
            # read billing contents, if it exists
            lines = [x for x in csv.DictReader(billing_data.get_contents_as_string().split("\n"), delimiter=',', quotechar='"')]
            bandwidth_cost = sum([float(x["CostBeforeTax"]) for x in lines if x.get('ProductName') in BANDWIDTH])
            storage_cost = sum([float(x["CostBeforeTax"]) for x in lines if x.get('ProductName') in STORAGE])
            cpu_cost = sum([float(x["CostBeforeTax"]) for x in lines if x.get('ProductName') in CPU])
            logging.info([bandwidth_cost, storage_cost, cpu_cost])

            # since the cost is only meaningful as a CPM, we calculate inventory for period in 
            # question and return the CPM
            beginning_of_month = end.replace(day=1)
            ads_for_period = self.ads_total(beginning_of_month, end)
            logging.info(ads_for_period)

            return ((bandwidth_cost + storage_cost + cpu_cost) / (ads_for_period / 1000.0), 
                bandwidth_cost / (ads_for_period / 1000.0), 
                storage_cost / (ads_for_period / 1000.0), 
                cpu_cost / (ads_for_period / 1000.0))
        else:
            logging.warn("Could not retrieve billing stats from AWS")
            return (0, 0, 0, 0)        
            
    def snippets(self, start):
        # room IDs can be obtained from HipChat
        API_KEY = "3ec795e1dd7781d59fb5b8731adef1"
        ROOMS = [("Client", 51581), 
                 ("AdServer", 57170),
                 ("Data", 81833), 
                 ("FE", 47652), 
                 ("MPX", 80467), 
                 ("Ops", 33343),
                 ("BD/AM", 93494),
                 ("JPStaff", 93728),
                 ("MoPub", 21565)] 
        date = start.strftime("%Y-%m-%d")
        
        # build snippets
        snippets = []
        
        # go through each room and pull statuses
        for room in ROOMS:
            url = "http://api.hipchat.com/v1/rooms/history?room_id=%d&date=%s&timezone=PST&format=json&auth_token=%s" % (room[1], date, API_KEY)
            logs = json.loads(urlfetch.fetch(url, deadline=30).content)
            for m in logs["messages"]:
                if "#standup" in m["message"] or "#snippet" in m["message"]:
                    snippets.append(("%s/%s" % (room[0], m["from"]["name"]), m["message"].replace("#standup", "").replace("#snippet", "").replace("@all", "").strip()))
        
        # return the snippet list
        return snippets
        
    def get(self):
        now = datetime.datetime.now() + datetime.timedelta(hours=-8)
        week = [now + datetime.timedelta(days=-7), now]
        month = [now + datetime.timedelta(days=-30), now]
        
        # total inventory
        request_count = (self.ads_total(now, now) / 1000000.0, 
            self.ads_total(week[0], week[1]) / 1000000000.0, 
            self.ads_total(month[0], month[1]) / 1000000000.0)

        # total spend
        total, a = self.mpx_total(now, now)
        mpx_spend = (total, 
            self.mpx_total(week[0], week[1])[0] / 1000.0, 
            self.mpx_total(month[0], month[1])[0] / 1000.0)
            
        # clear rate
        mpx_cleared = (self.mpx_cleared(now, now) / 1000000.0, 
            self.mpx_cleared(week[0], week[1]) / 1000000000.0, 
            self.mpx_cleared(month[0], month[1]) / 1000000000.0)
            
        # total cost 
        cost = self.cost_total(now)
        
        # snippets
        snippets = self.snippets(now)
            
        # cpm
        cpm = (mpx_spend[0] / request_count[0] / 1000.0, mpx_spend[1] / request_count[1] / 1000.0, mpx_spend[2] / request_count[2] / 1000.0)
        
        # compute body
        body = "Total Spend: $%.2f (7d: $%.1fK 30d: $%.1fK)\n" % mpx_spend
        body += "Total Inventory: %.1fMM (7d: %.1fB 30d: %.1fB)\n" % request_count
        body += "Clear Rate: %.1f%% (7d: %.1f%% 30d: %.1f%%)\n" % (100 * mpx_cleared[0] / request_count[0], 100 * mpx_cleared[1] / request_count[1], 100 * mpx_cleared[2] / request_count[2])
        body += "eCPM: $%.3f (7d: $%.3f 30d: $%.3f)\n" % cpm
        body += "COGS: $%.3f (bandwidth: $%.3f storage: $%.3f cpu: $%.3f)\n" % cost
        
        # bidders
        body += "\nTop Bidders\n===========\n"
        for x in a:
          body += "%s: $%.2f\n" % x
          
        # snippets 
        body += "\nSnippets\n========\n"
        for x in snippets:
          body += "%s: %s\n" % x

        body += "\nData retrieved at %s UTC. COGS computed on a month-to-date basis. Thank you - Automated John Chen" % time.strftime('%b %d %Y %H:%M:%S')
        
        # send mail
        logging.info(body)
        mail.send_mail(sender=SENDER, to="ft+reports@mopub.com", 
            subject="MPX Daily Spend Report for %s" % now.strftime('%b %d %Y'),
            body=body,
            html="<html><body><pre>%s</pre></body></html>" % body)


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/mail/daily', MpxReportHandler),
                                          ('/generate', GenerateHandler),
                                          ('/check/(.*)', CheckHandler),
                                          ('/check', CheckHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
