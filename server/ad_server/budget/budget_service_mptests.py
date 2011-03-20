from nose.tools import eq_
from nose.tools import with_setup
from server.ad_server.budget import budget_service
from google.appengine.api import memcache

# We simplify budget_service for testing purposes
budget_service.TEST_MODE = True
budget_service.TIMESLICES = 2 
budget_service.FUDGE_FACTOR = 0.0

def setup():
    """ simply resets the test values """
    budget_service.test_timeslice = 0


def mptest_to_memcache_int():
    setup()
    val = 123.00
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)

    val = 1
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)
    
    val = 15000000
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)

def mptest_get_budget():
    setup()
    budget_service.process(0, 0, 1000) #each ts has a budget of 500
    eq_(budget_service.get_current_timeslice(), 0)
    eq_(budget_service.get_timeslice_budget(0),500)

def mptest_budget_all_at_once():
    setup()
    budget_service.process(1, 0, 1000) #each ts has a budget of 500
    eq_(budget_service.get_timeslice_budget(1),500)
    eq_(budget_service.process(1,300,1000),True)
    eq_(budget_service.get_timeslice_budget(1),200)
    eq_(budget_service.process(1,300,1000),False)
    eq_(budget_service.get_timeslice_budget(1),200)

def mptest_budget_evenly_success():
    setup()
    budget_service.process(2, 0, 500) #each ts has a budget of 250
    eq_(budget_service.get_timeslice_budget(2),250)
    eq_(budget_service.process(2,125,500),True)
    eq_(budget_service.get_timeslice_budget(2),125)
    eq_(budget_service.process(2,125,500),True)
    eq_(budget_service.get_timeslice_budget(2),0)
    eq_(budget_service.process(2,125,500),False)

  
def mptest_budget_evenly_failure():
    setup()
    budget_service.process(3, 0, 500) #each ts has a budget of 250
    eq_(budget_service.process(3,300,500),False)
    eq_(budget_service.get_timeslice_budget(3),250)
    eq_(budget_service.process(3,300,500),False)
    eq_(budget_service.get_timeslice_budget(3),250)

def mptest_multiple_timeslices():
    setup()
    budget_service.process(4, 0, 2.4) #each ts is 1.2
    eq_(budget_service.get_timeslice_budget(4),1.2)
    eq_(budget_service.process(4,1.1,2.4),True)
    eq_(budget_service.get_timeslice_budget(4),0.1)
    eq_(budget_service.process(4,1.3,2.4),False)
    
    budget_service.test_timeslice += 1
    
    eq_(budget_service.process(4,1.1,2.4),True)
    eq_(budget_service.get_timeslice_budget(4),0.2)
 
def mptest_multiple_timeslice_rollover():
    setup()
    budget_service.process(5, 0, 200) #each ts has a budget of 100

    budget_service.test_timeslice += 1
    
    eq_(budget_service.process(5,100,200),True)
    eq_(budget_service.get_timeslice_budget(5),100)
    eq_(budget_service.process(5,100,200),True)
    eq_(budget_service.process(5,100,200),False)
   
def mptest_cache_failure():
    setup()
    budget_service.process(6, 0, 200) #each ts has a budget of 100
    
    budget_service.process(6, 10, 200)
    budget_service.process(6, 10, 200)
    budget_service.process(6, 10, 200)
    budget_service.process(6, 10, 200)
    budget_service.process(6, 10, 200)
    eq_(budget_service.get_timeslice_budget(6),50)
    
    #delete the count from memcache
    current_key = budget_service.make_campaign_ts_budget_key(6,budget_service.test_timeslice)
    memcache.delete(current_key, namespace="budget")

    #the next process request puts it back
    budget_service.process(6, 10, 200)
    eq_(budget_service.get_timeslice_budget(6),90)
    
def mptest_fudge_factor():
    setup()
    budget_service.FUDGE_FACTOR = 0.1
    budget_service.process(7, 0, 1000) #each ts has a budget of 500 + 50 fudge factor
    eq_(budget_service.get_timeslice_budget(7),550)
