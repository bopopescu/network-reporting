import cPickle as pickle
import urllib

from google.appengine.ext import webapp
from google.appengine.api import urlfetch

from publisher.models import Site as AdUnit
from publisher.query_managers import AdUnitContextQueryManager

from adserver_constants import ADSERVER_ADMIN_HOSTNAME, USER_PUSH_URL

def adunitcontext_fetch(adunit_key, testing=False):
    # This is a service to the AWS/Tornado adserver.
    # We are not following the RequestHandler pattern here (simple function instead), because we do not want to require login.
    complex_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)
    simple_context = complex_context.simplify()
    basic_context = simple_context.to_basic_dict()
    pickled_context = pickle.dumps(basic_context)
    return pickled_context

class AUCFetchHandler(webapp.RequestHandler):

    def get(self, adunit_key):
        # This is a service to the AWS/Tornado adserver.
        # We are not following the RequestHandler pattern here (simple function instead), because we do not want to require login.
        return self.response.out.write(adunitcontext_fetch(adunit_key))


class AUCUserPushHandler(webapp.RequestHandler):

    def get(self):
        """ For the given adunit context key, push down the updated context 
        to ec2 """
        # Dont' handle errors because if there are errors the TQ will be readded
        rpc = urlfetch.create_rpc()
        adunit_key = self.request.get('adunit_key')
        adunit = Adunit.get(adunit_key)
        adunit_context = AdUnitContext.wrap(adunit)
        pickled_context = pickle.dumps(adunit_context.simplify().to_basic_dict())
        body = urllib.urlencode(dict(data = pickled_context))
        full_url = 'http://' + ADSERVER_ADMIN_HOSTNAME + USER_PUSH_URL
        # Make async call to the adserver_admin, don't really care about wtf it sends back
        urlfetch.make_fetch_call(rpc, url=full_url, payload=body, method=urlfetch.POST)
