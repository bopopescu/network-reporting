from budget.models import BudgetSliceLog
from common.utils.query_managers import QueryManager
from budget.models import Budget

class BudgetSliceLogQueryManager(QueryManager):
    Model = BudgetSliceLog
    
    def get_most_recent(self, campaign):
        """ Returns the most recent SliceLog for a campaign. """
        budget_slicer = Budget.get_or_insert_for_campaign(campaign)
        
        return budget_slicer.timeslice_logs.order('-end_date').get()