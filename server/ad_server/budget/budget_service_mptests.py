from nose.tools import eq_
from nose.tools import with_setup
from server.ad_server.budget import budget_service

# We simplify budget_service for testing purposes
budget_service.TEST_MODE = True
budget_service.TIMESLICES = 2 

def init_test_campaign(campaign_id, daily_budget, fudge_factor=0, timeslices=1):
    """ Make a fake campaign """
    budget_service.test_timeslice = 0
    budget_service.test_daily_budget = daily_budget
    
    # process an empty bid to initialize values
    budget_service.process(campaign_id,0)


def mptest_to_memcache_int():
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
    init_test_campaign(0,1000) #each ts has a budget of 500
    eq_(budget_service.current_timeslice(), 0)
    eq_(budget_service.get_timeslice_budget(0),500)

def mptest_budget_all_at_once():
    init_test_campaign(1,1000) #each ts has a budget of 500
    eq_(budget_service.get_timeslice_budget(1),500)
    eq_(budget_service.process(1,300),True)
    eq_(budget_service.get_timeslice_budget(1),200)
    eq_(budget_service.process(1,300),False)
    eq_(budget_service.get_timeslice_budget(1),200)

def mptest_budget_evenly_success():
    init_test_campaign(2,500) #each ts has a budget of 250
    eq_(budget_service.get_timeslice_budget(2),250)
    eq_(budget_service.process(2,125),True)
    eq_(budget_service.get_timeslice_budget(2),125)
    eq_(budget_service.process(2,125),True)
    eq_(budget_service.get_timeslice_budget(2),0)
    eq_(budget_service.process(2,125),False)

  
def mptest_budget_evenly_failure():
    init_test_campaign(3,500) #each ts has a budget of 250
    eq_(budget_service.process(3,300),False)
    eq_(budget_service.get_timeslice_budget(3),250)
    eq_(budget_service.process(3,300),False)
    eq_(budget_service.get_timeslice_budget(3),250)

def mptest_multiple_timeslices():
    init_test_campaign(4,2.4) #each ts is 1.2
    eq_(budget_service.get_timeslice_budget(4),1.2)
    eq_(budget_service.process(4,1.1),True)
    eq_(budget_service.get_timeslice_budget(4),0.1)
    eq_(budget_service.process(4,1.3),False)
    
    budget_service.test_timeslice += 1
    
    eq_(budget_service.process(4,1.1),True)
    eq_(budget_service.get_timeslice_budget(4),0.2)
 
def mptest_multiple_timeslice_rollover():
    init_test_campaign(5,200) #each ts has a budget of 100

    budget_service.test_timeslice += 1
    
    eq_(budget_service.process(5,100),True)
    eq_(budget_service.get_timeslice_budget(5),100)
    eq_(budget_service.process(5,100),True)
    eq_(budget_service.process(5,100),False)