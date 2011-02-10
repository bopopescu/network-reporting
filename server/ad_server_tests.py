import sys

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append('/Users/f34r/mopub/server')


from server.ad_server.main import  ( AdHandler,
                                     AdAuction,
                                     AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )
from publisher.models import (  App,
                                Site
                                )

from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                TextCreative,
                                TextAndTileCreative,
                                HtmlCreative,
                                ImageCreative,
                                )

import logging

AdUnit = Site

from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )
AD_UNIT_ID = "agltb3B1Yi1pbmNyCgsSBFNpdGUYAgw" 
UDID = "thisisntrealatall"


test_mode = "3uoijg2349ic(test_mode)kdkdkg58gjslaf"

def fake_environ( query_string, method = 'get' ):
    return dict(    REQUEST_METHOD = method,
                    QUERY_STRING   = query_string,
                    HTTP_USER_AGENT = 'truck',
                    )

def build_ad_qs( udid, keys, ad_id, v = 3 ):
    return "v=%s&udid=%s&q=%s&id=%s&testing=%s" % (v, udid, keys, ad_id, test_mode)

def pause_all():
    for c in Campaign.all():
        c.active = False
        c.put()

def change_status( camp, stat ):
    for c in Campaign.all():
        if c.name == camp:
            c.active = stat
            c.put()

def resume( c_name ):
    change_status( c_name, True )

def pause( c_name ):
    change_status( c_name, False )

def set_ecpm( camp, ecpm= float( 1 ) ):
    adgroup = camp.adgroups[0]
    adgroup.bid = ecpm
    adgroup.put()


def prioritize( c_name ):
    for c in Campaign.all():
        if c.name == c_name:
           set_ecpm( c , float( 100 ) )

def de_prioritize( c_name ):
    for c in Campaign.all():
        if c.name == c_name:
            set_ecm( c )

def de_prioritize_all():
    for c in Campaign.all():
        set_ecpm( c )

def get_id():
    resp = Response()
    req = Request( fake_environ( build_ad_qs( UDID, '', AD_UNIT_ID ) ) )
    adH = AdHandler()
    adH.initialize( req, resp )
    return adH.get()


def faux_test():
    pause_all()
    de_prioritize_all()
    for c in ('iad', 'admob', 'adsense'):
        resume( c ) 
        k = get_id() 
        print k
        pause( c )

#    for c in ( 'test1', 'test2' ):
#        resume( c )
#        resp = Response()
#        req  = Request( fake_environ( build_ad_qs( UDID, '', AD_UNIT_ID ) ) )
#        adH = AdHandler()
#        adH.initialize( req, resp )
#        for i in range( 3 ):
#            k = adH.get()
#            print k
#        pause( c )

    for c in ( 'iad', 'admob', 'adsense' ):
        resume( c )
    for c in ( 'iad', 'admob', 'adsense' ):
        prioritize( c )
        k = get_id()
        print k
        de_prioritize( c )
        

    assert False



