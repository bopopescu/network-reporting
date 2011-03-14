from nose.tools import eq_
from nose.tools import with_setup
from server.ad_server.budget.budget_service import BudgetService

def mptest_budget_all_at_once():
    budget_service = BudgetService(1,500,timeslices=1,test_mode=True)
    eq_(budget_service.process(300),True)
    eq_(budget_service.process(300),False)

def mptest_budget_evenly_success():
    budget_service = BudgetService(1,500,timeslices=2,test_mode=True)
    eq_(budget_service.process(125),True)
    eq_(budget_service.process(125),True)
    eq_(budget_service._get_timeslice_budget(),0)
    eq_(budget_service.process(125),False)

  
def mptest_budget_evenly_failure():
    budget_service = BudgetService(1,500,timeslices=2,test_mode=True)
    eq_(budget_service.process(300),False)
    eq_(budget_service._get_timeslice_budget(),-50)
    eq_(budget_service.process(300),False)

def mptest_multiple_timeslices():
    budget_service = BudgetService(1,200,timeslices=2,test_mode=True)
    eq_(budget_service._get_timeslice_budget(),100)
    eq_(budget_service.process(100),True)
    
    budget_service._set_next_timeslice()
    eq_(budget_service._get_timeslice_budget(),100)
    eq_(budget_service.process(100),True)
 
def mptest_multiple_timeslice_rollover():
    budget_service = BudgetService(1,200,timeslices=2,test_mode=True)

    budget_service._set_next_timeslice()
    
    eq_(budget_service._get_timeslice_budget(),200)
    eq_(budget_service.process(100),True)
    eq_(budget_service._get_timeslice_budget(),100)
    eq_(budget_service.process(100),True)