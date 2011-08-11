from budget.models import BudgetSliceLog
from common.utils.query_managers import QueryManager
from budget.models import BudgetSlicer

class BudgetSliceLogQueryManager(QueryManager):
    Model = BudgetSliceLog
    
    def get_most_recent(self, campaign):
        """ Returns the most recent *completed* SliceLog for a campaign. 
            Returns none if no timeslices have been completed. """
        budget_obj = BudgetSlicer.get_or_insert_for_campaign(campaign)
        
        recent_timeslices = budget_obj.timeslice_logs.order('-end_date').fetch(2)
        
        try:
            return recent_timeslices[1]
        except IndexError:     
            return None