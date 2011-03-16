import sys
import os

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append(os.environ['PWD'])


from advertiser.models import ( Campaign,
                                AdGroup,
                                Creative,
                                TextCreative,
                                TextAndTileCreative,
                                HtmlCreative,
                                ImageCreative,
                                )
from datetime import          ( datetime,
                                timedelta,
                                )
from google.appengine.ext.webapp import ( Request,
                                          Response,
                                          )
from nose.tools import assert_equal
from publisher.models import (  App,
                                Site
                                )
from random import random
from server.ad_server.main import  ( AdHandler,
                                     AdAuction,
                                     AdClickHandler,
                                     AppOpenHandler,
                                     TestHandler,
                                     )

from server.ad_server.filters.filters import ll_dist

from time import mktime

import logging

AdUnit = Site

AD_UNIT_ID = "agltb3B1Yi1pbmNyCgsSBFNpdGUYAgw"
UDID = "thisisntrealatall"

test_mode = "3uoijg2349ic(test_mode)kdkdkg58gjslaf"
TEST_LLS = ["42.3584308,-71.0597732","40.7607794,-111.8910474","40.7142691,-74.0059729","38.3565773,-121.9877444","39.1637984,-119.7674034","34.0522342,-118.2436849","36.1749705,-115.137223"] 

NETWORKS = ( u'iad', u'admob', u'adsense' )
PROMOS = ( u'test1', u'test2' )
GTEES = ( u'testbudget1', u'testbudget2')

def fake_environ( query_string, method = 'get' ):
    ret = dict(    REQUEST_METHOD = method,
                    QUERY_STRING   = query_string,
                    HTTP_USER_AGENT = 'truck',
                    SERVER_NAME = 'localhost',
                    SERVER_PORT = 8000,
                    )
    ret[ 'wsgi.version' ] = (1, 0)
    ret[ 'wsgi.url_scheme' ] = 'http'
    return ret

def build_ad_qs( udid, keys, ad_id, v = 3, dt = datetime.now(), ll=None):
    dt = process_time( dt )
    basic_str = "v=%s&udid=%s&q=%s&id=%s&testing=%s&dt=%s" % ( v, udid, keys, ad_id, test_mode , dt )
    if ll is not None:
        basic_str += '&ll=%s' % ll
    return basic_str

def process_time( dt ):
    return mktime( dt.timetuple() ) 

def add_time( dt, **kw ):
    return dt + make_delta( **kw )

def make_delta( **kw ):
    if kw.has_key( 'days' ):
        return timedelta( days = kw[ 'days' ] )
    if kw.has_key( 'hours' ):
        return timedelta( hours = kw[ 'hours' ] )

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
    for adgroup in camp.adgroups:
        adgroup.bid = ecpm
        adgroup.put()


def prioritize( c_name ):
    for c in Campaign.all():
        if c.name == c_name:
           set_ecpm( c , float( 100 ) )

def de_prioritize( c_name ):
    for c in Campaign.all():
        if c.name == c_name:
            set_ecpm( c )

def de_prioritize_all():
    for c in Campaign.all():
        set_ecpm( c )

def set_freq( c_name, count, type = 'daily' ):
    assert type in ('daily', 'hourly' ), "Expected daily or hourly frequency, request frequency was %s" % type 
    for c in Campaign.all():
        if c.name == c_name:
            ag = c.adgroups[0]
            if type == 'daily':
                ag.daily_frequency_cap = count
                ag.put()
            elif type == 'hourly':
                ag.hourly_frequency_cap = count
                ag.put()
            else:
                print ":("

def zero_all_freqs():
    for c in Campaign.all():
        for t in ( 'daily', 'hourly' ):
            set_freq( c.name, 0, type = t )


def get_id( dt = datetime.now(), ll=None ):
    resp = Response()
    req = Request( fake_environ( build_ad_qs( UDID, '', AD_UNIT_ID, dt = dt, ll=ll) ) )
    adH = AdHandler()
    adH.initialize( req, resp )
    adH.get()
    return resp.headers.get('X-Creativeid')

def basic_net_test():
    pause_all()
    de_prioritize_all()
    for c in NETWORKS: 
        resume( c ) 
        id = get_id()
        print "id is: %s" % id
        cret = Creative.get( id ) 
        assert_equal( cret.ad_group.name, c, "Expected %s, got %s" % ( c, cret.ad_group.name ) )
        pause( c )

def basic_promo_test():
    pause_all()
    for c in PROMOS: 
        resume( c )
        for i in range( 3 ):
            camp = Creative.get( get_id() )
            t = camp.ad_group.name
            assert_equal( camp.ad_group.name, c, "Expected %s, got %s" % ( c, camp.ad_group.name ) )
        pause( c )

