from google.appengine.api import memcache
from google.appengine.ext import webapp

""" We use this to remove or flush things from memcache"""

class ClearHandler(webapp.RequestHandler):
    """ examples:
        http://app.mopub.com/m/memclear?key=daily_budget:agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPaS9AEM&namespace=budget
        http://app.mopub.com/m/memclear?key=flush
        """
    
    def get(self):
        key = self.request.get("key")
        namespace = self.request.get("namespace") or None
        if key is "flush":
            memcache.flush_all()
            self.response.out.write("Memcache has been flushed")
        else:
            deleted = memcache.delete(key, namespace=namespace)
            if deleted == 2:
                output = "Success"
            elif deleted == 1:
                output = "Failed, Entry did not exist"
            self.response.out.write(output)
            
            
            
class ShowHandler(webapp.RequestHandler):
    """ examples:
        http://app.mopub.com/m/memshow?key=daily_budget:agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPaS9AEM&namespace=budget
        
        http://app.mopub.com/m/memshow?key=context:agltb3B1Yi1pbmNyEQsSCENhbXBhaWduGPaS9AEM&namespace=context
        
        """

    def get(self):
        key = self.request.get("key")
        key = str(key).replace("'","")
        namespace = self.request.get("namespace") or None

        output = memcache.get(key, namespace=namespace)
        self.response.out.write(output)



