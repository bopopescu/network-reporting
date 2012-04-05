#!/usr/bin/env python
#
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.api import mail, urlfetch
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
    def post(self):
        # fire off reporting API request
        m = int(self.request.get('m'))
        y = int(self.request.get('y'))
        q = 'http://xyz/q?start=%d%02d%02d&end=%d%02d%02d' % (y, m, 1, y, m, calendar.monthrange(y, m)[1])
        
        # play robot movie
        self.response.out.write(
            """<html><head>
                    <script type='text/javascript' src='/images/jwplayer.js'></script>
                </head>
                <body align='center'>
                    <h1>Automated John Chen<br/>Is Generating Your Report... %s</h1>
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
               </html>""" % q)
               
class LogSenderHandler(InboundMailHandler):
    def receive(self, message):
        logging.info("Received a message from: " + message.sender)
        
        url = message.subject
        logging.info("Would fetch log from %s" % url)
        
        # download the report and resend as an attachment
        x = urlfetch.fetch(url)

        # create outbound email
        mail.send_mail(sender="Automated John Chen <johnchen@mopub.com>",
                          to="johnchen@mopub.com",
                          subject="Your report from %s" % message.date,
                          body="""Sir- Good times, as requested. Sincerely, Automated John Chen""",
                          attachments=[("report.csv", x.content)])
        

def main():
    application = webapp.WSGIApplication([('/', MainHandler), 
                                          ('/generate', GenerateHandler), 
                                          LogSenderHandler.mapping()],
                                         debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
