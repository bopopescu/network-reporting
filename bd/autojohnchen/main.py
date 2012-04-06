#!/usr/bin/env python
#
#
import logging, email
import datetime, time, calendar

from google.appengine.ext import webapp
from google.appengine.ext import deferred
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail, urlfetch, taskqueue

from hive_job_launcher import launch_monthly_mpx_rev_hivejob, get_jobflow_state, get_output_data


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
                        <select name='y'><option>2011</option><option selected>2012</option><option>2013</option></select>
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
        taskqueue.add(url="/check", params={"id": jobId, "s3_dir": s3_dir}, queue_name='jobcheck', countdown=60)

        # play robot movie for user
        self.response.out.write(
            """<html><head>
                    <script type='text/javascript' src='/images/jwplayer.js'></script>
                </head>
                <body align='center'>
                    <h1>Automated John Chen<br/>Is Generating Your Report... Job ID is %s</h1>
                    <!--center><p id="mediaplayer"></p></center-->
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
                </body>
               </html>""" % jobId)

class CheckHandler(webapp.RequestHandler):
    # Returns True if the job has completed, False if still running
    def _is_job_complete(self, jobId):
        state = get_jobflow_state(jobId)
        logging.info('%s\tjob %s state: %s' % (time.strftime('%b %d %Y %H:%M:%S'), jobId, state))
        if state == ['COMPLETED', 'WAITING']:
          return True, True   # done and successful
        if state in ['FAILED', 'TERMINATED']:
          return True, False  # done but failed
        return False, False   # still running

    # Checks the S3 job - notifies user on failure
    # handles completed jobs by defering into a task q for later
    def post(self):
        jobId = self.request.get('id')
        s3_dir = self.request.get('s3_dir')
        done, successful = self._is_job_complete(jobId)

        if done and successful:
            # OK go iterate through this directory
            self.collect_job_output(jobId, s3_dir)
            return
        elif done and not successful:
            # This failed so we send a note indicating failure
            mail.send_mail(sender="Automated John Chen <johnchen@mopub.com>",
                              to="johnchen@mopub.com",
                              subject="FAILED: Your report from %s could not be completed" % message.date,
                              body="""Sir- Sorry, I couldn't get it done. Apologies, Automated John Chen""")
        else:
            # Not complete yet so we fail this task and retry
            logging.info("JobID %s is not ready, retrying" % jobId)
            raise Exception("job not ready - retrying")

    def collect_job_output(self, jobId, s3_dir):
        logging.info(s3_dir)

        # grab the results
        content = get_output_data(s3_dir)

        # create outbound email
        mail.send_mail(sender="Automated John Chen <johnchen@mopub.com>",
                          to="jim@mopub.com",
                          subject="SUCCESS: Your report with ID %s" % jobId,
                          body="""Sir- Good times, as requested. Sincerely, Automated John Chen""",
                          attachments=[("%s.tsv" % jobId, content)])


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/generate', GenerateHandler),
                                          ('/check', CheckHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
