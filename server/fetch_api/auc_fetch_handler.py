import cPickle as pickle

from google.appengine.ext import webapp

from publisher.query_managers import AdUnitContextQueryManager

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

