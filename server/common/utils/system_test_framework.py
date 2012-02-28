
from appengine_django import LoadDjango
LoadDjango()

import os
from django.conf import settings

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# Force Django to reload its settings.
settings._target = None



from advertiser.models import (Campaign,
                                AdGroup,
                                Creative,
                               )
                               
from datetime import          (datetime,
                               timedelta,
                               )
from google.appengine.ext.webapp import (Request,
                                         Response,
                                         )
from ad_server.main import  (AdImpressionHandler,
                                     AdClickHandler,
                                     AppOpenHandler,
                                    )
from ad_server.handlers.adhandler import AdHandler  

from time import mktime
import logging
from google.appengine.ext.db import Key
""" 
This serves as the end-to-end framework for ad_server tests.
"""

UDID = "fakeudid"
TEST_MODE = "3uoijg2349ic(TEST_MODE)kdkdkg58gjslaf"

def _fake_environ(query_string, method = 'get'):
    ret = dict(   REQUEST_METHOD = method,
                    QUERY_STRING   = query_string,
                    HTTP_USER_AGENT = 'FakeAndroidOS',
                    SERVER_NAME = 'localhost',
                    SERVER_PORT = 8000,
                   )
    ret[ 'wsgi.version' ] = (1, 0)
    ret[ 'wsgi.url_scheme' ] = 'http'
    return ret

def _build_ad_querystring(udid, keys, ad_id, v = 3, dt = datetime.now(), ll=None):
    time_string = mktime(dt.timetuple()) 
    basic_str = "v=%s&udid=%s&q=%s&id=%s&testing=%s&dt=%s" % (v, udid, keys, ad_id, TEST_MODE , time_string)
    if ll is not None:
        basic_str += '&ll=%s' % ll
    return basic_str

def fake_request(adunit_key, dt=datetime.now(), ll=None):
    return Request(_fake_environ(_build_ad_querystring(UDID, '', str(adunit_key), dt=dt, ll=ll)))

def run_auction(adunit_key, 
                simulate_client_success=True, 
                
                dt = datetime.now(), 
                ll=None):
    """For use by other tests. Takes an adunit_key and returns the
    creative that won the CPM battle, if success = True, also simulates client callback"""
    
    resp = Response()
    req = fake_request(adunit_key, dt=dt, ll=ll)
    ad_handler = AdHandler()
    ad_handler.initialize(req, resp)
    ad_handler.get()
        
    # Pull data from ad_auction response
    creative_id = resp.headers.get('X-Creativeid')
    imp_tracker_url = resp.headers.get('X-Imptracker')
    clickthrough_url = resp.headers.get('X-Clickthrough')
    
    # Get the creative
    logging.warning("best creative: %s" % creative_id)
    if creative_id is None:
        return None
    creative = Creative.get(Key(creative_id))
    
    if simulate_client_success:
        # Simulate callback to impression handler
        # get rid of prepended "html://DOMAIN"
        query_string = imp_tracker_url.split('?')[1] + "&testing=%s" % TEST_MODE
        logging.warning("query string: %s" % query_string)
        req = Request(_fake_environ(query_string))
        resp = Response()
        imp_handler = AdImpressionHandler()
        imp_handler.initialize(req, resp)
        imp_handler.get()
        
        # Simulate callback to click handler
        # get rid of prepended "html://DOMAIN"
        query_string = '/m/' + clickthrough_url.split('/m/')[1] + "&testing=%s" % TEST_MODE
        logging.warning("query string: %s" % query_string)
        req = Request(_fake_environ(query_string))
        resp = Response()
        click_handler = AdClickHandler()
        click_handler.initialize(req, resp)
        click_handler.get()
    return creative
    
def simulate_impression(creative):
    # /m/imp?id=agltb3B1Yi1pbmNyDAsSBFNpdGUY1NsgDA&cid=agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGJvEIAw&udid=4863585ad8c80749
    raise NotImplementedError
    
    
 
