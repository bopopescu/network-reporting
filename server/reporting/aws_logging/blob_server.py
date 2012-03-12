#!/usr/bin/env python
import logging
import os
import sys
import time
import urllib


# add mopub root to path
sys.path.append(os.getcwd()+'/../../')

# for ubuntu EC2
sys.path.append('/home/ubuntu/mopub/server')
sys.path.append('/home/ubuntu/mopub/server/reporting')
sys.path.append('/home/ubuntu/google_appengine')
sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
sys.path.append('/home/ubuntu/google_appengine/lib/webob')
sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')

from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()

from google.appengine.ext import blobstore
from google.appengine.ext import webapp
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import taskqueue
from google.appengine.api import logservice

from reporting.aws_logging.stats_updater import parse_line as stats_updater_parse_line
from reporting.aws_logging.stats_updater import single_thread_put_models as stats_updater_put_models

from reporting.aws_logging.uniq_user_stats_updater import parse_line as uniq_user_stats_updater_parse_line
from reporting.aws_logging.uniq_user_stats_updater import single_thread_update_models as uniq_user_stats_updater_update_models


URL_HANDLER_PATH = '/offline/get_upload_url'
UPDATE_STATS_HANDLER_PATH = '/offline/update_stats'

    
class UrlHandler(webapp.RequestHandler):
    def get(self):
        upload_url = blobstore.create_upload_url('/offline/upload')
        format = self.request.get('format', None)
        if format == 'html':
            self.response.out.write(upload_url)
            self.response.out.write('<html><body>')
            self.response.out.write('<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url)
            self.response.out.write("""Upload File: <input type="file" name="file"><br> <input type="submit" 
                name="submit" value="Submit"> </form></body></html>""")
        else:
            self.response.out.write(upload_url)        
        

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        upload_files = self.get_uploads('file')  # 'file' is file upload field in the form
        blob_info = upload_files[0]
        self.response.out.write(blob_info.key())


class StatsWorker(webapp.RequestHandler):
    def get(self):
        start = time.time()
        
        blob_key = self.request.get('blob_key')
        blob_type = self.request.get('blob_type', 'log_counts')
        blob_reader = blobstore.BlobReader(blob_key)
        
        # using error to see it more easily in the GAE logs -- info or debug will get pushed out very quickly
        # using flush to see it in the logs immediately, since backends uses periodic logging by default
        logging.error('processing task: %s, %s' %(blob_key, blob_type))
        logservice.flush()
        
        if blob_type == 'log_counts':
            for line in blob_reader:
                stats_updater_parse_line(line)
            stats_updater_put_models()
            
            logging.error('log counts updates done')    
            logservice.flush()
        elif blob_type == 'uniq_user':
            for line in blob_reader:
                uniq_user_stats_updater_parse_line(line)
            uniq_user_stats_updater_update_models()       
            
            logging.error('uniq user updates done') 
            logservice.flush()
        else:
            logging.error('invalid blob type (accepts: "log_counts" or "uniq_user")')
            logservice.flush()
            
        elapsed = time.time() - start
        logging.error('updating GAE datastore with blob %s took %i minutes and %i seconds' % (blob_key, elapsed/60, elapsed%60))
        logservice.flush()

class ServeReportBlobHandler(blobstore_handlers.BlobstoreDownloadHandler):

    def get(self, report_blob_key):
        blob_key = str(urllib.unquote(report_blob_key))
        blob_info = blobstore.BlobInfo.get(blob_key)
        self.send_blob(blob_info, content_type='application/json')

class UpdateStatsHandler(webapp.RequestHandler):
    def get(self):
        blob_key = self.request.get('blob_key')
        blob_type = self.request.get('blob_type', 'log_counts')
        q = taskqueue.add(queue_name='stats-updater',
                      method='get',
                      url='/offline/worker', 
                      params={'blob_key': blob_key, 'blob_type': blob_type},
                      target='stats-updater')
        self.response.out.write('processing task for blob %s and type %s is added to task queue %s' % (blob_key, blob_type, q.name))
        
        

def main():
    application = webapp.WSGIApplication(
          [(URL_HANDLER_PATH, UrlHandler),
           ('/offline/upload', UploadHandler),
           ('/offline/reports/get_blob/(?P<report_blob_key>[-\w\.]+)/', ServeReportBlobHandler),
           ('/offline/worker', StatsWorker),
           (UPDATE_STATS_HANDLER_PATH, UpdateStatsHandler),
          ], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()