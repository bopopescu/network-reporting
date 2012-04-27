import cPickle as pickle
import logging
import urllib
from datetime import datetime
import time

from google.appengine.ext import webapp
from google.appengine.api import urlfetch, taskqueue

from publisher.models import Site as AdUnit
from publisher.query_managers import AdUnitContextQueryManager

from adserver_constants import ADSERVER_ADMIN_HOSTNAME, USER_PUSH_URL

def adunitcontext_fetch(adunit_key, created_at=None, testing=False):
    # This is a service to the AWS/Tornado adserver.
    # We are not following the RequestHandler pattern here (simple function instead), because we do not want to require login.
    complex_context = AdUnitContextQueryManager.cache_get_or_insert(adunit_key)
    now = int(time.mktime(datetime.utcnow().timetuple()))
    context_created_at = getattr(complex_context, 'created_at', now)
    if created_at == context_created_at and created_at != 0:
        return None
    simple_context = complex_context.simplify()
    basic_context = simple_context.to_basic_dict()
    pickled_context = pickle.dumps(basic_context)
    return pickled_context

class AUCFetchHandler(webapp.RequestHandler):

    def get(self, adunit_key):
        created_at = self.request.get('created_at', 0)
        # This is a service to the AWS/Tornado adserver.
        # We are not following the RequestHandler pattern here (simple function instead), because we do not want to require login.
        created_at = int(float(created_at))
        data_package = adunitcontext_fetch(adunit_key, created_at=created_at)
        if data_package:
            return self.response.out.write(data_package)
        else:
            return self.response.out.write("EMPTY")


class AUCUserPushHandler(webapp.RequestHandler):

    def get(self):
        """ For the given adunit context key, push down the updated context 
        to ec2 """
        # Dont' handle errors because if there are errors the TQ will be readded
        rpc = urlfetch.create_rpc()
        adunit_key = self.request.get('adunit_key')
        adunit_context = AdUnitContextQueryManager.get_context(adunit_key)
        pickled_context = pickle.dumps(adunit_context.simplify().to_basic_dict())
        body = urllib.urlencode(dict(data = pickled_context))
        full_url = 'http://' + ADSERVER_ADMIN_HOSTNAME + USER_PUSH_URL
        # Make async call to the adserver_admin, don't really care about wtf it sends back
        urlfetch.make_fetch_call(rpc, url=full_url, payload=body, method=urlfetch.POST)


class AUCUserPushFanOutHandler(webapp.RequestHandler):

    def post(self):
        inttime = int(time.time())
        ts = inttime / 60
        eta = (ts + 1)* 60
        eta += 5
        countdown = eta - inttime
        queue = taskqueue.Queue('push-context-update')
        adunit_keys = self.request.get_all('adunit_keys')
        for key in adunit_keys:
            task_name = 'adunit-%s-ts-%s' % (key, ts)
            task = taskqueue.Task(url='/fetch_api/adunit_update_push',
                                  name=task_name,
                                  method='GET',
                                  countdown=countdown,
                                  params={'adunit_key':key})
            try:
                queue.add(task)
            except taskqueue.BadTaskStateError, e:
                logging.warning("%s already exists" % task)
            except taskqueue.DuplicateTaskNameError, e:
                logging.warning("%s already exists" % task)
            except taskqueue.TaskAlreadyExistsError, e:
                logging.warning("%s already exists" % task)


