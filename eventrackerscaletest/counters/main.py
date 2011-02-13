from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import memcache
from google.appengine.ext import db

from counters.models import Counter


class TestHandler(webapp.RequestHandler):
    def get(self):
        # self.response.out.write('THESE ARE THE COUNTERS')
        key = self.request.get('key')
        value = memcache.get(key)
        
        flush = bool(int(self.request.get('flush','0')))
        if flush:
            memcache_flush_success = memcache.flush_all()
            db_flush_success = db.delete(Counter.all())
            self.response.out.write("memcache: %s db: %s"%(memcache_flush_success,db_flush_success))
        else:
            self.response.out.write(value)
        

application = webapp.WSGIApplication([('/counter/test', TestHandler),
                                     ],
                                     debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()