#!/usr/bin/env python
#
#
from google.appengine.ext import webapp
from google.appengine.ext import deferred
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.api import mail, urlfetch, taskqueue
import logging, email
import datetime, time, calendar 

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
    def _initiate_map_reduce(self, m, y):
        # TODO: XS please complete this... 
        q = 'http://www.google.com/q?start=%d%02d%02d&end=%d%02d%02d' % (y, m, 1, y, m, calendar.monthrange(y, m)[1])
        return "ABC123"
        
    def post(self):
        # fire off reporting API request
        m = int(self.request.get('m'))
        y = int(self.request.get('y'))
        jobId = self._initiate_map_reduce(m, y)
        
        # initiates a task queue item that checks to see if this job has completed
        taskqueue.add(url="/check", params={"id": jobId}, queue_name='jobcheck', countdown=60)
        
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
        # TODO -- XS please complete this
        return False
        
    # Returns S3 directory if the job has completed successfully 
    # or None if the job failed 
    def _get_job_output(self, jobId):
        # TODO -- XS please complete this 
        return "http://www.google.com"
        
    # Checks the S3 job - notifies user on failure
    # handles completed jobs by defering into a task q for later 
    def post(self):
        jobId = self.request.get('id')
        if self._is_job_complete(jobId): 
            s3_dir = self._get_job_output(jobId)
            if s3_dir:
                # OK go iterate through this directory
                self.collect_job_output(jobId, s3_dir)
                return
            else:
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
        x = urlfetch.fetch(s3_dir)

        # create outbound email
        mail.send_mail(sender="Automated John Chen <johnchen@mopub.com>",
                          to="jim@mopub.com",
                          subject="SUCCESS: Your report with ID %s" % jobId,
                          body="""Sir- Good times, as requested. Sincerely, Automated John Chen""",
                          attachments=[("%s.csv" % jobId, x.content)])
        

def main():
    application = webapp.WSGIApplication([('/', MainHandler), 
                                          ('/generate', GenerateHandler), 
                                          ('/check', CheckHandler)],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
