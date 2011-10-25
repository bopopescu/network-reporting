import logging

from budget.models import BudgetChangeLog, Budget, BudgetSliceLog
from common.utils.query_managers import QueryManager

from budget.helpers import (build_budget_update_string,
                            parse_budget_update_string,
                            get_datetime_from_slice,
                            get_slice_from_datetime,
                            )

ZERO_BUDGET = 0.0

class BudgetQueryManager(QueryManager):

    Model = Budget

    @classmethod
    def prep_update_budget(self, budget, 
                           start_datetime = None,
                           end_datetime = False,
                           active = None,
                           delivery_type = None,
                           static_total_budget = None,
                           static_slice_budget = None,
                           ):
        """ Flags the budget to be updated, sets it's update
        string appropriately """
        if end_datetime is False:
            end_datetime = budget.end_datetime
        if start_datetime is None:
            start_datetime = budget.start_datetime
        if active is None:
            active = budget.active
        if delivery_type is None:
            delivery_type = budget.delivery_type

        # if either of these are set, then override the previous, otherwise use prev
        if static_total_budget is None and static_slice_budget is None:
            static_total_budget = budget.static_total_budget
            static_slice_budget = budget.static_slice_budget

        update_str = build_budget_update_string(start_datetime, end_datetime, active, delivery_type, static_total_budget, static_slice_budget)
        budget.update = True
        budget.update_str = update_str
        budget.put()
        return

    @classmethod
    def exec_update_budget(self, budget):
        """ Takes the update string, applies all the updates, logs the change """

        new_start, new_end, new_active, new_delivery, new_static_total, new_static_slice = parse_budget_update_string(budget.update_str)

        change_log = BudgetChangeLog(start_datetime      = budget.start_datetime,
                                     end_datetime        = budget.end_datetime,
                                     static_total_budget = budget.static_total_budget,
                                     static_slice_budget = budget.static_slice_budget,
                                     delviery_type      = budget.delivery_type,
                                     budget             = budget,
                                     )
        change_log.put()


        budget.start_datetime = new_start
        budget.end_datetime = new_end
        budget.delivery_type = new_delivery
        budget.static_total_budget = new_static_total
        budget.static_slice_budget = new_static_slice

        budget.update_str = None
        budget.update = False
        budget.put()
        pass
