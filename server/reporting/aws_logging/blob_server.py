#!/usr/bin/env python
import os
import sys
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

from reporting.aws_logging import stats_updater 
from reporting.aws_logging import uniq_user_stats_updater


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
        # self.redirect('/offline/serve/%s' % blob_info.key())


class ServeHandler(blobstore_handlers.BlobstoreDownloadHandler):
    def get(self, resource):
        resource = str(urllib.unquote(resource))
        blob_info = blobstore.BlobInfo.get(resource)
        self.send_blob(blob_info)


class UpdateStatsHandler(webapp.RequestHandler):
    def get(self):
        blob_key = self.request.get('blob_key')
        blob_type = self.request.get('type', 'log_counts')
        blob_reader = blobstore.BlobReader(blob_key)
        
        if blob_type == 'log_counts':
            for line in blob_reader:
                stats_updater.parse_line(line)
            stats_updater.put_models()        
            self.response.out.write('log counts updates done')
        elif blob_type == 'uniq_user':
            for line in blob_reader:
                uniq_user_stats_updater.parse_line(line)
            uniq_user_stats_updater.update_models()        
            self.response.out.write('uniq user updates done')
        else:
            self.response.out.write('invalid blob type (accepts: "log_counts" or "uniq_user")')


def main():
    application = webapp.WSGIApplication(
          [(URL_HANDLER_PATH, UrlHandler),
           ('/offline/upload', UploadHandler),
           ('/offline/serve/([^/]+)?', ServeHandler),
           (UPDATE_STATS_HANDLER_PATH, UpdateStatsHandler),
          ], debug=True)
    run_wsgi_app(application)


if __name__ == '__main__':
    main()