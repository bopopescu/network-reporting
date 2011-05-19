from google.appengine.api import memcache
from google.appengine.ext import webapp

""" We use this to remove or flush things from memcache"""

class ClearHandler(webapp.RequestHandler):
    """examples:
        http://app.mopub.com/m/clear?key=daily_budget:agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPaS9AEM&namespace=budget
        http://app.mopub.com/m/clear?key=flush
        """
    
    def get(self):
        key = self.request.get("key")
        namespace = self.request.get("namespace") or None
        if key is "flush":
            self.response.out.write(memcache.flush_all())
        else:
            self.response.out.write(memcache.delete(key, namespace=namespace))