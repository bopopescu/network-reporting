import logging

from budget.models import BudgetChangeLog, Budget, BudgetSliceLog
from budget.tzinfo import Pacific, utc
from common.utils.query_managers import QueryManager

from budget.helpers import (build_budget_update_string,
                            parse_budget_update_string,
                            get_datetime_from_slice,
                            get_slice_from_datetime,
                            get_slice_budget_from_daily,
                            )

ZERO_BUDGET = 0.0

class BudgetQueryManager(QueryManager):

    Model = Budget
    @classmethod
    def update_or_create_budget_for_campaign(cls, camp):
        logging.warning("\n\nCAMPAIGN IS: %s\n\n" % camp)
        # Update budget
        if camp.budget_obj:
            budget = camp.budget_obj
            if camp.active != budget.active:
                budget.active = camp.active
                budget.put()

            update_dict = {}
            # Camp datetimes will either be PST/PDT and aware of it, or UTC and unaware of it
            # budget datetimes will always be UTC and unaware
            
            # if Campaigns are aware of their tz, set them to UTC and make them unaware of it
            # doesn't matter if we put budgets at this point because when it gets put it'll fix itself
            if str(camp.start_datetime.tzinfo) == str(Pacific):
                camp.start_datetime = camp.start_datetime.astimezone(utc).replace(tzinfo = None)
            if camp.end_datetime and str(camp.end_datetime.tzinfo) == str(Pacific):
                camp.end_datetime = camp.end_datetime.astimezone(utc).replace(tzinfo = None)

            if not camp.start_datetime == camp.budget_obj.start_datetime:
                update_dict['start_datetime'] = camp.start_datetime
            if not camp.end_datetime == camp.budget_obj.end_datetime:
                update_dict['end_datetime'] = camp.end_datetime

            if not camp.budget_strategy == camp.budget_obj.delivery_type:
                update_dict['delivery_type'] = camp.budget_strategy

            if camp.budget:
                slice_budget = get_slice_budget_from_daily(camp.budget)
                # Only update the update dict if new values
                if not slice_budget == camp.budget_obj.static_slice_budget:
                    update_dict['static_total_budget'] = None
                    update_dict['static_slice_budget'] = slice_budget
            elif camp.full_budget:
                if not camp.full_budget == camp.budget_obj.static_total_budget:
                    update_dict['static_total_budget'] = camp.full_budget
                    update_dict['static_slice_budget'] = None
            else:
                return None
                # This is more appropriate
                raise WTFError

            if update_dict:
                cls.prep_update_budget(camp.budget_obj, **update_dict)
            return camp.budget_obj
        # Create budget
        elif camp.budget:
            budget = Budget(start_datetime = camp.start_datetime,
                            end_datetime = camp.end_datetime,
                            active = camp.active,
                            delivery_type = camp.budget_strategy,
                            static_slice_budget = get_slice_budget_from_daily(camp.budget),
                            )
            budget.put()
            return budget
        elif camp.full_budget:
            budget = Budget(start_datetime = camp.start_datetime,
                            end_datetime = camp.end_datetime,
                            active = camp.active,
                            delivery_type = camp.budget_strategy,
                            static_total_budget =camp.full_budget,
                            )
            budget.put()
            return budget
        # No budget
        else:
            return None


    @classmethod
    def prep_update_budget(cls, budget, 
                           start_datetime = None,
                           end_datetime = False,
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
        if delivery_type is None:
            delivery_type = budget.delivery_type

        # if either of these are set, then override the previous, otherwise use prev
        if static_total_budget is None and static_slice_budget is None:
            static_total_budget = budget.static_total_budget
            static_slice_budget = budget.static_slice_budget

        update_str = build_budget_update_string(start_datetime, end_datetime, delivery_type, static_total_budget, static_slice_budget)
        budget.update = True
        budget.update_str = update_str
        budget.put()
        return

    @classmethod
    def exec_update_budget(self, budget):
        """ Takes the update string, applies all the updates, logs the change """

        new_start, new_end, new_delivery, new_static_total, new_static_slice = parse_budget_update_string(budget.update_str)

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