def priority_level_test():
    pause_all()
    de_prioritize_all()
    for a in PROMOS:
        resume(a)
    for a in NETWORKS:
        resume(a)
        prioritize(a)
    for i in range(100):
        camp = Creative.get(get_id())
        t = camp.ad_group.name
        assert t in PROMOS, "Expected promo, got %s" % t
    for a in PROMOS:
        pause(a)
    for i in range(20):
        camp = Creative.get(get_id())
        assert camp.ad_group.name in NETWORKS, "Expected network, got %s" % camp.ad_group.name
    de_prioritize_all()

def net_priorty_test():
    priority_t3st( NETWORKS ) 
    return 

def priority_t3st( camps ):
    for c in camps: 
        resume( c )
    for c in camps: 
        prioritize( c )
        for i in range( 5 ):
            k = get_id()
            cret = Creative.get( k ) 
            assert_equal( cret.ad_group.name, c, "Expected %s, got %s" % ( c, cret.ad_group.name ) )

        pause( c )
        print c
        for i in range( 5 ):
            cret = Creative.get( get_id() )
            assert cret.ad_group.name != c, "Expected NOT %s, got %s" % ( c, cret.ad_group.name )
        resume( c )
        de_prioritize( c )
    return

#def set_freq( c_name, count, type = 'daily' ):

#def add_time( dt, **kw ):
def basic_freq( c, def_freq, dt = datetime.now() ):
    for i in range( def_freq ):
        cret = Creative.get( get_id( dt ) )
        assert_equal( cret.ad_group.name, c, "Expected %s, got %s" % ( c, cret.ad_group.name ) )
    over_cap = get_id( dt ) 
    assert over_cap is None, "Expected none, got %s" % Creative.get( over_cap )
    return

def frequency_t3st( camps, def_freq = 5 ):
    #all frequency testing happens in the fuuuttttuuureeee (whoaaaaaa)
    s_time = datetime.now()
    s_time = add_time( s_time, days = 1 )
    #hourly
    for c in camps:
        #start the campaign and set its hourly frequency
        resume( c )
        set_freq( c, def_freq, 'hourly' )

        #run the test
        basic_freq( c, def_freq, s_time )

        #change the time
        the_time = add_time( s_time, hours = 3 )
        #run it again
        basic_freq( c, def_freq, the_time )
        
        #unset the minute thing & turn off
        set_freq( c, 0, 'hourly' )
        pause( c )
    
    #already been 10 impr for the day, so set the start_day for all
    #the daily tests to be three days from today
    s_time = add_time( s_time, days = 3 )

    #daily (same as above)
    for c in camps:
        resume( c )
        set_freq( c, def_freq, 'daily' )
        basic_freq( c, def_freq, s_time )
        the_time = datetime.now()
        the_time = add_time( the_time, days = 5 )
        basic_freq( c, def_freq, the_time )
        set_freq( c, 0, 'daily' )
        pause( c )

def net_freq_test():
    pause_all()
    zero_all_freqs()
    frequency_t3st( NETWORKS )
    


def promo_freq_test():
    pause_all()
    zero_all_freqs()
    frequency_t3st( PROMOS )

def comb_freq_test():
    pass

def lat_lon_test():
    pause_all()
    for c in PROMOS:
        resume(c)
    #prioritize test2 to show before everything else
    #BUT test2 is city constrained!
    prioritize(u'test2')
    for i in range(100):
        #iterate over all cities
        for ll in TEST_LLS:
            #pick a random city
            ll = [float(val) for val in ll.split(',')]
            #and slowly move away from it
            e = gen_ll(ll, i)
            f = str(e[0])+','+str(e[1])
            creat = Creative.get(get_id(ll=f))
            name = creat.ad_group.name
            #if we're close, we should get test2 (higher priority)
            tf_gen = (ll_dist(e, (float(lat), float(lng))) < 50 for (lat, lng) in (a.split(',') for a in TEST_LLS))
            for tf in tf_gen:
                if tf: 
                    assert_equal(name, u'test2', 'Expected city-constrained promo, got %s' % name)
                    #Break so else clause doesn't execute
                    break
            #otherwise, we should get the lower priority, unconstraned adgroup
            else:
                assert_equal(name, u'test1', 'Expected non-city-constrained promo (dist is %s), got %s' % (ll_dist(e,ll), name)) 




def gen_ll(ll, i):
    ret = [ll[0] + i * .05, ll[1] + i * .05] 
    return ret 
