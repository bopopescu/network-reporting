import logging

from datetime import datetime, timedelta

from budget.models import BudgetChangeLog, Budget, BudgetSliceLog, BudgetSlicer
from budget.tzinfo import Pacific, utc
from common.utils.query_managers import QueryManager

from budget.helpers import (build_budget_update_string,
                            parse_budget_update_string,
                            get_datetime_from_slice,
                            get_slice_from_datetime,
                            get_slice_budget_from_daily,
                            )

ZERO_BUDGET = 0.0
ONE_DAY = timedelta(days=1)

class BudgetQueryManager(QueryManager):

    Model = Budget
    @classmethod
    def update_or_create_budget_for_campaign(cls, camp, total_spent=0.0):
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
            if camp.start_datetime is None:
                camp.start_datetime = datetime.now().replace(tzinfo=utc)
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

            if update_dict:
                cls.prep_update_budget(camp.budget_obj, **update_dict)
            return camp.budget_obj
        # Create budget
        elif camp.full_budget:
            budget = Budget(start_datetime = camp.start_datetime,
                            end_datetime = camp.end_datetime,
                            active = camp.active,
                            delivery_type = camp.budget_strategy,
                            static_total_budget = camp.full_budget,
                            total_spent = total_spent,
                            )
            budget.put()
            return budget

        elif camp.budget:
            budget = Budget(start_datetime = camp.start_datetime,
                            end_datetime = camp.end_datetime,
                            active = camp.active,
                            delivery_type = camp.budget_strategy,
                            static_slice_budget = get_slice_budget_from_daily(camp.budget),
                            total_spent = total_spent,
                            )
            budget.put()
            return budget
        # No budget
        else:
            return None

    @classmethod
    def migrate_campaign(cls, campaign):
        if campaign.budget_obj:
            return
        campaign, budget = cls.test_migrate(campaign)
        campaign.budget_obj = budget
        campaign.put()

    @classmethod
    def test_migrate(cls, campaign):
        now = datetime.now().date()
        start = campaign.start_date
        end = campaign.end_date
        slicer = BudgetSlicer.get_by_campaign(campaign)
        if slicer is not None:
            spent_today = slicer.spent_today
            spent_in_camp = slicer.spent_in_campaign
        else:
            spent_today = 0.0
            spent_in_camp = 0.0
        total_spent = spent_today + spent_in_camp
        if start is None:
            if campaign.budget is not None or campaign.full_budget is not None:
                start = now
        if start:
            # make it the start of the day if it's a start date
            campaign.start_datetime = datetime(start.year, start.month, start.day, 0, tzinfo = Pacific)
        if end:
            # make it the end of the day if it's an end date
            campaign.end_datetime = datetime(end.year, end.month, end.day, 23, 59, 0, tzinfo = Pacific)
        if not total_spent:
            total_spent = 0
        budget = cls.update_or_create_budget_for_campaign(campaign, total_spent = total_spent)
        if budget is not None:
            budget.put()
            if spent_today:
                todays_log = BudgetSliceLog(budget = budget,
                                            slice_num = get_slice_from_datetime(now),
                                            desired_spending = spent_today,
                                            actual_spending = spent_today,
                                            prev_total_spending = spent_in_camp,
                                            prev_braking_fraction = 1.0,
                                            )
                todays_log.put()
            if spent_in_camp:
                all_prev_logs = BudgetSliceLog(budget = budget,
                                               slice_num = get_slice_from_datetime(now - ONE_DAY),
                                               desired_spending = spent_in_camp,
                                               actual_spending = spent_in_camp,
                                               prev_total_spending = 0.0,
                                               prev_braking_fraction = 1.0,
                                               )
                all_prev_logs.put()
        return campaign, budget

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
    def exec_update_budget(cls, budget):
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
