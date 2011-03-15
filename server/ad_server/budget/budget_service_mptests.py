from nose.tools import eq_
from nose.tools import with_setup
from server.ad_server.budget import budget_service

def mptest_memcache_int():
    val = 123.00
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)

    val = 1
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)
    
    val = 15000000
    same = budget_service.to_memcache_int(budget_service.from_memcache_int(val))
    eq_(val,same)

def mptest_budget_all_at_once():
    budget_service = BudgetService(1,500,300,timeslices=1)
    eq_(budget_service.process(),True)
    eq_(budget_service.process(),False)

def mptest_budget_evenly_success():
    budget_service = BudgetService(2,250,115,timeslices=1,test_mode=True)
    eq_(budget_service._get_timeslice_slots(),2)
    eq_(budget_service.process(),True)
    eq_(budget_service._get_timeslice_slots(),1)
    eq_(budget_service.process(),True)
    eq_(budget_service._get_timeslice_slots(),0)
    eq_(budget_service.process(),False)

  
def mptest_budget_evenly_failure():
    budget_service = BudgetService(3,500,300,timeslices=2,test_mode=True)
    eq_(budget_service.process(),False)
    eq_(budget_service._get_timeslice_slots(),0)
    eq_(budget_service.process(),False)

def mptest_multiple_timeslices():
    budget_service = BudgetService(4,200,100,timeslices=2,test_mode=True)
    eq_(budget_service._get_timeslice_slots(),1)
    eq_(budget_service.process(),True)
    eq_(budget_service.process(),False)
    
    budget_service._set_next_timeslice()
    eq_(budget_service._get_timeslice_slots(),1)
    eq_(budget_service.process(),True)
 
def mptest_multiple_timeslice_rollover():
    budget_service = BudgetService(5,200,100,timeslices=2,test_mode=True)

    budget_service._set_next_timeslice()
    
    eq_(budget_service._get_timeslice_slots(),2)
    eq_(budget_service.process(),True)
    eq_(budget_service._get_timeslice_slots(),1)
    eq_(budget_service.process(),True)
    eq_(budget_service.process(),False)